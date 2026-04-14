from datetime import datetime
import enum
from db import db

class StatusEnum(enum.Enum):
    open = 'open'
    under_review = 'under_review'
    approved = 'approved'
    rejected = 'rejected'
    closed = 'closed'

class RefundDisputes(db.Model):
    __tablename__ = 'refund_disputes'
    
    refund_dispute_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.payment_id'), nullable=False)
    opened_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.open)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    resoltion_notes = db.Column(db.Text, nullable=True)
