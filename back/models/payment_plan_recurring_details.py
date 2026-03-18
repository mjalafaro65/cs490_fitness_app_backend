from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class IntervalEnum(db.Enum):
    month = 'month'
    year = 'year'

class PaymentPlanRecurringDetails(db.Model):
    __tablename__ = 'payment_plan_recurring_details'
    
    details_id = db.Column(db.Integer, primary_key=True)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.plan_id'), nullable=False)
    interval_unit = db.Column(IntervalEnum, nullable=False)
    interval_count = db.Column(db.Integer, nullable=False)