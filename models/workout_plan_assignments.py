from datetime import datetime
import enum
from db import db

class AssignmentTypeEnum(enum.Enum):
    coach = 'coach'
    self = 'self'

class RepeatRuleEnum(enum.Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'

class AssignmentStatusEnum(enum.Enum):
    active = 'active'
    completed = 'completed'
    cancelled = 'cancelled'

class WorkoutPlanAssignments(db.Model):
    __tablename__ = 'workout_plan_assignments'

    workout_plan_assignment_id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.plan_id'), nullable=False)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    assignment_type = db.Column(db.Enum(AssignmentTypeEnum), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    repeat_rule = db.Column(db.Enum(RepeatRuleEnum))
    status = db.Column(db.Enum(AssignmentStatusEnum))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)