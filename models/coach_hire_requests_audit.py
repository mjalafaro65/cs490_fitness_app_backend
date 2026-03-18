from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class TypeEnum(db.Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class StatusEnum(db.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DENIED = "denied"
    CANCELLED = "cancelled"

class CoachHireRequestsAudit(db.Model):
    __tablename__ = 'coach_hire_requests_audit'

    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(TypeEnum, nullable=False)
    action_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action_by = db.Column(db.Integer)
    request_id = db.Column(db.Integer, nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    coach_id = db.Column(db.Integer, nullable=False)
    payment_plan_id = db.Column(db.Integer, nullable=True)
    status = db.Column(StatusEnum, nullable=False)
    decided_at = db.Column(db.DateTime, nullable=True)

