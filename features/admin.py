from flask.views import MethodView
from flask_smorest import Blueprint,abort
from middleware import roles_required
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos
from models.coach_profiles import ApprovalStatusEnum
from db import db
from datetime import date
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.coach_schema import CoachProfileSchema

admin_blp=Blueprint("Admin", __name__, url_prefix="/admin", description="Admin features")

@admin_blp.route("/coach-applications")
class CoachApplications(MethodView):
    # @roles_required("admin")
    @admin_blp.response(200, CoachProfileSchema(many=True))
    def get(self):
        """
        Get pending coach applications
        """
        return CoachProfiles.query.filter_by(status=ApprovalStatusEnum.pending).all()
    

@admin_blp.route("/coach-applications/<int:coach_pf_id>")
class CoachApplications(MethodView):
    # @roles_required("admin")
    @admin_blp.response(200, CoachProfileSchema)
    def get(self,coach_pf_id):
        """
        Get pending coach application
        """

        return CoachProfiles.query.filter_by(status=ApprovalStatusEnum.pending,coach_profile_id=coach_pf_id).first_or_404()


