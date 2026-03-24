from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos
from db import db
from datetime import date
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.coach_schema import CoachProfileSchema

admin_blp=Blueprint("Admin", __name__, url_prefix="/admin", description="Admin features")

@admin_blp.route("/coach-applications")
class CoachApplications(MethodView):
    @admin_blp.arguments(CoachProfiles)
    def get(self):

        coach_pfs=CoachProfiles.query.filter_by(status="pending")

        return {"Coach Application":coach_pfs}, 200
    

@admin_blp.route("/coach-applications/<int:coach_pf_id>")
class CoachApplications(MethodView):
    @admin_blp.arguments(CoachProfiles)
    def get(self,coach_pf_id):

        coach_pfs=CoachProfiles.query.filter_by(status="pending",coach_profile_id=coach_pf_id)

        return {"Coach Application":coach_pfs}, 200 


