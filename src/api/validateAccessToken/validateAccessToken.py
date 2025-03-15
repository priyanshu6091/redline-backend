import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Check if the provided access token is valid."""
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }
    
    try:
        body = json.loads(event['body'])
        access_token = body.get('access_token')
        
        if not access_token:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Access token is required', 'status': 'failed'}),
                'headers': common_headers
            }
        
        cognito = boto3.client('cognito-idp')
        response = cognito.get_user(AccessToken=access_token)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Access token is valid', 'status': 'success', 'user': response}),
            'headers': common_headers
        }
    except cognito.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Invalid or expired access token', 'status': 'expired'}),
            'headers': common_headers
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An unexpected error occurred: {str(e)}', 'status': 'failed'}),
            'headers': common_headers
        }