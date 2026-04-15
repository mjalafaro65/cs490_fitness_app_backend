from datetime import datetime
import enum
from db import db

class StatusEnum(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    denied = "denied"
    canceled = "canceled"

class CoachHireRequests(db.Model):
    __tablename__ = 'coach_hire_requests'

    request_id = db.Column(db.Integer, primary_key=True)
    client_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.payment_plan_id'), nullable=True)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    auto_pay_enabled = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decided_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

