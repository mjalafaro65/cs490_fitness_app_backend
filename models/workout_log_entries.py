from datetime import datetime

from db import db

class WorkoutLogEntries(db.Model):
    __tablename__ = 'workout_log_entries'

    workout_log_entry_id = db.Column(db.Integer, primary_key=True)
    workout_log_id = db.Column(db.Integer, db.ForeignKey('workout_logs.workout_log_id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    plan_day_exercise_id = db.Column(db.Integer, db.ForeignKey('workout_plan_day_exercises.day_exercise_id'))
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Numeric(10, 2),nullable=True)
    rpe = db.Column(db.Numeric(3, 1), nullable=True)
    distance = db.Column(db.Numeric(10, 2),nullable=True)
    calories = db.Column(db.Integer, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
