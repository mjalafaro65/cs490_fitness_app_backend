from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ActionTypeEnum(db.Enum):
    Insert = "insert"
    Update = "update"
    Delete = "delete"

class StatusEnum(db.Enum):
    Active = "active"
    Inactive = "inactive"
    Terminated = "terminated"

class CoachClientRelationshipAudit(db.Model):
    __tablename__ = "coach_client_relationships_audits"

    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(ActionTypeEnum, nullable=False)
    action_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action_by_user_id = db.Column(db.Integer, nullable=True)
    relationship_id = db.Column(db.Integer, nullable=False)
    coach_profile_id = db.Column(db.Integer, nullable=False)
    client_user_id = db.Column(db.Integer, nullable=False)
    status = db.Column(StatusEnum, nullable=False)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)

    