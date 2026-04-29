from marshmallow import Schema, fields, validate, pre_load
from models import Exercises,WorkoutPlanDayExercises, WorkoutPlans, CalendarWorkouts, WorkoutPlanDays
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema



class ExerciseCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    muscle_group = fields.Str(required=True, validate=validate.Length(max=60))
    equipment = fields.Str(required=True, validate=validate.Length(max=60))
    training_type = fields.Str(required=True, validate=validate.Length(max=60))
    description = fields.Str(required=False, allow_none=True)
    is_public = fields.Bool(load_default=False)


class ExerciseUpdateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120))
    muscle_group = fields.Str(required=False, validate=validate.Length(max=60))
    equipment = fields.Str(required=False, validate=validate.Length(max=60))
    training_type = fields.Str(required=False, validate=validate.Length(max=60))
    description = fields.Str(required=False, allow_none=True)
    is_public = fields.Bool(required=False)


class ExerciseListQuerySchema(Schema):
    q = fields.Str(required=False)
    muscle_group = fields.Str(required=False)
    equipment = fields.Str(required=False)
    training_type = fields.Str(required=False)


class PlanCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    description = fields.Str(required=False, allow_none=True)
    is_public = fields.Bool(load_default=False)


class PlanUpdateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120))
    description = fields.Str(required=False, allow_none=True)
    is_public = fields.Bool(required=False)


class PlanDayCreateSchema(Schema):
    day_label = fields.Str(required=True, validate=validate.Length(min=1, max=60))
    sort_order = fields.Int(required=True)
    weekday = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=6),
    )
    session_time = fields.Time(required=False, allow_none=True)


class PlanDayUpdateSchema(Schema):
    day_label = fields.Str(required=False, validate=validate.Length(min=1, max=60))
    sort_order = fields.Int(required=False)
    weekday = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=6),
    )
    session_time = fields.Time(required=False, allow_none=True)


class DayExerciseCreateSchema(Schema):
    exercise_id = fields.Int(required=True)
    sets = fields.Int(required=True, validate=validate.Range(min=1))
    reps = fields.Int(required=True, validate=validate.Range(min=1))
    weight = fields.Decimal(required=False, allow_none=True, places=2)
    duration_minutes = fields.Int(required=False, allow_none=True)
    notes = fields.Str(required=False, allow_none=True)
    sort_order = fields.Int(required=True)

    @pre_load
    def map_duration(self, data, **kwargs):
        if isinstance(data, dict) and "duration_minutes" not in data and "duraction_minutes" in data:
            data = {**data, "duration_minutes": data.get("duraction_minutes")}
        return data


class DayExerciseUpdateSchema(Schema):
    sets = fields.Int(required=False, validate=validate.Range(min=1))
    reps = fields.Int(required=False, validate=validate.Range(min=1))
    weight = fields.Decimal(required=False, allow_none=True, places=2)
    duration_minutes = fields.Int(required=False, allow_none=True)
    notes = fields.Str(required=False, allow_none=True)
    sort_order = fields.Int(required=False)

    @pre_load
    def map_duration(self, data, **kwargs):
        if isinstance(data, dict) and "duration_minutes" not in data and "duraction_minutes" in data:
            data = {**data, "duration_minutes": data.get("duraction_minutes")}
        return data


class PlanCopySchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120))


class PlanBrowseQuerySchema(Schema):
    q = fields.Str(required=False)
    muscle_group = fields.Str(required=False)
    equipment = fields.Str(required=False)
    training_type = fields.Str(required=False)
    exercise_ids = fields.Str(
        required=False,
        metadata={"description": "Comma-separated exercise IDs, e.g. '1,2,3'"},
    )
    exercise_match = fields.Str(
        required=False,
        validate=validate.OneOf(["any", "all"]),
        load_default="any",
    )


class PlanAssignmentSchema(Schema):
    start_date = fields.DateTime(required=False, allow_none=True)
    end_date = fields.DateTime(required=False, allow_none=True)
    repeat_rule = fields.Str(
        required=False,
        validate=validate.OneOf(["none", "daily", "weekly", "monthly"]),
        load_default="weekly",
    )


class CalendarOccurrenceSchema(Schema):
    plan_day_id = fields.Int(required=True)
    scheduled_start = fields.DateTime(required=True)
    scheduled_end = fields.DateTime(required=True)


class PlanCalendarSchema(Schema):
    occurrences = fields.List(fields.Nested(CalendarOccurrenceSchema), required=True)
from marshmallow import Schema, fields, validate

class WorkoutLogEntrySchema(Schema):
    workout_log_entry_id= fields.Int(dump_only=True)
    calendar_workout_id = fields.Int(allow_none=True)
    plan_day_exercise_id = fields.Int(allow_none=True)
    exercise_id = fields.Int(required=True)

    sets = fields.Int(allow_none=True)
    reps = fields.Int(allow_none=True)
    weight = fields.Float(allow_none=True)
    rpe = fields.Float(allow_none=True)
    distance = fields.Float(allow_none=True)
    calories = fields.Float(allow_none=True)
    duration_minutes = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)

class WorkoutLogSchema(Schema):
    workout_log_id = fields.Int(dump_only=True)
    user_id =fields.Int(allow_none=True)
    calendar_workout_id = fields.Int(allow_none=True)
    logged_at = fields.DateTime(dump_only=True)
    notes = fields.Str()

    entries = fields.List(fields.Nested(WorkoutLogEntrySchema))


    
class WorkoutLogQuerySchema(Schema):
    client_id = fields.Int(allow_none=True)
    calendar_workout_id = fields.Int(required=False)



class CalendarWorkoutQuerySchema(Schema):
    date = fields.Date(required=False)
    view = fields.Str(required=False) 


class ExerciseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Exercises
        load_instance = True
        
class PlanDayExerciseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WorkoutPlanDayExercises
        load_instance = True

    exercise = fields.Nested(ExerciseSchema)





class PlanSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WorkoutPlans
        load_instance = True

class PlanDaySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WorkoutPlanDays
        load_instance = True

    exercises = fields.Nested(PlanDayExerciseSchema, many=True)
    plan = fields.Nested(PlanSchema)

class CalendarViewSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CalendarWorkouts
        load_instance = True

    plan_day = fields.Nested(PlanDaySchema)
    
class CalendarWorkoutQuerySchemaWeek(Schema):
    view = fields.String(required=False)