from datetime import datetime
from typing import Dict, Any
import firebase_admin
from firebase_admin import credentials, messaging
import json
from bson import ObjectId

try:
    from helper.db.docdb import create_docdb_connection
except ImportError:
    from src.helper.db.docdb import create_docdb_connection

# Firebase initialization
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "river-freedom-444907-g7",
    "private_key_id": "5edb9e8aa1adb3b695ae2b7d1d0fb3824d818dcd",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCq8wwY6NpGmHM9\njx36da3f90KYSl2QsUPqNjJPLWMb/uA/RYi9tzk2DUnL1ysJ0ncbDxnFdnMUQaXY\nRYMsF5i3k7RvfAdezZh7Qot8yDFUO15hGzjDtoEwXEY97bGGQGnlRxAe2awR7XA8\nnVcco6QxjFRxCOK+NFyqMfCpnONQzov/o4MEG1bBWQNXHsaytLvH1tkB2xgQNbUJ\n5R3mbYTkJdmoQTGDl8fVa95cu0cA3HjzS3SIPhk0V7JhKRkk7EfpX6Pte8g07KRk\nkhKTSHo8KMqCXpIzhd5QPegEJPeYtfzgWicUw0DA+TrB4ePPzFBLVeKCn6gkUneY\nMC3a55llAgMBAAECggEAAP4//f4OVJYqpzsnYK7h13kDh0h5Ui+hdiEh+jFIj99T\ndLKl+HoxyCVcHiXOH3S8UekszGejhATcnozK1gz+C2T9iZ9GGLAnmGG61zr/hF6C\n7hv/IK31Aq+qjc4Nd7r0kosu5gr8M692NTfxy14NBGetDuoPDS1XM3ruS8H4VR4X\nplmtNVvd7qU97y48sqSzx4r7Ad1PDfFGA4OiBj4K2ubwvZKJ4FN/MBzLU2Gb9ftL\nFuoVwm6uiR3eW9LHomr6l1kuxx4cDsPwOem/kOooT144VzXWsz8KtxzC3sA0WWRe\nYo93mmw207H3H3RwMNL0IHqyw18EIHM2zji+B79WyQKBgQDRjlFhid4SHoGULrks\nr70duNAosvRq971i1NBj7LxrYEtb1FfThRYkk6oYLXl7qaiUkF0OTQBuL65k0IBk\ncI2Hi0CVWjU1cTimjKa8ao4K1Xyn/r7yQxx+Catcvb63oPBg5cjEyWciKl+rE+2e\nss0pHHU7FzbannqpM7iVxetdqQKBgQDQ1kqG+sbn16wuftj+GucyURQaI/5uZb0Z\nXioMQUDAIPyEivD3NubRaG3wbNJKBNYM7KWq9+BmZ7r4C/GEVHuoHGHfI+h+V3TL\nr0JAs8GDDOR49XeuAGKtqUG0cuSV9vP71lwoYKlw2EtanfHRoK6A0d+miE0RyjG6\n7/L4Z2/bXQKBgFSTDcFB9UB203FM0it42eiu+EQUxZSOW/8RSPGrT/g+Kuvq7W9O\n3Trx5cpQQCFqvcEH6qak6TGPSOEjTU48JsK3rt8YQzVIdsaxKXINxzoUI3Vh2QrJ\njyxHFsQdSGWwLJPO6ZKSfm9JjsbrChHss+SNubqZief94h974lmAQZfRAoGBALt6\nRPmcFAh6E3bCJWcpG7iOFO/KtFTDPNmTMUhDJC/W7RrH6L7mKJyBlYCrELWmVcrQ\nf4FWebs1ECIyBqV3enNW134MrGEPfiiEs4OGXAicAFeedcxdSDkCo5utMQx34FyK\n+by92h8V7b/x3u8DwuSehJrp7dY0oCRj2Mmrgj15AoGAcaHbrqTwjQCPVGqyAj0o\n5txfa00NkMPhthBLtUoCSTTTyubAOqwtT7DiADZuL++iNEZukw4eRpVGhP5goXka\n98jTI/YR1kS+zTFBoTmknxebIZZmHNPxMbvWLsav6TiWMOQJBD0fGEM710uPHvRu\nz4As81MbVzgKjqVFY41d0Aw=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@river-freedom-444907-g7.iam.gserviceaccount.com",
    "client_id": "111394919740883155293",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40river-freedom-444907-g7.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
})

