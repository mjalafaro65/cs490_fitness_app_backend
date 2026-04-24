from datetime import datetime
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos, Roles, CoachDocuments, DailySurvey, WorkoutPlanAssignments, MealPlanAssignments, MealPlans, MealLogs
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from models.meal_logs import MealLogs
from schemas.nutrition_schema import NutritionLogSchema , CreateMealplanSchema, CreateMealLogSchema

nutrition_bp = Blueprint('Nutrition', __name__, url_prefix="/nutrition", description='Nutrition features')

@nutrition_bp.route('/nutrition-logs')
class NutritionLogs(MethodView):
    @jwt_required()
    @nutrition_bp.arguments(NutritionLogSchema)
    @nutrition_bp.response(201, NutritionLogSchema)
    def post(self, nutrition_data):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        meal_log = MealLogs(
            user_id=user.user_id,
            meal_id=nutrition_data.get('meal_id'),
            servings=nutrition_data['servings'],
            notes=nutrition_data.get('notes'),
            logged_at=datetime.utcnow()
        )
        
        db.session.add(meal_log)
        db.session.commit()
        
        return meal_log

@nutrition_bp.route('/mealplans')
class MealPlanList(MethodView):
    @jwt_required()
    @nutrition_bp.arguments(CreateMealplanSchema)
    @nutrition_bp.response(201, CreateMealplanSchema)
    def post(self, data):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        meal_plan = MealPlans(
            owner_user_id=user.user_id,
            name=data['name'],
            description=data.get('description'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            db.session.add(meal_plan)
            db.session.commit()
            return meal_plan
        except Exception:
            db.session.rollback()
            abort(500, description="Could not create meal plan.")

@nutrition_bp.route('/meal-logs')
class CreateMealLog(MethodView):
    @jwt_required()
    @nutrition_bp.arguments(CreateMealLogSchema)
    @nutrition_bp.response(201, CreateMealLogSchema)
    def post(self, data):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        meal_log = MealLogs(
            user_id=user.user_id,
            meal_id=data['meal_id'],
            servings=data['servings'],
            notes=data.get('notes'),
            logged_at=datetime.utcnow()
        )
        
        try:
            db.session.add(meal_log)
            db.session.commit()
            return meal_log
        except Exception:
            db.session.rollback()
            abort(500, description="Could not create meal log.")