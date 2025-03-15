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
    if not body.get("shiftId"):
        return False, "shiftId is required"
    return True, ""

def get_user_from_shift(db, shift_id: str) -> dict:
    try:
        if not shift_id:
            print("Shift ID is missing")
            return None
            
        print(f"Looking up shift details for shift ID: {shift_id}")
        shift = db["shifts"].find_one({"_id": ObjectId(shift_id)})
        
        if not shift:
            print(f"No shift found with ID: {shift_id}")
            return None
            
        user_id = shift.get("userID")
        if not user_id:
            print(f"No user ID found in shift: {shift_id}")
            return None
            
        print(f"Looking up user details for user ID: {user_id}")
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            print(f"No user found with ID: {user_id}")
            return None
            
        return {
            "user_id": str(user["_id"]),
            "fcm_token": user.get("fcmToken"),
            "name": user.get("name", "User")
        }
    except Exception as e:
        print(f"Error fetching user from shift: {str(e)}")
        return None

def get_fcm_token_from_manager(db, manager_id: str) -> tuple[str, str]:
    try:
        if not manager_id:
            print("Manager ID is missing")
            return None, None
            
        print(f"Looking up FCM token for manager ID: {manager_id}")
        manager = db["users"].find_one({"_id": ObjectId(manager_id)})
        
        if manager and "fcmToken" in manager:
            fcm_token = manager["fcmToken"]
            manager_name = manager.get("name", "Manager")
            print(f"Found FCM Token for manager: {fcm_token}")
            return fcm_token, manager_name
        else:
            print("No FCM token found for the manager")
            return None, None
            
    except Exception as e:
        print(f"Error fetching manager FCM token: {str(e)}")
        return None, None

def check_report_exists(db, shift_id: str) -> bool:
    try:
        if not shift_id:
            return False
            
        print(f"Checking if report exists for shift ID: {shift_id}")
        # Use shift_id instead of shiftId to match your document structure
        report = db["incidents"].find_one({"shift_id": ObjectId(shift_id)})
        
        return report is not None
    except Exception as e:
        print(f"Error checking report existence: {str(e)}")
        return False

def send_fcm_notification(fcm_token: str, message: str):
    try:
        if not fcm_token:
            print("FCM token is missing")
            return False
            
        notification = messaging.Message(
            notification=messaging.Notification(
                title="Report Reminder",
                body=message
            ),
            data={
                'type': 'report_reminder',
                'message': message,
                'title': 'Report Reminder',
                'timestamp': str(datetime.utcnow()),
                'channelId': 'report_reminder'
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    priority='high',
                    sound='default',
                    visibility='public'
                )
            ),
            apns=messaging.APNSConfig(
                headers={
                    'apns-priority': '5',
                    'apns-push-type': 'alert'
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title="Report Reminder",
                            body=message
                        ),
                        sound='default',
                        badge=1,
                        category='report_reminder'
                    )
                )
            ),
            token=fcm_token
        )
        
        response = messaging.send(notification)
        print(f"Notification sent successfully: {response}")
        return True
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
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

        shift_id = body.get("shiftId")
        manager_id = body.get("managerId")  # Get manager ID from request
        
        db = create_docdb_connection()
        
        # Removed shift existence check
            
        # Check if report exists for this shift
        report_exists = check_report_exists(db, shift_id)
        
        # If report already exists, no need to send notification
        if report_exists:
            print(" Shift ID  exists no need message")

            return create_response(200, {
                "status": "success",
                "message": "Report already exists for this shift",
                "isReportFilled": True,
                "shiftExists": True
            })
            
        # First try to get user info from shift
        user_info = get_user_from_shift(db, shift_id)
        fcm_token = None
        notification_recipient = None
        recipient_id = None
        recipient_type = None
        
        # If user has FCM token, use it
        if user_info and user_info.get("fcm_token"):
            fcm_token = user_info.get("fcm_token")
            notification_recipient = user_info.get("name", "User")
            recipient_id = user_info.get("user_id")
            recipient_type = "user"
        # Otherwise try to get manager's FCM token
        elif manager_id:
            manager_fcm_token, manager_name = get_fcm_token_from_manager(db, manager_id)
            fcm_token = manager_fcm_token
            notification_recipient = manager_name
            recipient_id = manager_id
            recipient_type = "manager"
        
        # If no FCM token found anywhere, return error
        if not fcm_token:
            return create_response(400, {
                "status": "error",
                "message": "FCM token not found for user or manager",
                "isReportFilled": False,
                "shiftExists": True
            })

        collection = db["notifications"]
        message = f"Hi {notification_recipient}, please remember to fill out the shift report form."

        # Record this notification in the database
        data = {
            "user_id": recipient_id,
            "shift_id": ObjectId(shift_id),
            "message": message,
            "status": "sent",
            "created_at": datetime.utcnow(),
            "type": "ReportReminder",
            "priority": "normal",
            "recipient_type": recipient_type
        }

        success, result = insert_notification(collection, data)
        if not success:
            return create_response(500, {"error": result})

        # Send the notification
        notification_sent = send_fcm_notification(fcm_token, message)
        
        if not notification_sent:
            
            return create_response(500, {
                "status": "partial_success",
                "message": "Data saved but notification failed to send",
                "inserted_id": result,
                "shiftExists": True
            })

        return create_response(200, {
            "status": "success",
            "message": "Report reminder sent successfully",
            "inserted_id": result,
            "isReportFilled": False,
            "shiftExists": True,
            "notificationSent": True,
            "recipientType": recipient_type
        })

    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {"status": "error", "message": f"Internal server error: {str(e)}"})