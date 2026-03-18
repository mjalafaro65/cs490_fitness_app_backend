from datetime import datetime
from sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class ClientPaymentPlanOverride(db.Model):
    __tablename__ = "client_payment_plan_overrides"
    override_id = db.Column(db.Integer, primary_key=True)
    payment_plan_id = db.Column(db.Integer, nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    ### 0 = Monthly
    ### 1 = Yearly
    interval = db.Column(db.Integer, nullable=False)
    interval_amount = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
     onupdate=datetime.utcnow)