from datetime import datetime


from db import db

class CalendarWorkouts(db.Model):
    __tablename__ = "calendar_workouts"
    calendar_workout_id = db.Column(db.Integer, primary_key=True)
    for_user_id = db.Column(db.Integer, nullable=False)
    plan_day_id = db.Column(db.Integer, db.ForeignKey("workout_plan_days.plan_day_id"), nullable=False)
    coach_id = db.Column(db.Integer, nullable=False)
    scheduled_start = db.Column(db.DateTime, nullable=False)
    scheduled_end = db.Column(db.DateTime, nullable=False)
    assignment_id = db.Column(db.Integer,nullable=True )
    ### Statuses: 0 = scheduled, 1 = completed, 2 = missed, 3 = cancelled
    status = db.Column(db.Enum('scheduled', 'completed', 'skipped', 'canceled'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plan_day = db.relationship("WorkoutPlanDays", backref="calendar_workouts")
    
    