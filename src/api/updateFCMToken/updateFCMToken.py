import json
import pymongo
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any

try:
    from helper.db.docdb import create_docdb_connection  # Adjust this import based on your project structure
except ImportError:
    from src.helper.db.docdb import create_docdb_connection  # Adjust for local testing or different project structure

def get_mongodb_connection():
    """Create MongoDB connection"""
    db = create_docdb_connection()  
    return db

def lambda_handler(event, context):
    """Lambda function handler"""
    
    print("Received event:", json.dumps(event, indent=2)) 

    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }

    try:
        body = json.loads(event['body'])
        email = body.get('email')
        fcmToken = body.get('fcmToken')

        if not email or not fcmToken:
            return {
                'statusCode': 400,
                'headers': common_headers,
                'body': json.dumps({'message': 'Email and FCM token are required'})
            }

        db = get_mongodb_connection()
        users_collection = db['users']  # Replace with the correct collection name

        # Update the user document with the new FCM token
        result = users_collection.update_one(
            {'email': email},
            {'$set': {'fcmToken': fcmToken}}
        )

        if result.modified_count == 0:
            return {
                'statusCode': 404,
                'headers': common_headers,
                'body': json.dumps({'message': 'User not found'})
            }

        # Return success message if the FCM token was updated
        return {
            'statusCode': 200,
            'headers': common_headers,
            'body': json.dumps({'message': 'FCM token updated successfully'})
        }

    except pymongo.errors.PyMongoError as db_error:
        print(f'MongoDB Error: {str(db_error)}')
        return {
            'statusCode': 500,
            'headers': common_headers,
            'body': json.dumps({'message': 'Database error'})
        }

    except Exception as e:
        print(f'Error: {str(e)}')
        return {
            'statusCode': 500,
            'headers': common_headers,
            'body': json.dumps({'message': 'Internal server error'})
        }
