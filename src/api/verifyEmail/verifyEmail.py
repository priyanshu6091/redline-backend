import json
import boto3
import os
from botocore.exceptions import ClientError

# Initialize the Cognito client
cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])

def handler(event, context):
    # Check if 'body' is a string (i.e., JSON encoded) or a dictionary (already parsed)
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    else:
        body = event.get('body', {})

    # Extract the email and confirmation code from the request body
    email = body.get('email')
    confirmation_code = body.get('confirmationCode')

    # Validation for email and confirmation code
    if not email or not confirmation_code:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'failed',
                'message': 'Email and confirmation code are required.'
            })
        }

    # Trim any extra spaces from the confirmation code
    confirmation_code = confirmation_code.strip()

    # Validate confirmation code format
    if not confirmation_code or ' ' in confirmation_code:
        return {
            'statusCode': 422,  # Unprocessable Entity
            'body': json.dumps({
                'status': 'failed',
                'message': 'Confirmation code must not contain spaces and cannot be empty.'
            })
        }

    # User Pool and Client configuration
    user_pool_id = os.environ['USER_POOL_ID']
    client_id = os.environ['USER_POOL_CLIENT_ID']

    try:
        # Step 1: Confirm the user's sign-up with Cognito
        cognito_client.confirm_sign_up(
            ClientId=client_id,
            Username=email,  # Use 'Username' instead of 'email'
            ConfirmationCode=confirmation_code
        )

        # Step 2: Manually mark the email as verified
        cognito_client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
            ]
        )

        # Return a success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'User confirmed and email verified successfully.'
            })
        }

    except cognito_client.exceptions.CodeMismatchException:
        # If the code is incorrect, return a failure response
        return {
            'statusCode': 401,  # Unauthorized
            'body': json.dumps({
                'status': 'failed',
                'message': 'Invalid confirmation code.'
            })
        }

    except cognito_client.exceptions.ExpiredCodeException:
        # If the confirmation code is expired
        return {
            'statusCode': 410,  # Gone
            'body': json.dumps({
                'status': 'failed',
                'message': 'Confirmation code has expired.'
            })
        }

    except cognito_client.exceptions.UserNotFoundException:
        # If the user does not exist
        return {
            'statusCode': 404,  # Not Found
            'body': json.dumps({
                'status': 'failed',
                'message': 'User not found.'
            })
        }

    except cognito_client.exceptions.InvalidParameterException as e:
        # Handle invalid parameters (e.g., invalid email format)
        return {
            'statusCode': 422,  # Unprocessable Entity
            'body': json.dumps({
                'status': 'failed',
                'message': str(e)
            })
        }

    except ClientError as e:
        # Catch any other client errors
        error_code = e.response['Error']['Code']
        return {
            'statusCode': 500,  # Internal Server Error
            'body': json.dumps({
                'status': 'failed',
                'message': f'An unexpected error occurred: {error_code}'
            })
        }
