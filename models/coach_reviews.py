from datetime import datetime
from sqlalchemy import CheckConstraint
from db import db

class CoachReviews(db.Model):
    __tablename__ = 'coach_reviews'

    review_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    client_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating = db.Column(db.Integer, CheckConstraint('rating >= 1 AND rating <= 100'), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    is_anon = db.Column(db.Boolean, default=False, nullable=False)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
