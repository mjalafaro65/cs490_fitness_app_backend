from marshmallow import Schema, fields, validate
from models.invoices import StatusEnumList, Invoices
from models.refund_disputes import StatusEnum_Disputes, RefundDisputes

class CreateInvoiceSchema(Schema):
    invoice_id = fields.Int(dump_only=True)
    relationship_id = fields.Int(dump_only=True)
    client_user_id = fields.Int(required=True)
    subtotal = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    currency = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True) 
    pay_date = fields.DateTime(required=False, allow_none=True) 
    issued_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class CreateDisputeSchema(Schema):
    reason = fields.Str(required=True, validate=validate.Length(min=5, max=255))
    audit_id = fields.Int(required=False) 
    refund_dispute_id = fields.Int(dump_only=True)
    payment_id = fields.Int(dump_only=True)
    opened_by_user_id = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    resolved_at = fields.DateTime(dump_only=True)
    resolved_by_id = fields.Int(dump_only=True)
    resolution_notes = fields.Str(dump_only=True)


class UpdateInvoiceStatusSchema(Schema):
    invoice_id = fields.Int(required=True)
    new_status = fields.Enum(StatusEnumList, by_value=True, required=True)

class PayInvoiceSchema(Schema):
    invoice_id = fields.Int(required=True)
    last4 = fields.Str(required=False, allow_none=True, load_default=None)

class ResolveDisputeSchema(Schema):
    dispute_id = fields.Int(required=True)
    status = fields.Enum(StatusEnum_Disputes, by_value=True, required=True)
    notes = fields.Str(required=True)

class InitiateFireSchema(Schema):
    relationship_id = fields.Int(required=True)

class ConfirmTerminationSchema(Schema):
    relationship_id = fields.Int(required=True)
    reason = fields.Str(required=False, allow_none=True)