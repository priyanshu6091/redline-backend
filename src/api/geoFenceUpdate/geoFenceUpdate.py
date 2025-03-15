
import json
from bson import ObjectId
from datetime import datetime


try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection


def update_coordinates(shift_id, latitude, longitude):
    """Update coordinates in the shift collection"""
    db = create_docdb_connection()
    shifts = db['shifts']
    
    coordinate = {
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": datetime.utcnow()
    }
    
    # Update the shift document by pushing new coordinates to the array
    result = shifts.update_one(
        {"_id": ObjectId(shift_id)},
        {
            "$push": {
                "coordinates": coordinate
            }
        }
    )
    
    # client.close()
    return result.modified_count > 0

def lambda_handler(event, context):
    """Main Lambda handler for WebSocket events with timeout handling"""
    # Calculate remaining time for execution
    remaining_time = context.get_remaining_time_in_millis() if context else 30000
    
    # If we're close to timeout (less than 5 seconds), initiate reconnection
    if remaining_time < 5000:
        return {
            'statusCode': 1001,
            'body': json.dumps({'message': 'Connection timeout, please reconnect'})
        }
    
    # Get connection information from the event
    route_key = event['requestContext']['routeKey']
    
    # Handle different WebSocket routes
    if route_key == '$connect':
        # Handle new connection
        return {
            'statusCode': 200,
            'body': 'Connected'
        }
        
    elif route_key == '$disconnect':
        # Handle disconnection
        return {
            'statusCode': 200,
            'body': 'Disconnected'
        }
        
    elif route_key == 'updateLocation':
        try:
            # Parse the message body
            body = json.loads(event['body'])
            shift_id = body['shift_id']
            latitude = body['latitude']
            longitude = body['longitude']
            
            # Validate coordinates
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid coordinates'})
                }
            
            # Update coordinates in MongoDB
            success = update_coordinates(shift_id, latitude, longitude)
            
            if success:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Location updated successfully'})
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Shift not found'})
                }
                
        except KeyError as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing required field: {str(e)}'})
            }
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Internal server error: {str(e)}'})
            }
    
    # Handle unknown route
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Unknown route'})
    }
