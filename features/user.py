
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db import db
from models import UserAuths, UserRoles, Roles, Users
from middleware import roles_required 
from schemas.user_schema import  UserInfoSchema, UserUpdateSchema, UserDeleteSchema
from flask import jsonify
from models.coach_profiles import CoachProfiles # Ensure this path is correct
from models import Users, ClientProfiles, CoachProfiles, AccountDeletionInfo

user_blp = Blueprint("Users", __name__, url_prefix="/user", description="Operations for  all Users")


@user_blp.route("/me")
class UserMeProfile(MethodView):

    @jwt_required()
    @user_blp.response(200, UserInfoSchema)
    def get(self):
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        return user
    
    @jwt_required()
    @user_blp.arguments(UserUpdateSchema)
    @user_blp.response(200, UserInfoSchema)
    def patch(self, update_data):
        curr_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=curr_auth_id).first_or_404()

        for key, value in update_data.items():
            setattr(user, key, value)

        db.session.commit()
        return user
    
    @jwt_required()
    def delete(self, data):
        """
        Deletes the current user's account based on JWT identity
        """
        current_auth_id=get_jwt_identity()
        

        user_auth=UserAuths.query.get_or_404(current_auth_id)

        try:
            deletion_log = AccountDeletionInfo(
                auth_id=current_auth_id,
                reason=data.get("reason"),
                detailed_reason=data.get("detailed_reason"))
            
            db.session.add(deletion_log)
            
            db.session.delete(user_auth)
            db.session.commit()
            return {"msg": "Account successfully deleted"}, 200
        except:
            db.session.rollback()
            abort(500, description="Could not delete account")

            
@user_blp.route("/<int:user_id>")
class UserLookup(MethodView):

    @user_blp.response(200, UserInfoSchema)
    def get(self, user_id):
        user = Users.query.get_or_404(user_id)
        return user
    
    @jwt_required()
    @user_blp.arguments(UserUpdateSchema)
    @user_blp.response(200, UserInfoSchema)
    def patch(self, update_data, user_id):

        user = Users.query.get_or_404(user_id)

        for key, value in update_data.items():
            setattr(user, key, value)

        db.session.commit()

        return user
