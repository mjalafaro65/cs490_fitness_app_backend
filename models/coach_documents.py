from datetime import datetime
import enum

from db import db

class StatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class CoachDocuments(db.Model):
    __tablename__ = 'coach_documents'
    
    document_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)
    document_url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Enum(StatusEnum),  default=StatusEnum.pending)
    reviewed_by_admin_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)