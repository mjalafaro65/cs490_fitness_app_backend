from datetime import datetime

from db import db

class PaymentMethods(db.Model):
    __tablename__ = 'payment_methods'
    
    payment_method_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_ID'), nullable=False)
    provider = db.Column(db.String(60), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    last4 = db.Column(db.String(4), nullable=False)
    brand = db.Column(db.String(30), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)