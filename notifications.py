from database import db
from datetime import datetime, timedelta

def create_notification(recipient_user_id, sender_user_id, notification_message):
    utc_time = datetime.utcnow()
    ist_time = utc_time + timedelta(hours=5, minutes=30)

    notification = {
        "recipient_user_id": recipient_user_id,
        "sender_user_id": sender_user_id,
        "notification_type": "follow",
        "notification_message": notification_message,
        "timestamp": ist_time
    }
    db.notifications.insert_one(notification)