from flask import abort
from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select

from models.daily_survey import DailySurvey


#for connecting to app
client_blp=Blueprint("ClientOperations", __name__, url_prefix="/client", description="Client Operations")

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

        # changed to current_user.user_id when login feature is updated
        current_user_id = get_jwt_identity()
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