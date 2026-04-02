from datetime import datetime
import enum
from db import db

class ApprovalStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    switched= "switched"

class CoachProfiles(db.Model):
    __tablename__ = 'coach_profiles'

    coach_profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.specialty_id'), nullable=False)
    years_experience = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    
    profile_photo = db.Column(db.String(255), nullable=True) 
    
    status = db.Column(db.Enum(ApprovalStatusEnum), nullable=False, default=ApprovalStatusEnum.pending)
    
    approved_by_admin_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    flagged_by_admin_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    flagged_at = db.Column(db.DateTime, nullable=True)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)