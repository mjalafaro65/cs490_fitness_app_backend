from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class WorkoutPlanDays(db.Model):
    __tablename__ = 'plan_days'

    plan_day_id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.plan_id'), nullable=False)
    day_label = db.Column(db.String(60), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False)