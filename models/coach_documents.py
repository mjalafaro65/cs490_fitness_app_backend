from datetime import datetime

from db import db

class StatusEnum(db.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CoachDocuments(db.Model):
    __tablename__ = 'coach_documents'
    
    document_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)
    document_url = db.Column(db.String(500), nullable=False)
    status = db.Column(StatusEnum, nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admin_users.admin_user_id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)