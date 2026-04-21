from marshmallow import Schema, fields, validate

class DailySurveySchema(Schema):
    survey_id = fields.Int(dump_only=True)
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

    gender = fields.Method(
        serialize="get_gender",
        validate=validate.OneOf(['male', 'female', 'other', 'prefer_not_to_say']),
        required=False,
        allow_none=True
    )
    def get_gender(self, obj):
        return obj.gender.value if obj.gender else None
    
    bio = fields.Str(validate=validate.Length(max=500))
    profile_photo=fields.Str(required=False)
    height = fields.Float(validate=validate.Range(min=0))
    weight = fields.Float(validate=validate.Range(min=0))
    
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class HireRequestCreateSchema(Schema):
    coach_profile_id = fields.Int(required=True)
    payment_plan_id = fields.Int(required=True)
    auto_pay_enabled = fields.Bool(load_default=False)


class HireRequestStatusSchema(Schema):
    request_id = fields.Int()
    client_user_id = fields.Int()
    coach_profile_id = fields.Int()
    payment_plan_id = fields.Int(allow_none=True)
    status = fields.Str()
    auto_pay_enabled = fields.Bool()
    created_at = fields.DateTime()
    decided_at = fields.DateTime(allow_none=True)


class HireRequestListSchema(Schema):
    request_id = fields.Int()
    coach_profile_id = fields.Int()
    payment_plan_id = fields.Int(allow_none=True)
    status = fields.Str()
    auto_pay_enabled = fields.Bool()
    created_at = fields.DateTime()
    decided_at = fields.DateTime(allow_none=True)
class ReviewCoachSchema(Schema):
    ### For editing reviews
    review_id = fields.Int(dump_only=True)
    coach_profile_id = fields.Int(dump_only=True)
    ### For creating reviews
    rating = fields.Int(required=True, validate=validate.Range(min=1, max=100))
    comment = fields.Str(validate=validate.Length(max=1000))
    helpful_count = fields.Int(dump_only=True)
    unhelpful_count = fields.Int(dump_only=True)
    user_interaction = fields.Str(dump_only=True)

