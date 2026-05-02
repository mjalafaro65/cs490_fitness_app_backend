from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import MealLogs
from db import db

class NutritionLogSchema(Schema):
    meal_log_id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    meal_id = fields.Int()
    logged_at = fields.DateTime(dump_only=True)
    servings = fields.Decimal(as_string=True, required=True, validate=validate.Range(min=0.01))
    notes = fields.Str()

class CreateMealplanSchema(Schema):
    meal_plan_id = fields.Int(dump_only=True)
    owner_user_id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class CreateMealLogSchema(Schema):
    meal_log_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    meal_id = fields.Int(required=True)
    calories=fields.Int(required=False)
    logged_at = fields.DateTime(dump_only=True)
    servings = fields.Decimal(as_string=True, required=True, validate=validate.Range(min=0.01))
    notes = fields.Str()

class MealFilterArgsSchema(Schema):
    meal_type = fields.Str()
    min_calories = fields.Int()
    max_calories = fields.Int()
    min_protein = fields.Decimal(as_string=True)
    min_carbs = fields.Decimal(as_string=True)
    max_fats = fields.Decimal(as_string=True)

class FetchMealsSchema(Schema):
    meal_id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    meal_type = fields.Str(dump_only=True)
    calories = fields.Int(dump_only=True)
    protein_g = fields.Decimal(as_string=True, dump_only=True)
    carbs_g = fields.Decimal(as_string=True, dump_only=True)
    fats_g = fields.Decimal(as_string=True, dump_only=True)
    description = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)