from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class CoachProgressPhotos(db.Model):
    __tablename__ = 'coach_progress_photos'

    photo_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    before_photo_url = db.Column(db.String(500), nullable=False)
    after_photo_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)