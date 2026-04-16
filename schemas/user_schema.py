from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Users

class UserInfoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        load_instance = True
        

    
class UserUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        fields = ("first_name", "last_name", "phone_number")