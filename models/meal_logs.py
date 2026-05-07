from datetime import datetime
from sqlalchemy import ForeignKey
from db import db

class MealLogs(db.Model):
    __tablename__ = 'meal_logs'
    
    meal_log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.user_id'), nullable=False)
    custom_meal_name = db.Column(db.String(150), nullable=True)
    #cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")#
    meal_id = db.Column(db.Integer, ForeignKey('meals.meal_id'), nullable=True)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    calories = db.Column(db.Integer, nullable=True)

    servings = db.Column(db.Numeric(6, 2), nullable=False)
    notes = db.Column(db.Text)
    