from datetime import datetime

from db import db

class Notifications(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    #cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")#
    notification_type_id = db.Column(db.Integer, db.ForeignKey('notification_types.notification_type_id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)