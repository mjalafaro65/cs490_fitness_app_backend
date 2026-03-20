from datetime import datetime
import enum
from db import db

class IntervalEnum(enum.Enum):
    month = 'month'
    year = 'year'

class PaymentPlanRecurringDetails(db.Model):
    __tablename__ = 'payment_plan_recurring_details'
    
    details_id = db.Column(db.Integer, primary_key=True)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.payment_plan_id'), nullable=False)
    interval_unit = db.Column(db.Enum(IntervalEnum), nullable=False)
    interval_count = db.Column(db.Integer, nullable=False)