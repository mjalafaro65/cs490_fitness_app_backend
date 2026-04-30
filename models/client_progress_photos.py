from datetime import datetime
from db import db

class ClientProgressPhotos(db.Model):
    __tablename__ = 'client_progress_photos'

    photo_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, nullable=False)
    before_photo_url = db.Column(db.String(500), nullable=True)
    after_photo_url = db.Column(db.String(500), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
