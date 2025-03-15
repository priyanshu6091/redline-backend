import json
import pymongo
from bson import ObjectId
from typing import Dict, Any

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def get_mongodb_connection():
    db = create_docdb_connection()
    return db

def validate_shift_id(event_body: Dict[str, Any]) -> bool:
    return "shiftId" in event_body and isinstance(event_body["shiftId"], str)

def lambda_handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",  # Updated to POST
        "Access-Control-Allow-Credentials": True,
    }
    try:
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event['body']

        # Validate shiftId in the body
        if not validate_shift_id(body):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing or invalid shiftId'}),
                'headers': common_headers
            }

        # Connect to MongoDB and query the shift
        db = get_mongodb_connection()
        collection = db.shifts
        shift_id = body['shiftId']  # Changed from shiftID to shiftId for consistency

        shift_document = collection.find_one({"_id": ObjectId(shift_id)})
        if not shift_document:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Shift not found'}),
                'headers': common_headers
            }

        images = shift_document.get("images", [])

        return {
            'statusCode': 200,
            'body': json.dumps({'images': images}),
            'headers': common_headers
        }

    except pymongo.errors.ConnectionError:
        return {
            'statusCode': 503,
            'body': json.dumps({'error': 'Database connection error'}),
            'headers': common_headers
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'}),
            'headers': common_headers
        }