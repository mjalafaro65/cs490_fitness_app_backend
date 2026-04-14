from datetime import datetime

from db import db

class SavedCoaches(db.Model):
    __tablename__ = 'saved_coaches'
    
    saved_coach_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")
    coach_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)