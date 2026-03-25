from marshmallow import Schema, fields, validate

class DailySurveySchema(Schema):
    daily_goal = fields.Str(required=False, allow_none=True)
    energy_level = fields.Int(required=False, allow_none=True)
    target_focus = fields.Str(required=False, allow_none=True)
    
    water_oz = fields.Float(required=False, allow_none=True)
    weight_lbs = fields.Float(required=False, allow_none=True)
    sleep_hours = fields.Float(required=False, allow_none=True)
    mood_score = fields.Int(required=False, allow_none=True)

class ProfileSchema(Schema):
    client_profile_id = fields.Int(dump_only=True)
    client_id = fields.Int(dump_only=True)
    
    date_of_birth = fields.Date(format='%Y-%m-%d')

    gender = fields.Str(
        validate=validate.OneOf(["male", "female"]),
        required=False,
        allow_none=True
    )
    
    bio = fields.Str(validate=validate.Length(max=500))
    height = fields.Float(validate=validate.Range(min=0))
    weight = fields.Float(validate=validate.Range(min=0))
    
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)