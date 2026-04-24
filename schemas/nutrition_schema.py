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
    logged_at = fields.DateTime(dump_only=True)
    servings = fields.Decimal(as_string=True, required=True, validate=validate.Range(min=0.01))
    notes = fields.Str()