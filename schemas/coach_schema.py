from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import CoachProfiles
from db import db

#done automatically using model
class CoachProfileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CoachProfiles
        load_instance = True
        include_fk = True
        sqla_session = db.session
        name = "CoachProfileData"

    user_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(dump_only=True)
    is_flagged = fields.Bool(dump_only=True)
    approved_by_admin_user_id = fields.Int(dump_only=True)
    flagged_by_admin_user_id = fields.Int(dump_only=True)
    approved_at = fields.DateTime(dump_only=True)
    flagged_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class CoachProfileQuerySchema(Schema):
    user_id = fields.Int()

class CoachDocumentUploadSchema(Schema):
    document_type = fields.Str(required=True, validate=validate.OneOf(['Certification', 'ID', 'Insurance']))
    document_url = fields.Str(required=True)