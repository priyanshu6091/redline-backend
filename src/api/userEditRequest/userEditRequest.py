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
    """Check if the string is a valid MongoDB ObjectId"""
    try:
        ObjectId(id_str)
        return True
    except:
        return False

def connect_to_docdb():
    """Establish a connection to DocumentDB"""
    try:
        db = create_docdb_connection()
        return db
    except Exception as e:
        logger.error(f"Error connecting to DocumentDB: {str(e)}")
        raise Exception("Failed to connect to DocumentDB")

def lambda_handler(event, context):
    """
    Lambda function to take the most recent edit from `edit_job_details` and update `job_details`.
    """
    try:
        # Parse the body of the request for the job ID
        body = json.loads(event.get("body", "{}"))

        # Extract job ID from the request body
        job_id = body.get("job_id")

        if not job_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True
                },
                "body": json.dumps({"error": "Missing 'job_id' in the request body."}),
            }

        # Validate and convert job_id to ObjectId
        if not is_valid_object_id(job_id):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True
                },
                "body": json.dumps({"error": "Invalid ObjectId format."}),
            }

        # Convert string ID to ObjectId
        object_id = ObjectId(job_id)

        # Connect to DocumentDB
        db = connect_to_docdb()
        job_details_collection = db["job_details"]
        edit_job_details_collection = db["edit_job_details"]

        # Retrieve the most recent edit for the given job ID
        recent_edit = edit_job_details_collection.find_one(
            {"job_id": object_id},
            sort=[("updatedAt", -1)]  # Sort by updatedAt descending to get the latest edit
        )

        if not recent_edit:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True
                },
                "body": json.dumps({"error": f"No recent edits found for job ID: {job_id}"}),
            }

        # Remove non-updatable fields from the edit record
        update_fields = {
            key: value
            for key, value in recent_edit.items()
            if key not in ["_id", "job_id", "createdAt", "updatedAt"]
        }

        # Update `job_details` with the retrieved edit data and set updatedAt to now
        try:
            result = job_details_collection.update_one(
                {"_id": object_id},
                {"$set": {**update_fields, "updatedAt": datetime.now()}}
            )
            if result.matched_count == 0:
                return {
                    "statusCode": 404,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Credentials": True
                    },
                    "body": json.dumps({"error": f"No record found with _id: {job_id}"}),
                }
        except PyMongoError as e:
            logger.error(f"MongoDB error during update: {str(e)}")
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True
                },
                "body": json.dumps({"error": "Failed to update job details in MongoDB.", "details": str(e)}),
            }

        # Convert any `ObjectId` values in the updated fields to strings for JSON serialization
        updated_fields_serializable = {
            key: (str(value) if isinstance(value, ObjectId) else value)
            for key, value in update_fields.items()
        }

        # Successful response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True
            },
            "body": json.dumps({"message": "success", "updated_fields": updated_fields_serializable}),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True
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
                "Access-Control-Allow-Credentials": True
            },
            "body": json.dumps({"error": "Internal server error.", "details": str(e)}),
        }
