from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class WorkoutLogs(db.Model):
    __tablename__ = 'workout_logs'

    workout_log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    calendar_workout_id = db.Column(db.Integer, db.ForeignKey('calendar_workouts.calendar_workout_id'))
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    