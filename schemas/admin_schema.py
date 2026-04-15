from marshmallow import Schema, fields, validate

class AdminDocumentReviewSchema(Schema):
    # The Admin only sends these two things
    status = fields.Str(required=True, validate=validate.OneOf(['pending', 'approved', 'rejected']))
    notes = fields.Str(required=False)

class AdminCheckReviewsSchema(Schema):
    review_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(dump_only=True)
    client_user_id = fields.Int(dump_only=True)
    rating = fields.Int(dump_only=True)
    comment = fields.Str(dump_only=True)
    is_flagged = fields.Bool()
    is_visible = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class AdminPurgeUserSchema(Schema):
    user_id = fields.Int(required=True)