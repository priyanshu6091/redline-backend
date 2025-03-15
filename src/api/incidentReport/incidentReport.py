import json
from datetime import datetime
from typing import Dict, Any, Tuple
from bson import ObjectId


try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(body),
    }

def validate_input(body: Dict[str, Any]) -> Tuple[bool, str]:
    # Define required fields and their validation rules
    required_fields = {
        "incident_title": {"type": str, "max_length": 255},
        "incident_type": {"type": str},  
        "date": {"type": str},
        "time": {"type": str}, 
        "description": {"type": str},    
        "location": {"type": str},
        "user_id": {"type": int},
        "shift_id": {"type": str},  # Changed from int to str
    }

    # Validate each required field
    for field, rules in required_fields.items():
        # Check if the field is present
        if field not in body or body[field] is None:
            return False, f"{field} is required"

        # Check if the type matches
        if not isinstance(body[field], rules["type"]):
            print(f"{field} type mismatch: Expected {rules['type'].__name__}, got {type(body[field]).__name__}")  # Debug
            return False, f"{field} must be of type {rules['type'].__name__}"

        # Validate max length (if applicable)
        if "max_length" in rules and isinstance(body[field], str):
            print(f"Validating {field}: {len(body[field])} characters")  # Debug
            if len(body[field]) > rules["max_length"]:
                return False, f"{field} exceeds maximum length of {rules['max_length']} characters"



    if "shift_id" in body:
        try:
            ObjectId(body["shift_id"])  # Test if it can be converted to ObjectId
        except Exception:
            return False, "shift_id must be a valid ObjectId string"
        
    try:
        datetime.strptime(body["date"], "%m/%d/%Y") #change it to MM/DD/YYYY
    except ValueError:
        return False, "date must be in MM/DD/YYYY format"

    try:
        datetime.strptime(body["time"], "%H:%M:%S")
    except ValueError:
        return False, "time should be in HH:MM:SS format"

    # Validate othertype if present
    if "othertype" in body and body["othertype"]:
        if not isinstance(body["othertype"], str):
            return False, "othertype must be a string"
        if len(body["othertype"]) > 255:
            return False, "othertype exceeds maximum length of 255 characters"

    return True, ""


def insert_incident(collection, data: Dict[str, Any]) -> tuple[bool, str]:
    try:
        result = collection.insert_one(data)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, f"Database error: {str(e)}"

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        try:
            if "body" in event:
                body = (
                    json.loads(event["body"])
                    if isinstance(event["body"], str)
                    else event["body"]
                )
            else:
                return create_response(400, {"error": "Request body is missing"})
        except json.JSONDecodeError:
            return create_response(400, {"error": "Invalid JSON in request body"})

        
        is_valid, error_message = validate_input(body)
        if not is_valid:
            return create_response(400, {"error": error_message})

        
        db = create_docdb_connection()
        collection = db["incidents"]

        
        data = {
            "incident_title": body["incident_title"],
            "description": body["description"],
            "incident_type": body["incident_type"],
            "date": body["date"],
            "time": body["time"],
            "location": body["location"],
            "user_id": body["user_id"],
            "shift_id":  ObjectId(body["shift_id"]),  
            "othertype": body.get("othertype",""),
            "created_at": datetime.utcnow().isoformat(),
        }

        
        success, result = insert_incident(collection, data)
        if not success:
            return create_response(500, {"error": result})

        
        return create_response(
            200,
            {
                "status": "success",
                "message": "Incident report submitted successfully",
                "inserted_id": result,
            },
        )

    except Exception as e:
        
        return create_response(
            500,
            {"status": "error", "message": f"Internal server error: {str(e)}"},
        )