from datetime import datetime

from db import db

class WorkoutPlanDays(db.Model):
    __tablename__ = 'workout_plan_days'

    plan_day_id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.plan_id'), nullable=False)
    day_label = db.Column(db.String(60), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False)
    # 0 = Monday … 6 = Sunday; optional if you only use day_label ordering
    weekday = db.Column(db.Integer, nullable=True)
    # Preferred time of day for this session within the week
    session_time = db.Column(db.Time, nullable=True)