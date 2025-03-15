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
    db = create_docdb_connection()  # Use the custom connection function
    return db

def validate_job_details(event_body: Dict[str, Any]) -> bool:
    """Validate required fields in job details"""
    required_fields = [
        "propertyName",
        "propertyAddress",
        "propertyManagerName",
        "propertyManagerPhone",
        "gateAccess",
        "gateAccessrestroom",
        "longitude",
        "latitude",
        "buildingNo",
        "propertyclientName",
        "propertyclientPhonenumber"
    ]
    return all(field in event_body for field in required_fields)

def lambda_handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }
    try:
        # Parse the incoming event body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event['body']
        
        # Validate input
        if not validate_job_details(body):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields'
                }),
                'headers': common_headers
            }
        
        # Connect to MongoDB using custom connection function
        db = get_mongodb_connection()
        collection = db.job_details
        
        # Prepare document for insertion
        job_document = {
            'propertyName': body['propertyName'],
            'propertyAddress': body['propertyAddress'],
            'propertyManagerName': body['propertyManagerName'],
            'propertyManagerPhone': body['propertyManagerPhone'],
            'buildingNo': body['buildingNo'],
            'gateAccess': body.get('gateAccess'),
            'gateAccessrestroom': body.get('gateAccessrestroom'),
            'longitude': body['longitude'],
            'managerId': ObjectId(body['managerId']),
            'latitude': body['latitude'],
            'propertyclientName':body.get('propertyclientName'),
            'propertyclientPhonenumber':body.get('propertyclientPhonenumber'),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'status': 'active'
        }
        
        # Insert document
        result = collection.insert_one(job_document)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Job details created successfully',
                'jobId': str(result.inserted_id)
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
