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

def validate_job_lists(event_body: Dict[str, Any]) -> bool:
    required_fields = [
        "userID",
        "jobID",
        "startTime",
        "status"
    ]
    return all(field in event_body for field in required_fields)
def find_job_details(db, job_id):
    # Find the job document
    job_document = db.job_details.find_one({
        "_id": ObjectId(job_id),
    })
    
    if job_document:
        
        return job_document
    else:
        return None
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
        
        if not validate_job_lists(body):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields'
                }),
                'headers': common_headers
            }
        
        db = get_mongodb_connection()
        collection = db.shifts
        job_document = find_job_details(db,body['jobID'])
        manager_id = str(job_document['managerId'])

        shift_details = {
            'userID': body['userID'],
            'jobID': body['jobID'],
            'managerID':job_document['managerId'],
            'currentTime': datetime.now(),
            'endTime': body.get('endTime', None),
            'steps': body.get('steps', 0),
            'coordinates': [],
            'status': "Active",
            'createdAt': datetime.now(),
            'updatedAt': datetime.now(),
            "images":body['images']


        }
        
        result = collection.insert_one(shift_details)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Job details created successfully',
                'shiftId': str(result.inserted_id),
                'managerID': manager_id,

            }),
            'headers': common_headers
        }
    
    except pymongo.errors.ConnectionError:
        return {
            'statusCode': 503,
            'body': json.dumps({
                'error': 'Database connection error'
            }),
            'headers': common_headers
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            }),
            'headers': common_headers
        }
