from marshmallow import Schema, fields, validate

class AdminDocumentReviewSchema(Schema):
    # The Admin only sends these two things
    status = fields.Str(required=True, validate=validate.OneOf(['pending', 'approved', 'rejected']))
    notes = fields.Str(required=False)