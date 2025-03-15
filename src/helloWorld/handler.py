import os
import json
import logging
from typing import Dict, Any
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # First try direct import in case the directory is in the root
    from helper.db.docdb import create_docdb_connection
except ImportError:
    # If that fails, try to import using the full path from src
    from src.helper.db.docdb import create_docdb_connection

def connect(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for DocumentDB connection.

    Args:
        event (Dict): Lambda event
        context (LambdaContext): Lambda context

    Returns:
        Dict[str, Any]: Response with connection status and data
    """
    client = None
    try:
        # Create DocumentDB connection
        client = create_docdb_connection()

       
        db = client["REDLINE_FIREWATCH"]  # Use your database name
        collection = db["test"]  # Use your collection name

        # Perform a sample operation: Insert a document
        document = {"name": "alfas", "status": "success"}
        collection.insert_one(document)

        # Perform a sample query
        results = list(collection.find({}, {"_id": 0}).limit(10))
        logger.info(f"Query Results: {results}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Successfully connected to DocumentDB",
                "data": results
            })
        }

    except Exception as e:
        logger.error(f"Error during Lambda execution: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to process request",
                "message": str(e)
            })
        }

    finally:
        # Ensure connection is closed
        try:
            if client is not None:
                client.close()
                logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

# Lambda handler for direct invocation
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Entry point for the AWS Lambda function.
    """
    return connect(event, context)