from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ReviewFlags(db.Model):
    __tablename__ = 'review_flags'
    
    review_flag_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.review_id'), nullable=False)
    flagged_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)