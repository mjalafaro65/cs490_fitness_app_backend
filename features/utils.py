from models import Notifications, NotificationTypes
from db import db

def create_notification(user_id=None, role_id=None, type_slug=None, title=None, body=None):
    """Helper to insert a notification into the DB session"""
    
    notif_type = NotificationTypes.query.filter_by(slug=type_slug).first()
    
    if notif_type:
        new_notif = Notifications(
            user_id=user_id,
            role_id=role_id,
            notification_type_id=notif_type.notification_type_id,
            title=title,
            body=body
        )
        db.session.add(new_notif)