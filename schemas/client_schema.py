from marshmallow import Schema, fields

class DailySurveySchema(Schema):
    #general daily survey
    daily_goal = fields.Str(required=False,allow_none=True)
    energy_level = fields.Int(required=False,allow_none=True)
    target_focus = fields.Str(required=False,allow_none=True)
    
    # Wellness fields
    water_oz = fields.Float(required=False,allow_none=True)
    weight_lbs=fields.Float(required=False,allow_none=True)
    sleep_hours = fields.Float(required=False,allow_none=True)
    mood_score = fields.Int(required=False,allow_none=True)
    

    