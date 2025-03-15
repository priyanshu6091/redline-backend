import json
import pymongo
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any, List

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection


def get_mongodb_connection():
    db = create_docdb_connection()
    return db


def validate_shift_images(event_body: Dict[str, Any]) -> bool:
    required_fields = ["shiftId", "images"]
    if not all(field in event_body for field in required_fields):
        return False
    if not isinstance(event_body["images"], list):
        return False
    for image in event_body["images"]:
        if not isinstance(image, dict) or "imageUrl" not in image or "timeOfTaken" not in image:
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

        if not validate_shift_images(body):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields or invalid data format'}),
                'headers': common_headers
            }

        db = get_mongodb_connection()
        collection = db.shifts
        shift_id = body['shiftId']
        images = body['images']

        shift_document = collection.find_one({"_id": ObjectId(shift_id)})
        if not shift_document:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Shift not found'}),
                'headers': common_headers
            }

        # Create a new list with imageUrl and timeOfTaken fields
        image_data = [{"imageUrl": image["imageUrl"], "timeOfTaken": image["timeOfTaken"]} for image in images]

        # Append image data to the existing images array
        collection.update_one(
            {"_id": ObjectId(shift_id)},
            {"$push": {"images": {"$each": image_data}}, "$set": {"updatedAt": datetime.now()}}
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Images added successfully'}),
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
