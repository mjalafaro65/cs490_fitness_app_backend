from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Meals(db.Model):
    __tablename__ = 'meals'

    meal_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    meal_type = db.Column(db.String(20))
    calories = db.Column(db.Integer)
    protein = db.Column(db.Numeric(6, 2))
    carbs = db.Column(db.Numeric(6, 2))
    fats = db.Column(db.Numeric(6, 2))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)