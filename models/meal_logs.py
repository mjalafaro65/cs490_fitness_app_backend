from datetime import datetime
from sqlalchemy import ForeignKey, SQLAlchemy
from db import db

class MealLogs(db.Model):
    __tablename__ = 'meal_logs'
    
    meal_log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.user_id'), nullable=False)
    meal_id = db.Column(db.Integer, ForeignKey('meals.meal_id'), nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    servings = db.Column(db.Numeric(6, 2), nullable=False)
    notes = db.Column(db.Text)
    