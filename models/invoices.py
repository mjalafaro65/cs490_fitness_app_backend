from datetime import datetime
import enum
from db import db

class StatusEnum(enum.Enum):
    issued = "issued"
    paid = "paid"
    voided = "voided"
    past_due = "past_due"

class Invoices(db.Model):
    __tablename__ = "invoices"

    invoice_id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("coach_client_relationships.relationship_id"), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey("payment_methods.payment_method_id"), nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.issued)
    currency = db.Column(db.String(3), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    issued_at = db.Column(db.DateTime, nullable=True)
    pay_date = db.Column(db.DateTime, nullable=True)