try:
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase initialization failed: {e}")

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

def validate_input(body: Dict[str, Any]) -> tuple[bool, str]:
    if not body.get("sender_id"):
        return False, "sender_id is required"
    if not body.get("recepient_id"):
        return False, "recepient_id is required"
    if not body.get("shift_id"):
        return False, "shift_id is required"
    if not body.get("status"):
        return False, "status is required"
    return True, ""

def get_fcm_token(db, manager_id: str) -> str:
    try:
        if not manager_id:
            print(" Manager ID is missing")
            return None
            
        print(f" Looking up FCM token for manager ID: {manager_id}")
        user = db["users"].find_one({"_id": ObjectId(manager_id)}, {"fcmToken": 1})
        
        if user and "fcmToken" in user:
            fcm_token = user["fcmToken"]
            print(f" Found FCM Token: {fcm_token}")
            return fcm_token
        else:
            print(" No FCM token found for the given ID")
            return None
            
    except Exception as e:
        print(f" Error fetching FCM token: {str(e)}")
        return None

def send_fcm_notification(fcm_token: str, message: str):
    try:
        if not fcm_token:
            print(" FCM token is missing")
            return False
            
        notification = messaging.Message(
            notification=messaging.Notification(
                title="Emergency Alert",
                body=message
            ),
            data={
                'type': 'emergency',
                'message': message,
                'title': 'Emergency Alert',
                'timestamp': str(datetime.utcnow()),
                'channelId': 'emergency' 
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    priority='max',
                    sound='default',
                    # vibrate=True,
                    visibility='public'
                )
            ),
            apns=messaging.APNSConfig(
                headers={
                    'apns-priority': '10',
                    'apns-push-type': 'alert'
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title="Emergency Alert",
                            body=message
                        ),
                        sound='default',
                        badge=1,
                        category='emergency'
                    )
                )
            ),
            token=fcm_token
        )
        
        response = messaging.send(notification)
        print(f" Notification sent successfully: {response}")
        return True
        
    except Exception as e:
        print(f" Error sending notification: {str(e)}")
        return False

def insert_notification(collection, data: Dict[str, Any]) -> tuple[bool, str]:
    try:
        result = collection.insert_one(data)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, f"Database error: {str(e)}"

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        try:
            print("📥 Received event:", json.dumps(event, indent=2))
            if "body" in event:
                body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            else:
                return create_response(400, {"error": "Request body is missing"})
        except json.JSONDecodeError:
            return create_response(400, {"error": "Invalid JSON in request body"})

        is_valid, error_message = validate_input(body)
        if not is_valid:
            return create_response(400, {"error": error_message})

        db = create_docdb_connection()
        collection = db["notifications"]

        manager_id = body.get("recepient_id")
        fcm_token = get_fcm_token(db, manager_id)

        if not fcm_token:
            return create_response(400, {
                "status": "error",
                "message": "FCM token not found for the recipient"
            })

        user_id = body.get("sender_id")
        user_name = body.get("sender_name", "User")
        message = f"🚨 EMERGENCY: {user_name} has initiated a 911 emergency call. Immediate attention required!"

        data = {
            "sender_id": user_id,
            "recepient_id": manager_id,
            "shift_id": body.get("shift_id"),
            "message": message,
            "status": body.get("status"),
            "created_at": datetime.utcnow(),
            "type": "911CallAlertToManager",
            "priority": "high"
        }

        success, result = insert_notification(collection, data)
        if not success:
            return create_response(500, {"error": result})

        notification_sent = send_fcm_notification(fcm_token, message)
        
        if not notification_sent:
            return create_response(500, {
                "status": "partial_success",
                "message": "Data saved but notification failed to send",
                "inserted_id": result
            })

        return create_response(200, {
            "status": "success",
            "message": "911 call alert sent successfully",
            "inserted_id": result,
        })

    except Exception as e:
        print(f" Error in lambda_handler: {str(e)}")
        return create_response(500, {"status": "error", "message": f"Internal server error: {str(e)}"})