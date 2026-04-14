from datetime import datetime
import enum
from db import db

class ShareTypeEnum(enum.Enum):
    view = 'view'
    copy = 'copy'

class SharedPlans(db.Model):
    __tablename__ = 'shared_plans'
    
    shared_plan_id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.plan_id'), nullable=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")
    share_type = db.Column(db.Enum(ShareTypeEnum))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)