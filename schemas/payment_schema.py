from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import MealLogs
from db import db

class CreateInvoiceSchema(Schema):
    payment_id = fields.Int(dump_only=True)
    invoice_id = fields.Int(dump_only=True)
    payer_user_id = fields.Int(required=True)
    amount = fields.Float(required=True)
    status = fields.Str(dump_only=True)
    is_auto_pay = fields.Boolean(required=True)
    provider = fields.Str(required=True, validate=validate.OneOf(["stripe", "paypal"]))
    provider_ref = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    processed_at = fields.DateTime(dump_only=True)