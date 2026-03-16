from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class MealSlotEnum(db.Enum):
    breakfast = 'breakfast'
    brunch = 'brunch'
    branch = 'branch'
    lunch = 'lunch'
    dinner = 'dinner'
    snack = 'snack'
    other = 'other'

class MealPlanItems(db.Model):
    __tablename__ = 'meal_plan_items'
    
    meal_plan_item_id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('meal_plans.meal_plan_id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.meal_id'), nullable=False)
    ### Database says do it by int?
    day_index = db.Column(db.Integer, nullable=False)  
    meal_slot = db.Column(MealSlotEnum, nullable=False)
    servings = db.Column(db.Numeric(6, 2), nullable=False)
    notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False)