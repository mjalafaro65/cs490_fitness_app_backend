from wsgiref import validate
from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda p: len(p) >= 6)

class UserSetupSchema(Schema):
    #set up user info
    first_name = fields.Str(validate=validate.Length(min=1),required=True)
    last_name = fields.Str(validate=validate.Length(min=1),required=True)
    phone_number = fields.Str(required=False, allow_none=True)

    #set up client pf info
    date_of_birth = fields.Date(required=True)
    gender = fields.Str(
        required=False, 
        allow_none=True,
        validate=validate.OneOf(['male', 'female', 'prefer_not_to_say', 'other'])
    )
    profile_photo = fields.Str(required=False, allow_none=True)
    bio = fields.Str(required=False, allow_none=True)
    height = fields.Float(required=False,allow_none=True,)
    weight = fields.Float(required=False,allow_none=True,)