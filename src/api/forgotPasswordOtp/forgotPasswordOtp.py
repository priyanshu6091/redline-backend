import json
import boto3
import os

def lambda_handler(event, context):
    cognito = boto3.client('cognito-idp')
    

    body = json.loads(event['body'])
    Username = body['email']
    
    
    client_id = os.environ['USER_POOL_CLIENT_ID'] 
    
    try:

        cognito.forgot_password(
            ClientId=client_id,
            Username=Username
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success', 
                'message': 'OTP sent successfully to the user.',
                'Username': Username
            })
        }

        
    except cognito.exceptions.UserNotFoundException:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'failed', 
                'error': 'User not found.'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'failed', 
                'error': str(e)
            })
        }
