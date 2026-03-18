from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class SavedCoach(db.Model):
    __tablename__ = 'saved_coaches'
    
    saved_coach_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.coach_id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)