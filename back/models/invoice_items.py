from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class InvoiceItems(db.Model):
    __tablename__ = 'invoice_items'

    invoice_itemid = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)