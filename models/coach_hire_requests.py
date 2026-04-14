from datetime import datetime
import enum
from db import db

class StatusEnum(enum.Enum):
    pending = "pending"
    approved = "approved"
    reject = "rejected"

class CoachHireRequests(db.Model):
    __tablename__ = 'coach_hire_requests'

    request_id = db.Column(db.Integer, primary_key=True)
    client_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    #cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")#
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.payment_plan_id'), nullable=True)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    autopay_enabled = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

