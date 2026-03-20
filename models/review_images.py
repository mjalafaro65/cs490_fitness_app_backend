from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ReviewImages(db.Model):
    __tablename__ = 'review_images'
    
    review_image_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.review_id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)