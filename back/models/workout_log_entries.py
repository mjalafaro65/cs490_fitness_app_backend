from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class WorkoutLogEntry(db.Model):
    __tablename__ = 'workout_log_entries'

    workout_log_entry_id = db.Column(db.Integer, primary_key=True)
    workout_log_id = db.Column(db.Integer, db.ForeignKey('workout_logs.workout_log_id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    plan_day_exercise_id = db.Column(db.Integer, db.ForeignKey('plan_day_exercises.plan_day_exercise_id'))
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Numeric(10, 2))
    rpe = db.Column(db.Numeric(3, 1))
    distance = db.Column(db.Numeric(10, 2))
    calories_burned = db.Column(db.Integer)
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
