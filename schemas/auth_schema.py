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
        validate=validate.OneOf(['male', 'female'])
    )
    height = fields.Float(required=False, allow_none=True)
    weight = fields.Float(required=False, allow_none=True)

    # coach specific
    specialty_id = fields.Int(required=False, allow_none=True)
    years_experience = fields.Int(required=False, allow_none=True, validate=validate.Range(min=0))
    
    # read-only output
    coach_profile_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    approval_status = fields.Str(dump_only=True)