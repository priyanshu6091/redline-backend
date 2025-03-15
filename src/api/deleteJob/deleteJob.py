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
    Lambda function to delete a job entry from the 'job_details' collection based on the provided ID.
    """
    try:
        # Parse the body of the request
        body = json.loads(event.get("body", "{}"))
        
        # Extract 'id' from the request body
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

        # Attempt to delete the document
        delete_result = job_details_collection.delete_one({"_id": object_id})

        if delete_result.deleted_count == 0:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": True,
                },
                "body": json.dumps({"error": f"No record found with _id: {job_id}"}),
            }

        # Successful response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"message": "success", "deleted_id": job_id}),
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
