import json
import pymongo
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def get_mongodb_connection():
    db = create_docdb_connection()
    return db


def validate_log_entry(event_body: Dict[str, Any]) -> bool:
    required_fields = ["shiftId", "log"]
    if not all(field in event_body for field in required_fields):
        return False
    if not isinstance(event_body["log"], dict):
        return False
    return True


def lambda_handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event['body']

        if not validate_log_entry(body):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields or invalid format'}),
                'headers': common_headers
            }

        db = get_mongodb_connection()
        collection = db.shifts
        shift_id = body['shiftId']
        log_entry = body['log']

        shift_document = collection.find_one({"_id": ObjectId(shift_id)})
        if not shift_document:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Shift not found'}),
                'headers': common_headers
            }

        # Append the log entry to the logs array
        collection.update_one(
            {"_id": ObjectId(shift_id)},
            {"$push": {"logs": log_entry}, "$set": {"updatedAt": datetime.now()}}
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': "success"}),
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
