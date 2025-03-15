import json
import boto3
import random

s3_client = boto3.client('s3', region_name='us-east-1')
BUCKET_NAME = "redline-firewatch"
URL_EXPIRATION_SECONDS = 300  # 5 minutes

common_headers = {
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Credentials": True,

}

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        shift_id = body.get("shift_id")

        if not shift_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing shift_id in request"}),
                "headers": common_headers,
            }

        # Generate a random filename within the shift_id folder
        random_id = random.randint(100000, 999999)
        file_name = f"{shift_id}/{random_id}.jpeg"  # Images are stored under respective shift_id folder

        # Generate pre-signed URL
        upload_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_name,
                'ContentType': "image/jpeg"
            },
            ExpiresIn=URL_EXPIRATION_SECONDS,
            HttpMethod='PUT'
        )

        print("Generated URL:", upload_url)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "uploadURL": upload_url,
                "Key": file_name
            }),
            "headers": common_headers,
        }

    except Exception as e:
        print(f"Error generating upload URL: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to generate upload URL",
                "details": str(e)
            }),
            "headers": common_headers,
        }
