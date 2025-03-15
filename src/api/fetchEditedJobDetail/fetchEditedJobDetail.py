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
        if '_id' in obj:
            obj['id'] = str(obj.pop('_id'))
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
    Lambda function to fetch data from the 'edit_job_details' collection.
    If 'managerId' is provided, fetch data for that specific managerId and with status "active".
    Otherwise, fetch all data from the collection.
    """
    try:
        # Parse the body for managerId
        body = json.loads(event.get("body", "{}"))
        manager_id = body.get("managerId")

        # Connect to DocumentDB
        db = connect_to_docdb()
        edit_job_details_collection = db["edit_job_details"]

        # If managerId is provided, validate and fetch data for the specific managerId
        if manager_id:
            if not is_valid_object_id(manager_id):
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Credentials": True,
                    },
                    "body": json.dumps({"error": "Invalid ObjectId format for managerId"}),
                }

            # Convert string ID to ObjectId
            object_id = ObjectId(manager_id)

            # Fetch the edited job details for the specific managerId with status 'active'
            edited_job_details = list(edit_job_details_collection.find({
                "managerId": object_id,
                "status": "active"
            }))

            if not edited_job_details:
                return {
                    "statusCode": 404,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Credentials": True,
                    },
                    "body": json.dumps({"error": f"No active edited job details found for managerId: {manager_id}"}),
                }

            # Convert all ObjectId and datetime instances to strings
            edited_job_details = convert_objectids_and_dates(edited_job_details)

            # Successful response
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"message": "Edited job details fetched successfully.", "data": edited_job_details}),
            }

        # If no managerId is provided, fetch all job details
        all_job_details = list(edit_job_details_collection.find({"status": "active"}))

        if not all_job_details:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": "No active edited job details found."}),
            }

        # Convert all ObjectId and datetime instances to strings
        all_job_details = convert_objectids_and_dates(all_job_details)

        # Successful response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"message": "All active edited job details fetched successfully.", "data": all_job_details}),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"error": "Invalid JSON format in the request body."}),
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"error": "Internal server error", "details": str(e)}),
        }
