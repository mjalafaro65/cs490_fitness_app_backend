from datetime import datetime

from db import db

class ApprovalStatusEnum(db.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

class CoachProfiles(db.Model):
    __tablename__ = 'coach_profiles'

    coach_profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.specialty_id'), nullable=False)
    years_experience = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_picture_url = db.Column(db.String(500), nullable=True)
    approval_status = db.Column(ApprovalStatusEnum, nullable=False, default=ApprovalStatusEnum.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('admin_users.admin_user_id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    flagged_by = db.Column(db.Integer, db.ForeignKey('admin_users.admin_user_id'), nullable=True)
    flagged_at = db.Column(db.DateTime, nullable=True)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
