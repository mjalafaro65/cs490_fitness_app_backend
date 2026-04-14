from datetime import datetime

from db import db

class WorkoutPlans(db.Model):
    __tablename__ = 'workout_plans'

    plan_id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    is_public= db.Column(db.Boolean)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    copied_from_plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.plan_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)