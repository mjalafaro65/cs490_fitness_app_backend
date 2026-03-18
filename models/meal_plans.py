from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class MealPlans(db.Model):
    __tablename__ = 'meal_plans'
    
    meal_plan_id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)