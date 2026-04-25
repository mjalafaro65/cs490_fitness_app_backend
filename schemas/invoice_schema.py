from marshmallow import Schema, fields, validate
# Import the actual enum class from your models file
from models.invoices import StatusEnumList 

class CreateInvoiceSchema(Schema):
    relationship_id = fields.Int(required=True)
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    pay_date = fields.DateTime(required=False, allow_none=True) 

class UpdateInvoiceStatusSchema(Schema):
    invoice_id = fields.Int(required=True)
    # Use the imported StatusEnumList here
    new_status = fields.Enum(StatusEnumList, by_value=True, required=True)