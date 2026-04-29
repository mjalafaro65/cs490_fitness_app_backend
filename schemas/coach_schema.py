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
from models.payment_plans import BillTypeEnum

#done automatically using model

class UserBasicSchema(Schema):
    user_id = fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()

class CoachProfileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CoachProfiles
        load_instance = True
        include_fk = True
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
    
    specialty_id = fields.Int(required=True, load_only=True)
    
    specialty_name = fields.String(attribute="specialty.name", dump_only=True)
    
    user = fields.Nested("UserBasicSchema", allow_none=True)

    


class CoachProfileQuerySchema(Schema):
    user_id = fields.Int()
    coach_profile_id = fields.Int(required=False)

class CoachDocumentSchema(Schema):
    document_type = fields.Str(required=True, validate=validate.OneOf(['Certification', 'Identification', 'License ', 'Other']))
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
    user_id=fields.Int(dump_only=True)
    specialty_name = fields.Str(dump_only=True)
    years_experience = fields.Int(dump_only=True)
    is_favorited = fields.Bool(dump_only=True)
    profile_photo = fields.Str(validate=validate.Length(max=500), allow_none=True)
    bio = fields.Str(dump_only=True)


class CoachBrowsingQuery(Schema):
    specialty_id = fields.Int(required=False)
    min_price = fields.Float(required=False)
    max_price = fields.Float(required=False)


# Dashboard Schemas
class ClientBasicInfoSchema(Schema):
    user_id = fields.Int(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    relationship_start_date = fields.DateTime(dump_only=True)
    relationship_status = fields.Str(dump_only=True)


class ProgressSummarySchema(Schema):
    avg_energy_level = fields.Float(dump_only=True)
    avg_mood_score = fields.Float(dump_only=True)
    avg_sleep_hours = fields.Float(dump_only=True)
    workout_completion_rate = fields.Float(dump_only=True)
    nutrition_logging_rate = fields.Float(dump_only=True)
    active_goals_count = fields.Int(dump_only=True)
    completed_goals_count = fields.Int(dump_only=True)
    total_workouts_completed = fields.Int(dump_only=True)
    days_tracked = fields.Int(dump_only=True)


class RecentActivitySchema(Schema):
    date = fields.Date(dump_only=True)
    activity_type = fields.Str(dump_only=True)  # 'workout', 'meal', 'survey', 'goal'
    description = fields.Str(dump_only=True)
    details = fields.Dict(dump_only=True)


class GoalStatusSchema(Schema):
    goal_id = fields.Int(dump_only=True)
    description = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    progress_percentage = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    target_date = fields.DateTime(dump_only=True, allow_none=True)


class ClientDashboardSchema(Schema):
    client_info = fields.Nested(ClientBasicInfoSchema)
    progress_summary = fields.Nested(ProgressSummarySchema)
    recent_activity = fields.List(fields.Nested(RecentActivitySchema))
    goals_status = fields.List(fields.Nested(GoalStatusSchema))


class ClientListSchema(Schema):
    clients = fields.List(fields.Nested(ClientDashboardSchema))
    day_of_week = fields.Int(required=False)



class PaymentPlanSchema(Schema):
    payment_plan_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(required=True)
    name = fields.Str(required=True)
    billing_type = fields.Str(validate=validate.OneOf(['recurring', 'onetime']), required=True)
    billing_type = fields.Function(lambda obj: obj.billing_type.value)
    amount = fields.Decimal(as_string=True, required=True)
    is_active = fields.Bool(dump_only=True)
    is_custom = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)




