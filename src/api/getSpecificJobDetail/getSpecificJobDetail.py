import json
import logging
from bson import ObjectId
from pymongo.errors import PyMongoError
from datetime import datetime

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Common headers
common_headers = {
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,GET",
    "Access-Control-Allow-Credentials": True,
}

def is_valid_object_id(id_str):
    """Check if the string is a valid MongoDB ObjectId."""
    try:
        ObjectId(id_str)
        return True
    except Exception:
        return False

def connect_to_docdb():
    """Establish a connection to DocumentDB."""
    try:
        db = create_docdb_connection()
        return db
    except Exception as e:
        logger.error(f"Error connecting to DocumentDB: {str(e)}")
        raise Exception("Failed to connect to DocumentDB")

def convert_objectids_and_dates(obj):
    """
    Recursively convert ObjectId instances to strings and datetime objects to ISO8601 strings
    in a dictionary or list.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, datetime):
                obj[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                convert_objectids_and_dates(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, ObjectId):
                obj[i] = str(item)
            elif isinstance(item, datetime):
                obj[i] = item.isoformat()
            elif isinstance(item, (dict, list)):
                convert_objectids_and_dates(item)
    return obj

def lambda_handler(event, context):
    """
    Lambda function to fetch data from the 'job_details' collection.
    If 'job_id' is provided, fetch data for that specific job_id.
    Otherwise, fetch all data from the collection.
    """
    try:
        # Parse the body for job_id
        body = json.loads(event.get("body", "{}"))
        job_id = body.get("job_id")

        # Connect to DocumentDB
        db = connect_to_docdb()
        job_details_collection = db["job_details"]  # Updated collection name

        # If job_id is provided, validate and fetch data for the specific job_id
        if job_id:
            if not is_valid_object_id(job_id):
                return {
                    "statusCode": 400,
                    "headers": common_headers,
                    "body": json.dumps({"error": "Invalid ObjectId format"}),
                }

            # Convert string ID to ObjectId
            object_id = ObjectId(job_id)

            # Fetch the job details for the specific job_id
            job_details = job_details_collection.find_one({"_id": object_id})  # Use "_id" for primary key lookup

            if not job_details:
                return {
                    "statusCode": 404,
                    "headers": common_headers,
                    "body": json.dumps({"error": f"No job details found for job_id: {job_id}"}),
                }

            # Convert all ObjectId and datetime instances to strings
            job_details = convert_objectids_and_dates(job_details)

            # Successful response
            return {
                "statusCode": 200,
                "headers": common_headers,
                "body": json.dumps({"message": "success", "data": job_details}),
            }

        # If no job_id is provided, fetch all data
        all_job_details = list(job_details_collection.find())

        # Convert all ObjectId and datetime instances to strings
        all_job_details = convert_objectids_and_dates(all_job_details)

        # Successful response
        return {
            "statusCode": 200,
            "headers": common_headers,
            "body": json.dumps({"message": "All job details fetched successfully.", "data": all_job_details}),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": common_headers,
            "body": json.dumps({"error": "Invalid JSON format in the request body."}),
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": common_headers,
            "body": json.dumps({"error": "Internal server error", "details": str(e)}),
        }
