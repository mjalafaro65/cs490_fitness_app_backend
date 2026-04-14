from marshmallow import Schema, fields, validate

class WorkoutLogSchema(Schema):
    exercise_id = fields.Int(required=True)
    plan_day_exercise_id = fields.Int(dump_only=True)
    sets = fields.Int(validate=validate.Range(min=0))
    reps = fields.Int(validate=validate.Range(min=0))
    weight = fields.Float(validate=validate.Range(min=0))
    rpe = fields.Int(validate=validate.Range(min=0))
    distance = fields.Float(validate=validate.Range(min=0))
    calories = fields.Float(validate=validate.Range(min=0))
    duration_minutes = fields.Float(validate=validate.Range(min=0))
    notes = fields.Str(validate=validate.Length(max=1000))

