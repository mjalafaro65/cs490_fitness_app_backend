from flask import abort, request
from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema, ProfileSchema 
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select

from models.daily_survey import DailySurvey
from models import ClientProfiles

client_blp = Blueprint("ClientOperations", __name__, url_prefix="/client", description="Client Operations")

@client_blp.route("/profile")
class ClientProfileView(MethodView):
    @jwt_required()
    @client_blp.response(200, ProfileSchema)
    def get(self):
        """Retrieve the authenticated client's profile details."""
        current_user_id = get_jwt_identity()
        profile = ClientProfiles.query.filter_by(client_id=current_user_id).first()
        
        if not profile:
            abort(404, message="Profile not found.")
            
        return profile

    @jwt_required()
    @client_blp.arguments(ProfileSchema) # Automatically validates input
    @client_blp.response(200, ProfileSchema)
    def put(self, data):
        """Update the authenticated client's physical metrics and bio."""
        current_user_id = get_jwt_identity()
        
        profile = ClientProfiles.query.filter_by(client_id=current_user_id).first()
        
        if not profile:
            profile = ClientProfiles(client_id=current_user_id)
            db.session.add(profile)

        for key, value in data.items():
            setattr(profile, key, value)

        try:
            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Database error: {str(e)}")