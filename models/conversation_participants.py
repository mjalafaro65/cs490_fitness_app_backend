from datetime import datetime

from db import db

class ConversationParticipants(db.Model):
    __tablename__ = 'conversation_participants'
    
    participant_id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_read_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    conversation = db.relationship('Conversations', foreign_keys=[conversation_id], backref='participants')
    user = db.relationship('Users', foreign_keys=[user_id], backref='conversation_participations')
    
    # Unique constraint to prevent duplicate participants
    __table_args__ = (db.UniqueConstraint('conversation_id', 'user_id', name='unique_conversation_user'),)
