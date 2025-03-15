import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Initialize the Cognito client
cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Common headers for CORS
common_headers = {
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST"
}

def lambda_handler(event, context):
    # Generate a unique requestId for tracing
    request_id = context.aws_request_id

    # Log the environment variables for debugging
    logger.info(f"USER_POOL_ID: {os.environ.get('USER_POOL_ID')}")
    logger.info(f"REGION: {os.environ.get('REGION')}")
    
    # Parse the request body
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    else:
        body = event.get('body', {})

    # Extract email from the request body
    email = body.get('email')

    # Validate email
    if not email:
        logger.error(f"[{request_id}] Email is required.")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'failed',
                'message': 'Email is required.',
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }

    # Get Cognito configuration from environment variables
    user_pool_id = os.environ['USER_POOL_ID']
    client_id = os.environ['USER_POOL_CLIENT_ID']

    try:
        # First, check if the user exists and get their status
        try:
            user_status = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            # Check if user is already confirmed
            if user_status.get('UserStatus') == 'CONFIRMED':
                logger.info(f"[{request_id}] User {email} is already confirmed.")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'status': 'failed',
                        'message': 'User is already confirmed.',
                        'requestId': request_id
                    }),
                    'headers': common_headers  # Add CORS headers here
                }
        except cognito_client.exceptions.UserNotFoundException:
            logger.warning(f"[{request_id}] User {email} not found.")
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'status': 'failed',
                    'message': 'User not found.',
                    'requestId': request_id
                }),
                'headers': common_headers  # Add CORS headers here
            }

        # Resend confirmation code
        response = cognito_client.resend_confirmation_code(
            ClientId=client_id,
            Username=email
        )

        # Change the status of the user to CONFIRMED if OTP is successfully sent
        cognito_client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[{
                'Name': 'email_verified',
                'Value': 'true'
            }]
        )

        logger.info(f"[{request_id}] Confirmation code resent successfully to {email}.")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Confirmation code has been resent successfully.',
                'delivery': {
                    'destination': response.get('CodeDeliveryDetails', {}).get('Destination'),
                    'medium': response.get('CodeDeliveryDetails', {}).get('DeliveryMedium')
                },
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }

    except cognito_client.exceptions.LimitExceededException:
        logger.error(f"[{request_id}] Too many attempts. Please try again later.")
        return {
            'statusCode': 429,  # Too Many Requests
            'body': json.dumps({
                'status': 'failed',
                'message': 'Too many attempts. Please try again later.',
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }

    except cognito_client.exceptions.InvalidParameterException as e:
        logger.error(f"[{request_id}] Invalid parameter: {str(e)}")
        return {
            'statusCode': 422,  # Unprocessable Entity
            'body': json.dumps({
                'status': 'failed',
                'message': str(e),
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }

    except cognito_client.exceptions.NotAuthorizedException:
        logger.error(f"[{request_id}] Not authorized to perform this operation.")
        return {
            'statusCode': 403,  # Forbidden
            'body': json.dumps({
                'status': 'failed',
                'message': 'Not authorized to perform this operation.',
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"[{request_id}] AWS ClientError: {error_message}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'failed',
                'message': f'An unexpected error occurred: {error_message}',
                'code': error_code,
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }

    except Exception as e:
        logger.error(f"[{request_id}] Internal server error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'failed',
                'message': f'Internal server error: {str(e)}',
                'requestId': request_id
            }),
            'headers': common_headers  # Add CORS headers here
        }
