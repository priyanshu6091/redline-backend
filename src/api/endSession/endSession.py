import json
import traceback
from bson import ObjectId
from datetime import datetime  # Import the datetime module

# Import the connection creation function
try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

# MongoDB connection
def get_mongodb_connection():
    db = create_docdb_connection()  # Use the imported create_docdb_connection
    return db

# Update shift status to inactive and add endTime as a string
def update_shift_status(db, shift_id: str):
    collection = db['shifts']
    
    # Check if the shift exists
    shift = collection.find_one({'_id': ObjectId(shift_id)})
    if not shift:
        return {'success': False, 'message': 'Shift not found'}
    
    # Get the current time for endTime and convert it to a string
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Update shift status to inactive and add endTime as a string
    result = collection.update_one(
        {'_id': ObjectId(shift_id)}, 
        {'$set': {'status': 'Inactive', 'endTime': current_time}}
    )
    
    if result.modified_count > 0:
        return {'success': True, 'message': 'success'}
    else:
        return {'success': False, 'message': 'No changes made'}

# Lambda handler
def lambda_handler(event, context):
    common_headers = {
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Extract shiftId from the request body
        shift_id = body.get('shiftId')
        if not shift_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'shiftId is required'}),
                'headers': common_headers
            }
        
        # Get MongoDB connection
        db = get_mongodb_connection()

        # Update shift status
        update_result = update_shift_status(db, shift_id)
        
        # Return response
        return {
            'statusCode': 200,
            'body': json.dumps(update_result, indent=4),
            'headers': common_headers
        }
    
    except Exception as e:
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'}),
            'headers': common_headers
        }
