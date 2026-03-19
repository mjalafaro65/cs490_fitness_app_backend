from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Conversations(db.Model):
    __tablename__ = 'conversations'

    conversation_id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.Integer, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)