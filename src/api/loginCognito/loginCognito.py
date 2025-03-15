import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def connect_to_docdb():
    """Establish a connection to DocumentDB"""
    try:
        return create_docdb_connection()
    except Exception as e:
        logger.error(f"Error connecting to DocumentDB: {str(e)}")
        raise Exception("Failed to connect to DocumentDB")

def check_existing_user(db, email: str) -> bool:
    """Check if user already exists in MongoDB"""
    try:
        return db.users.find_one({'email': email})
    except Exception as e:
        logger.error(f"Error checking existing user: {str(e)}")
        return False

def refresh_access_token(cognito, client_id, refresh_token):
    """Refresh the access token using the refresh token"""
    try:
        response = cognito.initiate_auth(
            ClientId=client_id,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={'REFRESH_TOKEN': refresh_token}
        )
        if 'AuthenticationResult' in response:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Token refreshed successfully',
                    'access_token': response['AuthenticationResult']['AccessToken'],
                    'id_token': response['AuthenticationResult']['IdToken'],
                    'refresh_token': response['AuthenticationResult']['RefreshToken']
                }),
                'headers': {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                }
            }
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Unable to refresh token', 'status': 'failed'}),
            'headers': {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error refreshing token: {str(e)}', 'status': 'failed'}),
            'headers': {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            }
        }

def handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }
    cognito = boto3.client('cognito-idp')
    
    try:
        body = json.loads(event['body'])
        email, password = body['email'], body['password']
        
        logger.info(f"Attempting login for email: {email}")
        user_pool_id, client_id = os.environ['USER_POOL_ID'], os.environ['USER_POOL_CLIENT_ID']
        
        try:
            response = cognito.list_users(UserPoolId=user_pool_id, Filter=f"email = \"{email}\"")
            if not response['Users']:
                logger.warning(f"User not found for email: {email}")
                return {
                    'statusCode': 404,
                    'body': json.dumps({'message': 'User not found', 'status': 'failed'}),
                    'headers': common_headers
                }
            username = response['Users'][0]['Username']
        except Exception as e:
            logger.error(f"Error fetching user by email: {str(e)}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Error fetching user details', 'status': 'failed'}),
                'headers': common_headers
            }
        
        user_info = cognito.admin_get_user(UserPoolId=user_pool_id, Username=username)
        email_verified = next((attr['Value'] for attr in user_info['UserAttributes'] if attr['Name'] == 'email_verified'), None)
        
        if email_verified == 'true':
            logger.info(f"User {email} is confirmed. Attempting authentication.")
            response = cognito.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={'USERNAME': username, 'PASSWORD': password}
            )
            logger.info(f"Authentication response: {json.dumps(response)}")
            
            db = connect_to_docdb()
            user_data = check_existing_user(db, email)
            if not user_data:
                return {
                    'statusCode': 403,
                    'body': json.dumps({'message': 'User is not registered', 'status': 'failed'}),
                    'headers': common_headers
                }
            
            if 'AuthenticationResult' in response:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'Login successful',
                        'status': 'success',
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'expiry_time': response['AuthenticationResult']['ExpiresIn'],
                        'role': user_data['role'],
                        'user_id': str(user_data['_id'])
                    }),
                    'headers': common_headers
                }
            logger.error(f"Unexpected response: {json.dumps(response)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Unexpected authentication response', 'status': 'failed'}),
                'headers': common_headers
            }
        
        logger.warning(f"User {email} is not confirmed.")
        return {
            'statusCode': 403,
            'body': json.dumps({'message': 'User is not confirmed. Please check your email and confirm your account.', 'status': 'failed'}),
            'headers': common_headers
        }
    except cognito.exceptions.UserNotConfirmedException:
        return {
            'statusCode': 403,
            'body': json.dumps({'message': 'User is not confirmed. Please check your email and confirm your account.', 'status': 'failed'}),
            'headers': common_headers
        }
    except cognito.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Incorrect email or password', 'status': 'failed'}),
            'headers': common_headers
        }
    except cognito.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'User not found', 'status': 'failed'}),
            'headers': common_headers
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An unexpected error occurred: {str(e)}', 'status': 'failed'}),
            'headers': common_headers
        }
