from datetime import datetime

from db import db

class WorkoutPlanDayExercises(db.Model):
    __tablename__ = 'workout_plan_day_exercises'

    day_exercise_id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey('workout_plan_days.plan_day_id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Numeric(10, 2))
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False)