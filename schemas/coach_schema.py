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
        
    exclude = ("approved_at", "approved_by_admin_user_id", "is_flagged")

class CoachProfilePostSchema(Schema):
    user_id = fields.Int(load_only=True)

class CoachDocumentUploadSchema(Schema):
    document_type = fields.Str(required=True, validate=validate.OneOf(['Certification', 'ID', 'Insurance']))
    document_url = fields.Str(required=True)