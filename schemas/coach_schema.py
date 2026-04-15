# schemas/coach_schema.py

###for other coach profile feat in case main dont work 
# class CoachProfileSchema(Schema):
#     coach_profile_id = fields.Int(dump_only=True)
#     user_id = fields.Int(dump_only=True)
    
#     specialty_id = fields.Int(required=True)
#     years_experience = fields.Int(required=True, validate=validate.Range(min=0))
    
#     # Optional professional details
#     bio = fields.Str(validate=validate.Length(max=1000), allow_none=True)
#     profile_photo = fields.Str(validate=validate.Length(max=500), allow_none=True)
    
#     # System managed fields (read-only for coach)
#     status = fields.Str(dump_only=True) 
#     is_flagged = fields.Bool(dump_only=True)
#     approved_at = fields.DateTime(dump_only=True)
#     created_at = fields.DateTime(dump_only=True)
#     updated_at = fields.DateTime(dump_only=True)

from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import CoachProfiles, CoachDocuments
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

class CoachDocumentSchema(Schema):
    document_type = fields.Str(required=True, validate=validate.OneOf(['Certification', 'ID', 'Other']))
    document_url = fields.Str(required=True)
    
    # These are for the Database/Response only
    document_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(dump_only=True)

    class Meta:
        model = CoachDocuments
        load_instance = True
        sqla_session = db.session
        include_fk = True
        

class SpecialtySchema(Schema):
    specialty_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class CoachBrowsingSchema(Schema):
    coach_profile_id = fields.Int(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    specialty_name = fields.Str(dump_only=True)
    years_experience = fields.Int(dump_only=True)
    bio = fields.Str(dump_only=True)



#class CoachFiltering(Schema):
#    pass

class AssignWorkoutPlanSchema(Schema):
    plan_id = fields.Int(required=True)
    assigned_to_client_id = fields.Int(required=True)
    assigned_by_coach_id = fields.Int(dump_only=True)  
    assignment_date = fields.Date(dump_only=True)
    start_date = fields.Date()
    end_date = fields.Date()
    repeat_rules = fields.Str(validate=validate.OneOf(['none', 'daily', 'weekly', 'monthly']), required=True)
    status = fields.Str(validate=validate.OneOf(['active', 'completed', 'cancelled']), required=True)
    created_at = fields.DateTime(dump_only=True)

class AssignMealPlanSchema(Schema):
    meal_plan_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    assigned_by_user_id = fields.Int(dump_only=True)  
    start_date = fields.Date()
    end_date = fields.Date()
    repeat_rule = fields.Str(validate=validate.OneOf(['none', 'daily', 'weekly', 'biweekly', 'monthly']), required=True)
    status = fields.Str(validate=validate.OneOf(['active', 'completed', 'canceled']), required=True)
    created_at = fields.DateTime(dump_only=True)
