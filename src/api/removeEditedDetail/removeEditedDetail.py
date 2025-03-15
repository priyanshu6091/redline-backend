import json
import logging
from bson import ObjectId
from pymongo.errors import PyMongoError

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

def lambda_handler(event, context):
    """
    Lambda function to update the status of a job in the 'edit_job_details' collection.
    Takes 'job_id' as input from the event body and updates its status to 'disabled'.
    Note: This function ONLY updates the 'edit_job_details' collection, not 'job_details'.
    """
    try:
        # Parse the body for job_id
        body = json.loads(event.get("body", "{}"))
        job_id = body.get("job_id")

        # Validate the job_id format
        if not job_id or not is_valid_object_id(job_id):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": "Invalid ObjectId format for job_id."}),
            }

        # Connect to DocumentDB
        db = connect_to_docdb()
        edit_job_details_collection = db["edit_job_details"]

        # Convert string ID to ObjectId for query
        object_id = ObjectId(job_id)

        # Update the status field to "disabled"
        result = edit_job_details_collection.update_one(
            {"job_id": object_id},
            {"$set": {"status": "disabled"}}
        )

        if result.matched_count == 0:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": f"No job found with job_id: {job_id}"}),
            }

        # Successful update response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"message": f"Job with job_id: {job_id} updated to 'disabled' successfully."}),
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
