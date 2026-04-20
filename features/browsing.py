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
from models.coach_favorites import CoachFavorites
from flask_jwt_extended import jwt_required, get_jwt_identity


class CoachBrowsingSchema(Schema):
    coach_profile_id = fields.Int(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    specialty_name = fields.Str(dump_only=True)
    years_experience = fields.Int(dump_only=True)
    bio = fields.Str(dump_only=True)
    is_favorited = fields.Bool(dump_only=True)

#class CoachFiltering(Schema):
#    pass

coach_blp = Blueprint("browsing", __name__, description="Operations on coaches")

@coach_blp.route("/coachbrowse")
class CoachBrowse(MethodView):
    @jwt_required()
    @coach_blp.response(200, CoachBrowsingSchema(many=True))
    def get(self):
        # Get current user
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        # Get user's favorite coach IDs
        favorite_ids = []
        if user:
            favorite_coach_ids = db.session.query(CoachFavorites.coach_profile_id).filter_by(
                user_id=user.user_id
            ).all()
            favorite_ids = [fav[0] for fav in favorite_coach_ids]
        
        # Get all approved coaches with favorite status
        results = []
        coaches = db.session.query(
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
        
        # Convert to dict format and add favorite status
        for coach in coaches:
            coach_dict = {
                'coach_profile_id': coach.coach_profile_id,
                'first_name': coach.first_name,
                'last_name': coach.last_name,
                'specialty_name': coach.specialty_name,
                'years_experience': coach.years_experience,
                'bio': coach.bio,
                'is_favorited': coach.coach_profile_id in favorite_ids
            }
            results.append(coach_dict)
        
        # Sort: favorited coaches first
        results.sort(key=lambda x: not x['is_favorited'])
        
        return results