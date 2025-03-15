import json
import pymongo
from datetime import datetime, timezone
from typing import Dict, Any
from bson import ObjectId
import traceback
try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def get_mongodb_connection():
    db = create_docdb_connection()
    return db

# Convert datetime objects to ISO format
def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to string
    return obj

def check_active_shift(db, user_id: str):
    collection = db['shifts']
    
    # Get current date in UTC
    current_date = datetime.now(timezone.utc)
    
    # Create date boundaries for today
    start_of_day = datetime(
        current_date.year,
        current_date.month,
        current_date.day,
        tzinfo=timezone.utc
    )
    
    # Find shift for today (either Active or Inactive)
    shift = collection.find_one({
        'userID': user_id,
        'createdAt': {'$gte': start_of_day},
        'status': {'$in': ['Active']}  # Check for both statuses
    })
    
    if shift:
        # Get associated job details
        job_document = db.job_details.find_one({
            '_id': ObjectId(shift['jobID'])
        })
        
        # Determine isActive based on shift status (not stored in DB)
        is_active = shift['status'] == 'Active'
        
        return {
            'isActive': is_active,  # Derived from status, not stored
            'shiftData': {
                'shiftId': str(shift['_id']),
                'jobId': shift['jobID'],
                'startTime': shift['currentTime'].isoformat(),
                'coordinates': shift['coordinates'],
                'steps': shift['steps'],
                'status': shift['status'],  # Include actual stored status
                'propertyName': job_document.get('propertyName') if job_document else None,
                'latitude': job_document.get('latitude') if job_document else None,
                'longitude': job_document.get('longitude') if job_document else None
            }
        }
    
    return {
        'isActive': False,
        'shiftData': None
    }

def lambda_handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }
    
    try:
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Extract userId from the request body
        user_id = body.get('userId')
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'userId is required in request body'
                }),
                'headers': common_headers
            }
        
        db = get_mongodb_connection()
        shift_status = check_active_shift(db, user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(shift_status, default=convert_datetime, indent=4),
            'headers': common_headers
        }
        
    except Exception as e:
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            }),
            'headers': common_headers
        }