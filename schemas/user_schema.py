from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Users

class UserInfoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        load_instance = True
  
class UserQuerySchema(Schema):
    user_id = fields.Int()
    is_active = fields.Int()
    page = fields.Int(load_default=1)
    per_page = fields.Int(load_default=20)      

    
class UserUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        fields = ("first_name", "last_name", "phone_number")
        
class UserDeleteSchema(Schema):
    reason = fields.String(required=False, allow_none=True)
    detailed_reason = fields.String(required=False, allow_none=True)