from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class RepeatEnum(db.Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    biweekly = 'biweekly'
    monthly = 'monthly'

class StatusEnum(db.Enum):
    active = 'active'
    completed = 'completed'
    cancelled = 'cancelled'

class MealPlanAssignments(db.Model):
    __tablename__ = 'meal_plan_assignments'
    
    assignment_id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('meal_plans.meal_plan_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    repeat_rule = db.Column(RepeatEnum, default=RepeatEnum.none, nullable=False)
    status = db.Column(StatusEnum, default=StatusEnum.active, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)