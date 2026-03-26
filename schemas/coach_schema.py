# schemas/coach_schema.py
from marshmallow import Schema, fields, validate

class CoachProfileSchema(Schema):
    coach_profile_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    
    specialty_id = fields.Int(required=True)
    years_experience = fields.Int(required=True, validate=validate.Range(min=0))
    
    # Optional professional details
    bio = fields.Str(validate=validate.Length(max=1000), allow_none=True)
    profile_photo = fields.Str(validate=validate.Length(max=500), allow_none=True)
    
    # System managed fields (read-only for coach)
    status = fields.Str(dump_only=True) 
    is_flagged = fields.Bool(dump_only=True)
    approved_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)