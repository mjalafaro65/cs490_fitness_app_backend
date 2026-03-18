from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class StatusEnum(db.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CoachHireRequest(db.Model):
    __tablename__ = 'coach_hire_requests'

    request_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.client_profile_id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.payment_plan_id'), nullable=True)
    status = db.Column(StatusEnum, nullable=False)
    autopay_enabled = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

