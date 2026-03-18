from datetime import datetime
from sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CalendarWorkout(db.Model):
    __tablename__ = "calendar_workouts"
    calendar_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    plan_id = db.Column(db.Integer, nullable=False)
    coach_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    ### Statuses: 0 = scheduled, 1 = completed, 2 = missed, 3 = cancelled
    status = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)