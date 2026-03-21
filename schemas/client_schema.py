from marshmallow import Schema, fields

class DailySurveySchema(Schema):
    #general daily survey
    daily_goal = fields.Str(allow_none=True)
    energy_level = fields.Int(allow_none=True)
    target_focus = fields.Str(allow_none=True)
    
    # Wellness fields
    water_oz = fields.Float(allow_none=True)
    sleep_hours = fields.Float(allow_none=True)
    mood_score = fields.Int(allow_none=True)