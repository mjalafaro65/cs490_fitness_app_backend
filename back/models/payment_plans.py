from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class BillTypeEnum(db.Enum):
    one_time = 'one_time'
    recurring = 'recurring'

class PaymentPlan(db.Model):
    __tablename__ = 'payment_plans'
    
    payment_plan_id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.coach_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    billing_type = db.Column(BillTypeEnum, nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_custom = db.Column(db.Boolean, default=False)