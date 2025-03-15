import json
from datetime import datetime
from typing import Dict, Any
from pymongo import MongoClient

# Import the function to create the database connection
try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Generates an HTTP response with JSON headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(body),
    }

def validate_input(body: dict) -> tuple[bool, str]:
    """Validates input fields for the alert."""
    if not body.get("sender_id"):
        return False, "sender_id is required"
    if not body.get("recepient_id"):
        return False, "recepient_id is required"
    if not body.get("shift_id"):
        return False, "shift_id is required"
    if not body.get("status"):
        return False, "status is required"
    return True, ""

def insert_notification(collection, data: Dict[str, Any]) -> tuple[bool, str]:
    """Inserts notification data into the MongoDB collection."""
    try:
        result = collection.insert_one(data)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, f"Database error: {str(e)}"

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for the missed photo alert."""
    try:
        # Debug: Inspect event structure
        print(f"Received Event: {event}")

        # Parse the request body
        body = event.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return create_response(400, {"error": "Invalid JSON in request body"})
        elif not isinstance(body, dict):
            return create_response(400, {"error": "Request body must be a JSON object"})

        # Validate input
        is_valid, error_message = validate_input(body)
        if not is_valid:
            return create_response(400, {"error": error_message})

        # Connect to the database
        db = create_docdb_connection()
        collection = db["notifications"]

        # Prepare the notification data
        user_id = body.get("sender_id")
        user_name = body.get("sender_name", "User")
        message = body.get(
            "message", f"{user_name} failed to complete the required action."
        )

        data = {
            "sender_id": user_id,
            "recepient_id": body.get("recepient_id"),
            "shift_id": body.get("shift_id"),
            "message": message,
            "status": body.get("status"),
            "created_at": datetime.utcnow(),
            "type": "MissedIncidentPhotoAlert",
        }

        # Insert data into MongoDB
        success, result = insert_notification(collection, data)
        if not success:
            return create_response(500, {"error": result})

        # Return a success response
        return create_response(
            200,
            {
                "message": "Alert inserted successfully",
                "inserted_id": result,
                "status": True,
            },
        )

    except Exception as e:
        # Debug: Log unexpected errors
        print(f"Unexpected error: {str(e)}")
        return create_response(500, {"error": f"Internal server error: {str(e)}"})