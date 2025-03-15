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
    except Exception:
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
    Lambda function to edit job details and store the edited details in the 'edit_job_details' collection.
    """
    try:
        # Parse the body of the request for fields to update
        body = json.loads(event.get("body", "{}"))
        # Extract 'id' from the request body (not from URL)
        job_id = body.get("id")
        # Ensure 'id' is provided in the body
        if not job_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": "Missing 'id' in the request body."}),
            }
        # Extract fields to update (excluding 'id', 'createdAt', and 'updatedAt')
        update_fields = {
            key: value
            for key, value in body.items()
            if key not in ["id", "createdAt", "updatedAt"] and value is not None
        }
        # Ensure there are fields to update
        if not update_fields:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": "No fields to update."}),
            }
        # Validate and convert job_id to ObjectId
        if not is_valid_object_id(job_id):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": "Invalid ObjectId format"}),
            }

        # Convert string ID to ObjectId
        object_id = ObjectId(job_id)

        # Connect to DocumentDB
        db = connect_to_docdb()
        job_details_collection = db["job_details"]
        edit_job_details_collection = db["edit_job_details"]

        # Retrieve the existing job details
        existing_job_details = job_details_collection.find_one({"_id": object_id})

        if not existing_job_details:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": f"No record found with _id: {job_id}"}),
            }

        # Store the edited details in 'edit_job_details' collection
        try:
            updated_job_details = {**existing_job_details, **update_fields}
            updated_job_details["job_id"] = object_id
            # Add createdAt and updatedAt timestamps
            updated_job_details["createdAt"] = existing_job_details.get("createdAt")
            updated_job_details["updatedAt"] = datetime.now()

            # Remove '_id' to avoid duplication issues
            updated_job_details.pop("_id", None)

            edit_job_details_collection.insert_one(updated_job_details)
        except PyMongoError as e:
            logger.error(f"Error inserting into edit_job_details: {str(e)}")
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps(
                    {"error": "Failed to save updated job details in edit_job_details", "details": str(e)}
                ),
            }

        # Successful response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"message": "success", "updated_fields": update_fields}),
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
