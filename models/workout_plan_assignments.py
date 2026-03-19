from datetime import datetime

from db import db

class AssignmentTypeEnum(db.Enum):
    coach = 'coach'
    self = 'self'

class RepeatRuleEnum(db.Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'

class AssignmentStatusEnum(db.Enum):
    active = 'active'
    completed = 'completed'
    cancelled = 'cancelled'

class WorkoutPlanAssignments(db.Model):
    __tablename__ = 'workout_plan_assignments'

    workout_plan_assignment_id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.plan_id'), nullable=False)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    assignment_type = db.Column(AssignmentTypeEnum, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    repeat_rule = db.Column(RepeatRuleEnum)
    status = db.Column(AssignmentStatusEnum)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)