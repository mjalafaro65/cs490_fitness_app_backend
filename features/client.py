from flask.views import MethodView
from flask_smorest import Blueprint
from models.daily_wellness import DailyWellness
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema

#for connecting to app
client_blp=Blueprint("Client", __name__, url_prefix="/client", description="Client Operations")

@client_blp.route("/daily-survey")
class DailySurvey(MethodView):
    @client_blp.response(201, DailySurveySchema)
    def post(self):
        