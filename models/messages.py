from datetime import datetime

from db import db

class Messages(db.Model):
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=False)
    sender_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime)