from datetime import datetime
import enum
from db import db

class InteractionType(enum.Enum):
    helpful = 'helpful'
    unhelpful = 'unhelpful'

class ReviewInteractions(db.Model):
    __tablename__ = 'review_interactions'
    
    interaction_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('coach_reviews.review_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    interaction_type = db.Column(db.Enum(InteractionType))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
