from datetime import datetime
import enum
from db import db

class GoalType(enum.Enum):
    weight = "weight"
    strength = "strength"
    performance = "performance"
    nutrition = "nutrition"
    custom = "custom"

class StatusEnum(enum.Enum):
    active = "active"
    completed = "completed"
    paused = "paused"

class Goals(db.Model):
    __tablename__ = "goals"
    
    goal_id = db.Column(db.Integer, primary_key=True)
    for_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    goal_type = db.Column(db.Enum(GoalType), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    target_value = db.Column(db.Numeric(10,2))
    unit = db.Column(db.String(30))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.active)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text)
