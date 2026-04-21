from datetime import datetime
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos, Roles, CoachDocuments, DailySurvey, WorkoutPlanAssignments, MealPlanAssignments
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from models.meal_logs import MealLogs
from schemas.nutrition_schema import NutritionLogSchema

nutrition_bp = Blueprint('Nutrition', __name__, url_prefix="/nutrition", description='Nutrition features')

@nutrition_bp.route('/nutrition-logs')
class NutritionLogs(MethodView):
    #@jwt_required()
    @nutrition_bp.arguments(NutritionLogSchema)
    @nutrition_bp.response(201, NutritionLogSchema)
    def post(self, nutrition_data):
        #user_id = get_jwt_identity()
        #user = Users.query.filter_by(auth_id=user_id).first()
        user = Users.query.get(1)
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