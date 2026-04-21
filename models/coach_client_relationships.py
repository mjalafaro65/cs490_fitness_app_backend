from datetime import datetime
import enum


from db import db

class status_enum(enum.Enum):
    active = "active"
    inactive = "inactive"
    terminated = "terminated"

class CoachClientRelationships(db.Model):
    __tablename__ = "coach_client_relationships"

    relationship_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey("coach_profiles.coach_profile_id"), nullable=False)
    client_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    #cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")#
    
    payment_plan_id = db.Column(db.Integer, db.ForeignKey("payment_plans.payment_plan_id"), nullable=False)
    status = db.Column(db.Enum(status_enum), default=status_enum.active)
    termination_reason = db.Column(db.String(255))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, default=datetime.utcnow)