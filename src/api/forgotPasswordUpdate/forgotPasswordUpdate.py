import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    cognito = boto3.client('cognito-idp')
    CLIENT_ID = os.environ['USER_POOL_CLIENT_ID'] 
    
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        otp = body.get('otp')
        new_password = body.get('newPassword')
        
        cognito.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=otp,
            Password=new_password
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'status': 'success',
                'message': 'Password reset successful'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'status': 'failed', 
                'message': str(e),
                'error': 'Server Error'
            })
        }