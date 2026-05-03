from datetime import datetime
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos, Roles, CoachDocuments, DailySurvey, WorkoutPlanAssignments, MealPlanAssignments, MealPlans, MealLogs, CoachClientRelationships
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from models.meal_logs import MealLogs
from schemas.nutrition_schema import NutritionLogSchema , CreateMealplanSchema, CreateMealLogSchema, FetchMealsSchema, MealFilterArgsSchema
from models.meals import Meals

nutrition_bp = Blueprint('Nutrition', __name__, url_prefix="/nutrition", description='Nutrition features')



@nutrition_bp.route('/mealplans')
class MealPlanList(MethodView):
    @jwt_required()
    
    @nutrition_bp.response(200, CreateMealplanSchema(many=True))
    def get(self):
        """
        Get all meal plans for the current user
        """
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        meal_plans = MealPlans.query.filter_by(owner_user_id=user.user_id).all()
        return meal_plans
   
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
        """
        use can log meal
        """
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        meal_log = MealLogs(
            user_id=user.user_id,
            meal_id=data['meal_id'],
            servings=data['servings'],
            calories=data['calories'],  
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
            
    @jwt_required()
    @nutrition_bp.response(201, CreateMealLogSchema(many=True))

    def get(self):
        """
        User can get all their meal log
        """
        
        auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=auth_id).first_or_404()

        logs = MealLogs.query.filter_by(user_id=user.user_id).all()

        return logs, 200

    
@nutrition_bp.route('/meal-logs/<int:log_id>')
class MealLogUpdate(MethodView):
    @jwt_required()
    @nutrition_bp.response(201, CreateMealLogSchema)

    def get(self, log_id):
        """
        Get one meal log 
        
        """
        
        auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=auth_id).first_or_404()

        log = MealLogs.query.get_or_404(log_id)

        if log.user_id != user.user_id:
            abort(403, description="Not allowed")

        return log, 200
    
    @jwt_required()
    @nutrition_bp.response(201, CreateMealLogSchema)
    def put(self, log_id):
        """
        Update one meal log
        
        """
        auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=auth_id).first_or_404()

        log = MealLogs.query.get_or_404(log_id)

        if log.user_id != user.user_id:
            abort(403, description="Not allowed")

        data = request.get_json()

        log.servings = data.get('servings', log.servings)
        log.calories = data.get('calories', log.calories)
        log.notes = data.get('notes', log.notes)

        db.session.commit()

        return {"message": "Updated"}, 200
    
    @jwt_required()
    
    def delete(self, log_id):
        auth_id = get_jwt_identity()
        """
        Delete one meal log
        """
        user = Users.query.filter_by(auth_id=auth_id).first_or_404()

        log = MealLogs.query.get_or_404(log_id)

        if log.user_id != user.user_id:
            abort(403, description="Not allowed")

        try:
            db.session.delete(log)
            db.session.commit()
            return {"message": "Meal log deleted"}, 200
        except Exception:
            db.session.rollback()
            abort(500, description="Could not delete meal log.")
    
@nutrition_bp.route('/coach/meal-logs')
class CoachAllClientLogs(MethodView):
    @jwt_required()
    @nutrition_bp.response(201, CreateMealLogSchema(many=True))

    def get(self):
        """
        filter logs by client and date , default=every log 
        """
        
        auth_id = get_jwt_identity()
        coach = Users.query.filter_by(auth_id=auth_id).first_or_404()

        coach_profile = CoachProfiles.query.filter_by(user_id=coach.user_id).first_or_404()

        # all client IDs for this coach
        client_ids = db.session.execute(
            select(CoachClientRelationships.client_user_id).where(
                CoachClientRelationships.coach_profile_id == coach_profile.coach_profile_id
            )
        ).scalars().all()

        if not client_ids:
            return [], 200

        #query params
        client_id = request.args.get("client_id", type=int)
        date = request.args.get("date")
        limit = request.args.get("limit", 20, type=int)

        query = MealLogs.query

        # filter by coach's clients ONLY
        query = query.filter(MealLogs.user_id.in_(client_ids))

        # filter by specific client
        if client_id:
            if client_id not in client_ids:
                abort(403, description="Not your client")
            query = query.filter(MealLogs.user_id == client_id)

        # filter by date
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
                query = query.filter(func.date(MealLogs.logged_at) == parsed_date)
            except ValueError:
                abort(400, description="Invalid date format")

        logs = (
            query
            .order_by(MealLogs.logged_at.desc())
            .limit(limit)
            .all()
        )

        return logs, 200
    
### Fetchs all meals
### Filters by type, calories, carbs, protein, fats
@nutrition_bp.route('/fetch-meals')
class FetchMeals(MethodView):
    @nutrition_bp.arguments(MealFilterArgsSchema, location="query")
    @nutrition_bp.response(200, FetchMealsSchema(many=True))
    def get(self, args):
        query = Meals.query.filter_by(is_active=True)

        if "meal_type" in args:
            query = query.filter(Meals.meal_type == args["meal_type"])

        if "min_calories" in args:
            query = query.filter(Meals.calories >= args["min_calories"])

        if "max_calories" in args:
            query = query.filter(Meals.calories <= args["max_calories"])

        if "min_protein" in args:
            query = query.filter(Meals.protein_g >= args["min_protein"])

        if "min_carbs" in args:
            query = query.filter(Meals.carbs_g >= args["min_carbs"])

        if "max_fats" in args:
            query = query.filter(Meals.fats_g <= args["max_fats"])

        return query.order_by(Meals.created_at.desc()).all()
