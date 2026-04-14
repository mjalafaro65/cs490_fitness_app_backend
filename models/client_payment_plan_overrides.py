from datetime import datetime


from db import db
class ClientPaymentPlanOverrides(db.Model):
    __tablename__ = "client_payment_plan_overrides"
    override_id = db.Column(db.Integer, primary_key=True)
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.payment_plan_id'),nullable=False)
    client_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")
    custom_amount = db.Column(db.Numeric(10, 2), nullable=False)
    ### 0 = Monthly
    ### 1 = Yearly
    custom_interval = db.Column(db.Integer, nullable=False)
    custom_interval_count = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
    onupdate=datetime.utcnow)