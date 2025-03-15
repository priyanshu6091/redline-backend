import json
import logging
from typing import List
from pymongo import MongoClient
from pymongo.errors import PyMongoError

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def validate_coordinates(latitude: str, longitude: str):
    """Ensure that both latitude and longitude are strings and not empty"""
    if not isinstance(latitude, str) or not isinstance(longitude, str):
        raise ValueError("Latitude and longitude must be strings.")
    if not latitude or not longitude:
        raise ValueError("Latitude and longitude cannot be empty.")


def connect_to_docdb():
    """Establish a connection to DocumentDB"""
    try:
        # Create DocumentDB connection (assuming MongoDB-compatible)
        db = create_docdb_connection()
        return db
    except Exception as e:
        logger.error(f"Error connecting to DocumentDB: {str(e)}")
        raise Exception("Failed to connect to DocumentDB")


def lambda_handler(event, context):
    """
    Lambda function to handle requests for storing latitude and longitude.
    """
    try:
        # Parse the body of the request
        body = json.loads(event.get("body", "{}"))
        latitude = body.get("latitude")
        longitude = body.get("longitude")

        # Check for missing latitude or longitude
        if latitude is None or longitude is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*","Access-Control-Allow-Credentials": True},
                "body": json.dumps(
                    {"error": "Missing latitude or longitude in the request body."}
                ),
            }

        # Validate latitude and longitude
        try:
            validate_coordinates(latitude, longitude)
        except ValueError as ve:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*","Access-Control-Allow-Credentials": True},
                "body": json.dumps({"error": str(ve)}),
            }

        # Prepare data to store
        coordinates_data = {"latitude": latitude, "longitude": longitude}

        # Connect to DocumentDB
        db = connect_to_docdb()
        coordinates_collection = db[
            "coordinates"
        ]  # Get or create 'coordinates' collection

        # Store the data in DocumentDB (MongoDB-compatible)
        try:
            result = coordinates_collection.insert_one(coordinates_data)
            # Add the generated ObjectId to the response after converting it to a string
            coordinates_data["_id"] = str(result.inserted_id)
        except PyMongoError as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*","Access-Control-Allow-Credentials": True},
                "body": json.dumps(
                    {"error": "Failed to store data in MongoDB", "details": str(e)}
                ),
            }

        # Successful response with the list of stored coordinates
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*","Access-Control-Allow-Credentials": True},
            "body": json.dumps(
                {
                    "message": "Coordinates stored successfully.",
                    "stored_data": coordinates_data,
                }
            ),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*","Access-Control-Allow-Credentials": True},
            "body": json.dumps({"error": "Invalid JSON format in the request body."}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*","Access-Control-Allow-Credentials": True},
            "body": json.dumps({"error": "Internal server error", "details": str(e)}),
        }
