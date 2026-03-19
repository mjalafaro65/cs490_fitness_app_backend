from datetime import datetime

from db import db

class StatusEnum(db.Enum):
    pending = 'pending'
    completed = 'completed'
    failed = 'failed'
    refunded = 'refunded'

class Payments(db.Model):
    __tablename__ = 'payments'
    
    payment_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.invoice_id'), nullable=False)
    payer_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    status = db.Column(StatusEnum, nullable=False)
    is_auto_payment = db.Column(db.Boolean, default=False)
    provider = db.Column(db.String(60), nullable=True)
    provider_ref = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)