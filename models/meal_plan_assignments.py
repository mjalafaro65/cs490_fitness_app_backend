from datetime import datetime
import enum
from db import db

class RepeatEnum(enum.Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    biweekly = 'biweekly'
    monthly = 'monthly'

class StatusEnum(enum.Enum):
    active = 'active'
    completed = 'completed'
    canceled = 'canceled'

class MealPlanAssignments(db.Model):
    __tablename__ = 'meal_plan_assignments'
    
    meal_plan_assignment_id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('meal_plans.meal_plan_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    #cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")#
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    repeat_rule = db.Column(db.Enum(RepeatEnum), default=RepeatEnum.none, nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.active, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)