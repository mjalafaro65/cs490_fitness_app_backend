from datetime import datetime

from db import db

class Conversations(db.Model):
    __tablename__ = 'conversations'

    conversation_id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.Integer, unique=True, nullable=False)
    conversation_type = db.Column(db.String(20), default='direct', nullable=False)  # direct, group
   
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    participants = db.relationship(
            "Users",
            secondary="conversation_participants",
            viewonly=True
    )
    
    participant_links = db.relationship(
        "ConversationParticipants",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )