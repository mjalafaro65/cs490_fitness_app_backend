from flask import abort, request
from flask.views import MethodView
from flask_smorest import Blueprint
from models import Users
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema, ProfileSchema 
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select

from models.daily_survey import DailySurvey
from models import ClientProfiles

client_blp = Blueprint("ClientOperations", __name__, url_prefix="/client", description="Client Operations")
@client_blp.route("/daily-survey")
class DailySurveyView(MethodView):
    @jwt_required()
    @client_blp.arguments(DailySurveySchema)
    @client_blp.response(200,DailySurveySchema)
    def post(self, data):
        """
        Input or update daily surveys: initial and wellness

        *no need to pass client id in url, it will be obtained from jwt
        """
        today=date.today()

        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            return {"msg":"user not found"},404
        
        current_user_id=user.user_id
        #make stmt
        #current_user is logged in uses from login_required
        stmt=select(DailySurvey).filter_by(user_id=current_user_id , date=today)

        #execute 
        entry=db.session.execute(stmt).scalar_one_or_none()

        if not entry:   
            #create new
            entry= DailySurvey(user_id=current_user_id , date=today, **data)
            db.session.add(entry)
        else:
            #update 
            for key, value in data.items():
                if value is not None:
                    setattr(entry, key, value)

        db.session.commit()
        return entry
    
    @jwt_required()
    def get(self):
        """
        Check if the user has already submitted a survey today.
        """
        today = date.today()
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        if not user:
            return {"msg": "User not found"}, 404

        # Check for an existing entry for today
        stmt = select(DailySurvey).filter_by(user_id=user.user_id, date=today)
        entry = db.session.execute(stmt).scalar_one_or_none()

        if entry:
            # You can return the data or just a simple boolean
            return {
                "completed": True, 
                "date": today.isoformat(),
                "survey_id": entry.survey_id
            }, 200
        
        return {"completed": False}, 200

@client_blp.route("/profile")
class ClientProfileView(MethodView):
    @jwt_required()
    @client_blp.response(200, ProfileSchema)
    def get(self):
        """Retrieve the authenticated client's profile details."""
        current_auth_id = get_jwt_identity()
        
        # find user record linked to Auth ID
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        if not user:
            return {"msg":"User record not found."}, 404

        # use user.user_id to find the profile
        profile = ClientProfiles.query.filter_by(client_id=user.user_id).first()
        
        if not profile:
            return {"msg":"Profile not found. Please complete setup."}, 404
            
        return profile

    @jwt_required()
    @client_blp.arguments(ProfileSchema)
    @client_blp.response(200, ProfileSchema)
    def put(self, data):
        """Update the authenticated client's metrics and bio."""
        current_auth_id = get_jwt_identity()
        
        from models import Users
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        if not user:
            abort(404, description="User record not found.")
        
        profile = ClientProfiles.query.filter_by(client_id=user.user_id).first()
        
        if not profile:
            abort(400, description="Profile not found. Use /auth/setup to create your profile.")

        for key, value in data.items():
            setattr(profile, key, value)

        try:
            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error: {str(e)}")