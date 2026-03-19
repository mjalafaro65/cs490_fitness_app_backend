from datetime import datetime

from db import db

class status_enum(db.Enum):
    active = "active"
    inactive = "inactive"
    terminated = "terminated"

class CoachClientRelationships(db.Model):
    __tablename__ = "coach_client_relationships"

    relationshi_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer,
     db.ForeignKey("coach_profiles.coach_profile_id"), nullable=False)
    client_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey("payment_plans.payment_plan_id"), nullable=False)
    status = db.Column(status_enum, default=status_enum.active)
    term_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)