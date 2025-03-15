import json
from datetime import datetime
from bson import ObjectId
from typing import Dict, Any

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized API response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # Configure CORS as needed
        },
        "body": json.dumps(body),
    }


def validate_input(body: Dict[str, Any]) -> tuple[bool, str]:
    """Validate the input parameters"""
    if not body.get("shiftId"):
        return False, "shiftId is required"

    if not body.get("steps"):
        return False, "steps count is required"

    try:
        steps = int(body["steps"])
        if steps < 0:
            return False, "steps count must be positive"
    except ValueError:
        return False, "steps must be a valid number"

    try:
        ObjectId(body["shiftId"])
    except:
        return False, "Invalid shiftId format"

    return True, ""


def update_steps_in_db(db, shift_id: str, steps: int) -> tuple[bool, str]:
    """Update steps in MongoDB"""
    try:
        # Get the shifts collection
        shifts_collection = db["shifts"]

        # Convert string ID to ObjectId
        shift_object_id = ObjectId(shift_id)

        # Update the document
        result = shifts_collection.update_one(
            {"_id": shift_object_id},
            {"$set": {"steps": steps, "lastUpdated": datetime.now()}},
        )

        if result.matched_count == 0:
            return False, "Shift not found"

        if result.modified_count == 0:
            return False, "No changes made to the document"

        return True, "Steps updated successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler function"""
    try:
        # Connect to MongoDB
        db = create_docdb_connection()

        # Parse the request body
        try:
            body = (
                json.loads(event["body"])
                if isinstance(event.get("body"), str)
                else event.get("body", {})
            )
        except json.JSONDecodeError:
            return create_response(400, {"error": "Invalid JSON in request body"})

        # Validate input
        is_valid, error_message = validate_input(body)
        if not is_valid:
            return create_response(400, {"error": error_message})

        # Update steps in database
        success, message = update_steps_in_db(
            db=db, shift_id=body["shiftId"], steps=int(body["steps"])
        )

        if not success:
            return create_response(400, {"error": message})

        return create_response(
            200,
            {
                "message": message,
                "data": {"shiftId": body["shiftId"], "steps": body["steps"]},
            },
        )

    except Exception as e:
        return create_response(500, {"error": f"Internal server error: {str(e)}"})


# For local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps({"shiftId": "677e8426bb7c1db4d7aeea9d", "steps": 100})
    }
    print(json.dumps(lambda_handler(test_event, None), indent=2))
