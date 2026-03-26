from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from db import db 
#from schemas import UserSignUpSchema, UserLoginSchema
from marshmallow import Schema, fields
from flask_login import login_user, logout_user, login_required, current_user
from models.coach_profiles import CoachProfiles, ApprovalStatusEnum
from models.specialties import Specialties
from models.users import Users


class CoachBrowsingSchema(Schema):
    coach_profile_id = fields.Int(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    specialty_name = fields.Str(dump_only=True)
    years_experience = fields.Int(dump_only=True)
    bio = fields.Str(dump_only=True)

#class CoachFiltering(Schema):
#    pass

coach_blp = Blueprint("browsing", __name__, description="Operations on coaches")

@coach_blp.route("/coachbrowse")
class CoachBrowse(MethodView):
    @coach_blp.response(200, CoachBrowsingSchema(many=True))
    def get(self):

        results = db.session.query(
            CoachProfiles.coach_profile_id,
            Users.first_name,
            Users.last_name,
            Specialties.name.label("specialty_name"),
            CoachProfiles.years_experience,
            CoachProfiles.bio
        ).join(Users, CoachProfiles.user_id == Users.user_id) \
        .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id) \
        .filter(CoachProfiles.status == ApprovalStatusEnum.APPROVED) \
        .all()

        return results