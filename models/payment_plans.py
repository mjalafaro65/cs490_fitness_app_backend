from datetime import datetime
import enum
from db import db

class BillTypeEnum(enum.Enum):
    one_time = 'one_time'
    recurring = 'recurring'

class PaymentPlans(db.Model):
    __tablename__ = 'payment_plans'
    
    payment_plan_id = db.Column(db.Integer, primary_key=True)
    coach_profile_id = db.Column(db.Integer, db.ForeignKey('coach_profiles.coach_profile_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    billing_type = db.Column(db.Enum(BillTypeEnum), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_custom = db.Column(db.Boolean, default=False)