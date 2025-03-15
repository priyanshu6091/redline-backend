import json
import pymongo
from bson import ObjectId

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def get_mongodb_connection():
    """Create MongoDB connection"""
    db = create_docdb_connection()
    return db

def lambda_handler(event, context):
    """Fetch the email from the users collection by user_id"""
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,GET",
    }
    try:
        # Extract user_id from the request body
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")

        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "user_id is required"
                }),
                "headers": common_headers
            }

        # Validate the user_id
        if not ObjectId.is_valid(user_id):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Invalid user_id format"
                }),
                "headers": common_headers
            }

        # Connect to MongoDB
        db = get_mongodb_connection()
        users_collection = db["users"]

        # Fetch the user from the users collection
        user = users_collection.find_one({"_id": ObjectId(user_id)}, {"_id": 0, "email": 1})

        if not user:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "User not found"
                }),
                "headers": common_headers
            }

        # Return the email of the user
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Email fetched successfully",
                "email": user.get("email")
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
