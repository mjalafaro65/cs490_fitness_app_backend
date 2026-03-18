from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ActionTypeEnum(db.Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class StatusEnum(db.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DENIED = "denied"
    CANCELLED = "cancelled"

class CoachProfileAudit(db.Model):
    __tablename__ = 'coach_profile_audit'

    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(ActionTypeEnum, nullable=False)
    action_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action_by = db.Column(db.Integer)
    request_id = db.Column(db.Integer, nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    coach_profile_id = db.Column(db.Integer, nullable=False)
    payment_plan_id = db.Column(db.Integer, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)