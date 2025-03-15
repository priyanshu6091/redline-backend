import os
import json
import logging
import requests
from typing import Dict, Any
import traceback
import boto3
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Common headers for CORS
common_headers = {
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
}

# Status codes
class StatusCodes:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    CONFLICT_ERROR = "CONFLICT_ERROR"

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def validate_request_body(body: Dict[str, Any]) -> tuple[bool, list]:
    """
    Validate the request body contains all required fields
    Returns: (is_valid: bool, missing_fields: list)
    """
    required_fields = ['email', 'password', 'role', 'location']
    missing_fields = [field for field in required_fields if not body.get(field)]
    return len(missing_fields) == 0, missing_fields

def store_user_data(db, user_data: Dict[str, Any]) -> str:
    """Store user data in MongoDB"""
    try:
        users_collection = db.users
        result = users_collection.insert_one({
            'email': user_data['email'],
            'role': user_data['role'],
            'location': user_data['location'],
            'status': 'active',
            'createdAt': datetime.utcnow()
        })
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error storing user data in MongoDB: {str(e)}")
        raise Exception("Failed to store user data")

def check_existing_user(db, email: str) -> bool:
    """Check if user already exists in MongoDB"""
    try:
        users_collection = db.users
        existing_user = users_collection.find_one({'email': email})
        return existing_user is not None
    except Exception as e:
        logger.error(f"Error checking existing user: {str(e)}")
        raise Exception("Failed to check existing user")

def connect_to_docdb():
    """Establish a connection to DocumentDB"""
    try:
        # client = create_docdb_connection()
        db = create_docdb_connection()
        return db
    except Exception as e:
        logger.error(f"Error connecting to DocumentDB: {str(e)}")
        raise Exception("Failed to connect to DocumentDB")

def is_user_authorized_in_homebase(homebase_url: str, email: str) -> bool:
    """Check if the user exists and is authorized in Homebase"""
    try:
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {os.environ["HOMEBASE_API_KEY"]}'
        }
        params = {
            'page': 1,
            'per_page': 999999,
            'with_archived': 'false'
        }
        
        logger.info(f"Checking Homebase authorization for email: {email}")
        response = requests.get(homebase_url, headers=headers, params=params, timeout=10)
        logger.info(f"Homebase API Response: {response.status_code}")
        
        if response.status_code == 200:
            employees = response.json()
            for employee in employees:
                if employee.get('email') == email:
                    logger.info(f"User {email} found in Homebase")
                    return True
            logger.info(f"User {email} not found in Homebase")
            return False
        else:
            logger.error(f"Homebase API error: {response.status_code} - {response.text}")
            raise Exception(f"Homebase API returned status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error checking Homebase authorization: {str(e)}")
        raise Exception("Failed to verify Homebase authorization")

def create_cognito_user(cognito, client_id: str, user_pool_id: str, email: str, password: str):
    """Create user in Cognito, email verification required"""
    try:
        cognito.sign_up(
            ClientId=client_id,
            Username=email,
            Password=password,
            UserAttributes=[{'Name': 'email', 'Value': email}]
        )
        
        logger.info(f"Successfully created Cognito user: {email}. Awaiting email verification.")
    except cognito.exceptions.UsernameExistsException:
        raise Exception("Email already registered in Cognito")
    except Exception as e:
        logger.error(f"Cognito error: {str(e)}")
        raise Exception(f"Failed to create user in Cognito: {str(e)}")

def create_response(status_code: int, status: str, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized response with status and message
    
    :param status_code: HTTP status code
    :param status: Status from StatusCodes class
    :param message: Descriptive message about the result
    :param data: Optional additional data to include in the response
    :return: Standardized response dictionary
    """
    response_body = {
        'status': status,
        'message': message
    }
    
    # Add data if provided
    if data:
        response_body['data'] = data
    
    return {
        'statusCode': status_code,
        'body': json.dumps(response_body),
        'headers': common_headers
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main handler function for the Lambda"""
    try:
        logger.info("Processing sign-up request")
        
        # Parse request body
        try:
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            elif isinstance(event.get('body'), dict):
                body = event['body']
            else:
                return create_response(
                    400, 
                    StatusCodes.VALIDATION_ERROR, 
                    'Invalid request format'
                )
        except json.JSONDecodeError:
            return create_response(
                400, 
                StatusCodes.VALIDATION_ERROR, 
                'Invalid JSON in request body'
            )

        # Validate request body
        is_valid, missing_fields = validate_request_body(body)
        if not is_valid:
            return create_response(
                400, 
                StatusCodes.VALIDATION_ERROR, 
                'Missing required fields',
                {'missing_fields': missing_fields}
            )

        # Extract fields
        email = body['email']
        password = body['password']
        role = body['role']
        location = body['location']

        # Initialize AWS clients
        try:
            cognito = boto3.client('cognito-idp', region_name=os.environ['REGION'])
            client_id = os.environ['USER_POOL_CLIENT_ID']
            user_pool_id = os.environ['USER_POOL_ID']
        except Exception as e:
            logger.error(f"Failed to initialize AWS services: {str(e)}")
            return create_response(
                500, 
                StatusCodes.FAILURE, 
                'AWS service initialization failed'
            )

        # Check Homebase authorization
        homebase_url = "https://app.joinhomebase.com/api/public/locations/66c527ed-cb65-49a5-9ddb-ba615526b437/employees"
        if not is_user_authorized_in_homebase(homebase_url, email):
            return create_response(
                403, 
                StatusCodes.AUTHORIZATION_ERROR, 
                'User not authorized in Homebase'
            )

        # Connect to DocumentDB and check for existing user
        db = connect_to_docdb()
        if check_existing_user(db, email):
            return create_response(
                400, 
                StatusCodes.CONFLICT_ERROR, 
                'User already exists'
            )

        # Create user in Cognito
        create_cognito_user(cognito, client_id, user_pool_id, email, password)

        # Store user data in DocumentDB
        user_data = {
            'email': email,
            'role': role,
            'location': location
        }
        store_user_data(db, user_data)
        
        logger.info(f"Successfully completed sign-up for user: {email}")
        
        return create_response(
            200, 
            StatusCodes.SUCCESS, 
            'User signed up successfully',
            {
                'email': email,
                'role': role
            }
        )

    except Exception as e:
        logger.error(f"Error in sign-up process: {str(e)}\n{traceback.format_exc()}")
        return create_response(
            500, 
            StatusCodes.FAILURE, 
            'Internal server error',
            {'error_details': str(e)}
        )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point"""
    return handler(event, context)
