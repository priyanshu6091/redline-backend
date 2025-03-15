import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }
    cognito = boto3.client('cognito-idp')
    
    try:
        body = json.loads(event['body'])
        refresh_token = body['refresh_token']
        
        logger.info("Attempting to refresh tokens")
        client_id = os.environ['USER_POOL_CLIENT_ID']
        
        response = cognito.initiate_auth(
            ClientId=client_id,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            }
        )
        
        logger.info("Token refresh successful")
        
        # Note: Refresh token auth flow only returns new access and ID tokens
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Token refresh successful',
                'status': 'success',
                'id_token': response['AuthenticationResult']['IdToken'],
                'access_token': response['AuthenticationResult']['AccessToken']
            }),
            'headers': common_headers
        }
        
    except cognito.exceptions.NotAuthorizedException:
        logger.warning("Invalid or expired refresh token")
        return {
            'statusCode': 401,
            'body': json.dumps({
                'message': 'Invalid or expired refresh token',
                'status': 'failed'
            }),
            'headers': common_headers
        }
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An unexpected error occurred: {str(e)}',
                'status': 'failed'
            }),
            'headers': common_headers
        }