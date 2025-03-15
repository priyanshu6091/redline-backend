import os
import logging
# import boto3

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ssm = boto3.client("ssm")
# PYTHON_DB_URL = os.environ.get("DOC_DB_URI")
# mongo_uri = ssm.get_parameter(Name=PYTHON_DB_URL, WithDecryption=True)["Parameter"][
#     "Value"
# ]
# # Cached database connection
CACHE_DB  = None
def get_mongo_uri():
    try:
        # Directly fetch the URI from the environment variables
        mongo_uri = os.environ.get('DOC_DB_URI')
        print(mongo_uri)
        if not mongo_uri:
            raise ValueError("Mongo connection URI not found in environment variables")

        return mongo_uri

    except Exception as e:
        print(f"Error fetching Mongo URI: {str(e)}")
        raise  # Re-raise the error to be handled by the calling function


def create_docdb_connection() -> MongoClient:
    """
    Create a connection to DocumentDB.
    
    Args:
        credentials (Dict[str, str]): Database credentials
    
    Returns:
        MongoClient: Configured MongoDB client
    """
    try:
        # Retrieve connection parameters
        
        # print(os.)
        if CACHE_DB is not None:
            return CACHE_DB

        connection_uri = get_mongo_uri()
        
        # Create MongoDB Client with specific options
        client = MongoClient(
            connection_uri,
            tls=True,
            tlsAllowInvalidHostnames=False,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Verify connection
        client.admin.command('ping')
        logger.info("Successfully connected to DocumentDB")
        stage_Name = os.environ.get("STAGE")
        db = client[f'REDLINE_FIREWATCH_{stage_Name}']
        
        
        return db
    
    except ConnectionFailure as e:
        logger.error("Failed to connect to DocumentDB: %s", str(e))

        raise
    except Exception as e:
        logger.error("Unexpected error in connection: %s",str(e))
        raise