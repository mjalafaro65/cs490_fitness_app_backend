from datetime import datetime

from db import db

class Conversations(db.Model):
    __tablename__ = 'conversations'

    conversation_id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.Integer, unique=True, nullable=False)
    conversation_type = db.Column(db.String(20), default='direct', nullable=False)  # direct, group
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)