# Dashboard Schemas
class ClientBasicInfoSchema(Schema):
    user_id = fields.Int(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    relationship_start_date = fields.DateTime(dump_only=True)
    relationship_status = fields.Str(dump_only=True)


class ProgressSummarySchema(Schema):
    avg_energy_level = fields.Float(dump_only=True)
    avg_mood_score = fields.Float(dump_only=True)
    avg_sleep_hours = fields.Float(dump_only=True)
    workout_completion_rate = fields.Float(dump_only=True)
    nutrition_logging_rate = fields.Float(dump_only=True)
    active_goals_count = fields.Int(dump_only=True)
    completed_goals_count = fields.Int(dump_only=True)
    total_workouts_completed = fields.Int(dump_only=True)
    days_tracked = fields.Int(dump_only=True)


class RecentActivitySchema(Schema):
    date = fields.Date(dump_only=True)
    activity_type = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    details = fields.Dict(dump_only=True)


class GoalStatusSchema(Schema):
    goal_id = fields.Int(dump_only=True)
    description = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    progress_percentage = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    target_date = fields.DateTime(dump_only=True, allow_none=True)


class ClientDashboardSchema(Schema):
    client_info = fields.Nested(ClientBasicInfoSchema)
    progress_summary = fields.Nested(ProgressSummarySchema)
    recent_activity = fields.List(fields.Nested(RecentActivitySchema))
    goals_status = fields.List(fields.Nested(GoalStatusSchema))


class ClientListSchema(Schema):
    clients = fields.List(fields.Nested(ClientDashboardSchema))


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


class WeeklyWorkoutDaySchema(Schema):
    weekday = fields.Int(required=True, validate=validate.Range(min=1, max=7))
    session_time = fields.Time(required=False, allow_none=True)
    exercises = fields.List(fields.Dict(), required=True)
    notes = fields.Str(required=False, allow_none=True)


class ClientWorkoutPlanCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(max=120))
    description = fields.Str(required=False, allow_none=True)
    weekly_schedule = fields.List(fields.Nested(WeeklyWorkoutDaySchema), required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=False, allow_none=True)
    repeat_rule = fields.Str(validate=validate.OneOf(['none', 'weekly', 'biweekly']), required=False)
    intensity_notes = fields.Str(required=False, allow_none=True)


class ClientWorkoutPlanSchema(Schema):
    plan_id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    owner_user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    weekly_schedule = fields.List(fields.Nested(WeeklyWorkoutDaySchema), dump_only=True)
    assignment_id = fields.Int(dump_only=True)
    assigned_to_client_id = fields.Int(dump_only=True)
    assigned_by_coach_id = fields.Int(dump_only=True)
    start_date = fields.Date(dump_only=True)
    end_date = fields.Date(dump_only=True, allow_none=True)
    repeat_rule = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)


class ClientWorkoutAssignmentsSchema(Schema):
    assignments = fields.List(fields.Nested(ClientWorkoutPlanSchema), dump_only=True)
    total_active = fields.Int(dump_only=True)
    total_completed = fields.Int(dump_only=True)
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

class ManageClientSchema(Schema):
    relationship_id = fields.Int(required=True)
    status = fields.String(required=True, validate=validate.OneOf(["active", "inactive", "terminated"]))

class FavoriteCoachSchema(Schema):
    favorite_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)


class CoachAvailabilitySchema(Schema):
    availability_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(dump_only=True)

    day_of_week = fields.Int(required=True)
    start_time = fields.Str(required=True)
    end_time = fields.Str(required=True)

class PaymentPlanSchema(Schema):
    payment_plan_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(dump_only=True)

    name = fields.Str(required=True)

    billing_type = fields.Method(
        serialize="get_billing_type",
        deserialize="load_billing_type"
    )

    amount = fields.Decimal(as_string=True, required=True)

    is_active = fields.Bool()
    is_custom = fields.Bool()

    created_at = fields.DateTime(dump_only=True)

    # ---------- ENUM HANDLING ----------
    def get_billing_type(self, obj):
        # returns "onetime" or "recurring"
        return obj.billing_type.value if obj.billing_type else None

    def load_billing_type(self, value):
        try:
            return BillTypeEnum(value)
        except ValueError:
            raise ValueError("billing_type must be 'onetime' or 'recurring'")
