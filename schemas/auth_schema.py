from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda p: len(p) >= 6)

class UserSetupSchema(Schema):
    # shared info
    first_name = fields.Str(validate=validate.Length(min=1), required=True)
    last_name = fields.Str(validate=validate.Length(min=1), required=True)
    phone_number = fields.Str(required=False, allow_none=True)
    profile_photo = fields.Str(required=False, allow_none=True, validate=validate.Length(max=255))
    bio = fields.Str(required=False, allow_none=True)

    # client specific info
    date_of_birth = fields.Date(required=False, allow_none=True)
    gender = fields.Str(
        required=False, 
        allow_none=True,
        validate=validate.OneOf(['male', 'female', 'other','prefer_not_to_say'])
    )
    height = fields.Float(required=False, allow_none=True)
    weight = fields.Float(required=False, allow_none=True)

    # read-only output
    user_id = fields.Int(dump_only=True)