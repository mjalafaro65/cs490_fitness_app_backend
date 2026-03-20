from datetime import datetime

from db import db

class Exercises(db.Model):
    __tablename__ = "exercises"

    exercise_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    muscle_group = db.Column(db.String(60), nullable=False)
    equipment = db.Column(db.String(60), nullable=False)
    training_type = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)