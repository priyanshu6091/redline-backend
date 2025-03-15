import json
import requests
from datetime import datetime, timedelta
import pytz
def lambda_handler(event, context):
    tampa_timezone = pytz.timezone('America/New_York')
    current_time = datetime.now(tampa_timezone)
    location_id='0a418c9b-df9a-471d-b92e-4eff672a627b'
    user_id=13635282
    # Format the current date and the next day
    start_date = current_time.strftime('%Y-%m-%d')
    end_date = (current_time + timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"https://app.joinhomebase.com/api/public/locations/{location_id}/shifts?page=1&per_page=25&start_date={start_date}&end_date={end_date}&open=false&with_note=false&date_filter=start_at"

    payload = {}
    headers = {
    'Accept': 'application/json',
    'X-CSRF-Token': 'sBsQtyetzfpppFZTral8TvIdjQBD0XUB-MsqT6Z46vU',
    'Authorization': 'Bearer 5zfxST1qxvWPQl7ay1USaItIXr9P0V0WqQo-7zorcIQ'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    
    latest_start = None
    latest_item = None
    
    for item in response.json():
        
        if item['user_id'] == user_id:
            start_time = datetime.fromisoformat(item['start_at'].replace('Z', '+00:00')).astimezone(tampa_timezone)

            # Update latest_start and latest_item if conditions are met
            if start_time <= current_time and (latest_start is None or start_time > latest_start):
                latest_start = start_time
                latest_item = item

    # Check if latest_start is today
    if latest_start and latest_start.date() == current_time.date():
        print("The latest start time is today.")
        # print("Latest Item:", latest_item)
        return {#+
            'statusCode': 200,#+
            'body': json.dumps({'shift':latest_item,'status':True})#+
        }#+
    else:#+
        return {#+
            'statusCode': 404,#+
            'body': json.dumps({'message':'No valid shifts found for the user','status':False})#+
        }#+

    # return {#-
    #     'statusCode': 200,#-
    #     'body': json.dumps('Hello from Lambda!')#-
    # }#-
#-
# For local testing#+
if __name__ == "__main__":#+
    lambda_handler(None, None)#+