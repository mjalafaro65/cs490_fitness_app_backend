from datetime import datetime
import enum
from db import db

class StatusEnum(enum.Enum):
    pending = "pending"
    reviewed = "reviewed"
    resolved = "resolved"
    dismissed = "dismissed"

class CoachReports(db.Model):
    __tablename__ = 'coach_reports'

    report_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.pending)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)