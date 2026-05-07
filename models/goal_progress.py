
from datetime import datetime

from db import db

class GoalProgress(db.Model):
    __tablename__ = "goal_progress"

    progress_id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.goal_id"), nullable=False)

    value = db.Column(db.Numeric(10,2), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)