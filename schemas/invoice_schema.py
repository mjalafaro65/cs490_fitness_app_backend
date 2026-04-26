from marshmallow import Schema, fields, validate
# Import the actual enum class from your models file
from models.invoices import StatusEnumList 
from models.refund_disputes import StatusEnum_Disputes

class CreateInvoiceSchema(Schema):
    relationship_id = fields.Int(required=True)
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    pay_date = fields.DateTime(required=False, allow_none=True) 

class UpdateInvoiceStatusSchema(Schema):
    invoice_id = fields.Int(required=True)
    # Use the imported StatusEnumList here
    new_status = fields.Enum(StatusEnumList, by_value=True, required=True)

class PayInvoiceSchema(Schema):
    invoice_id = fields.Int(required=True)
    # Optional: if provided, we search for this specific card
    last4 = fields.Str(required=False, allow_none=True, load_default=None)

class CreateDisputeSchema(Schema):
    payment_id = fields.Int(required=True)
    # required=True: The key "reason" MUST be in the JSON
    # allow_none=True: The value can be null/None
    reason = fields.Str(required=True, allow_none=True)

class ResolveDisputeSchema(Schema):
    dispute_id = fields.Int(required=True)
    # This validates against your StatusEnum_Disputes values ('approved', 'rejected', etc.)
    status = fields.Enum(StatusEnum_Disputes, by_value=True, required=True)
    notes = fields.Str(required=True)