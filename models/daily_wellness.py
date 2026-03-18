from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class DailyWellness(db.Model):
    __tablename__ = 'daily_wellness'

    wellness_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    water_oz = db.Column(db.Integer, nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Numeric(5, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sleep_hours = db.Column(db.Numeric(4, 2))
    notes = db.Column(db.Text)