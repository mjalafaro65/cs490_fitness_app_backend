from datetime import datetime
from db import db

class CoachFavorites(db.Model):
    __tablename__ = 'coach_favorites'
    
    favorite_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Ensure unique user-coach combination
    __table_args__ = (
        db.UniqueConstraint('user_id', 'coach_profile_id', name='unique_user_coach_favorite'),
    )
