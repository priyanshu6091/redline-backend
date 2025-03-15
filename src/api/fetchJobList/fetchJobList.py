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
    """Create MongoDB connection"""
    db = create_docdb_connection()
    return db

def lambda_handler(event, context):
    """Fetch the job list from the database"""
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,GET",
    }
    try:

        db = get_mongodb_connection()
        collection = db.job_details
        jobs = collection.find({}, {"_id": 1,  "propertyName": 1,"longitude": 1, "latitude": 1})
        
        # changing objectId into string
        job_list = []
        for job in jobs:
            job_list.append({
                "id": str(job["_id"]),
                "propertyName": job.get("propertyName", ""),
                "longitude": job.get("longitude", ""),
                "latitude": job.get("latitude", ""),
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Job list fetched successfully",
                "data": job_list
            }),
            "headers": common_headers
        }
    
    except pymongo.errors.ConnectionError:
        return {
            "statusCode": 503,
            "body": json.dumps({
                "error": "Database connection error"
            }),
            "headers": common_headers
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}"
            }),
            "headers": common_headers
        }
