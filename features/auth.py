from http.client import HTTPException

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db import db
from models import UserAuths, UserRoles, Roles, Users
from middleware import roles_required 
from schemas.auth_schema import RegisterSchema, UserSetupSchema
from flask import jsonify
from models.coach_profiles import CoachProfiles # Ensure this path is correct
from models import Users, ClientProfiles, CoachProfiles

auth_blp = Blueprint("Authentication", __name__, url_prefix="/auth", description="Operations for User Auth")

@auth_blp.route("/register")
class UserRegister(MethodView):
    @auth_blp.arguments(RegisterSchema)
    @auth_blp.response(201)
    def post(self, data):
        # Check if user already exists
        if UserAuths.query.filter_by(email=data["email"]).first():
            abort(400, description="An account with this email already exists.")

        # create auth record and commit
        new_user = UserAuths(email=data["email"], password=data["password"])
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            client_role = Roles.query.filter_by(name='client').first()
            
            if client_role:
                role_link = UserRoles(user_id=new_user.auth_id, role_id=client_role.role_id)
                db.session.add(role_link)
                db.session.commit()
            else:
                return {"message": "Role 'client' not found in database."}, 500

            # gen token and return
            access_token = create_access_token(identity=str(new_user.auth_id))
            return {
                "message": "User registered successfully", 
                "user_id": new_user.auth_id, 
                "token": access_token
            }
            
        except Exception as e:
            db.session.rollback()
            return {"message": f"Registration failed at role assignment: {str(e)}"}, 500

@auth_blp.route("/setup")
class UserSetup(MethodView):
    @auth_blp.arguments(UserSetupSchema())
    @jwt_required()
    def post(self, data):
        current_auth_id=get_jwt_identity()

        #not client 
        print(current_auth_id)
        auth_rol_re=UserRoles.query.filter_by(user_id=current_auth_id, role_id=1).first()

        if not auth_rol_re:
            return {"msg":"Only for clients accounts"}, 403
        
        
        #handle users table
        existing_user=Users.query.filter_by(auth_id=current_auth_id).first()
                                        

        if existing_user: 
            return {"msg":"Client profile exists"},400
            
        user_info = {
            "first_name": data.pop("first_name"),
            "last_name": data.pop("last_name"),
            "phone_number": data.pop("phone_number", None)
        }

        try:
            #create user table, dont commit
            user=Users(auth_id=current_auth_id,**user_info)
                
            db.session.add(user)
            db.session.flush()
                
             
            client_pf=ClientProfiles(client_id=user.user_id, **data)

            db.session.add(client_pf)
            db.session.commit()
            return {"msg": "Setup successful", "auth_id": user.user_id}, 201 
    
        except Exception as e:
            db.session.rollback()
            return {"msg":f"Error occur during set up: {str(e)}"}, 400
        
@auth_blp.route("/login")
class UserLogin(MethodView):
    @auth_blp.arguments(RegisterSchema)
    def post(self,data):        
        
        user = UserAuths.query.filter_by(email=data.get("email")).first()
        
        # Check if user exists and password matches
        if user and user.password == data.get("password"):
            # Create JWT Token
            token = create_access_token(identity=str(user.auth_id))
            return {"token": token}, 200
        
        abort(401, description="Invalid email or password")

@auth_blp.route("/me")
class UserMe(MethodView):
    @jwt_required()
    def get(self):
        """
        Gets the current user's account based on JWT identity

        """
        current_auth_id = get_jwt_identity()
        user_roles = UserRoles.query.filter_by(user_id=current_auth_id).all()

        user=Users.query.filter_by(auth_id=current_auth_id).first()
        if user:
            user_id = user.user_id
        else:
            user_id = None       


        roles = [entry.role_id for entry in user_roles]
        return {
             #this is auth_id
            "logged_in_as": current_auth_id,
            "user_id":user_id,   
            "roles": roles,
            "msg": "Token is valid and middleware is active"
        }, 200
    
    @jwt_required()
    def delete(self):
        """
        Deletes the current user's account based on JWT identity
        """
        current_auth_id=get_jwt_identity()

        user_auth=UserAuths.query.get_or_404(current_auth_id)

        try:
            db.session.delete(user_auth)
            db.session.commit()
            return {"msg": "Account successfully deleted"}, 200
        except:
            db.session.rollback()
            abort(500, description="Could not delete account")


@auth_blp.route("/promote/<int:auth_id>")
class AdminPromote(MethodView):
    @jwt_required()
    # @roles_required('admin') <--------------------------------------------------------------------------------------------------- Commented for testing purposes, uncomment afterwards
    def post(self, auth_id):
        coach_role = Roles.query.filter_by(name='coach').first()
        
        if not coach_role:
            abort(404, description="Coach role not found in database")

        # checks the user_roles table to see if user is already a coach
        existing_role = UserRoles.query.filter_by(user_id=auth_id, role_id=coach_role.role_id).first()
        if existing_role:
            return {"message": "User is already a coach"}, 200

        new_assignment = UserRoles(user_id=auth_id, role_id=coach_role.role_id)
        
        try:
            db.session.add(new_assignment)

                
            db.session.commit()
            return {"msg": f"User with auth_id {auth_id} is now a coach"}, 200
        
        except Exception as e:
            db.session.rollback()
            # Added {str(e)} to can see if the role insert fails
            abort(400, description=f"Promotion failed: {str(e)}")
        
@auth_blp.route("/check-my-roles") # 1=admin, 2=coach, 3=client
class CheckRoles(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        # Query the user_roles table in models/role_model.py
        user_roles = UserRoles.query.filter_by(user_id=current_auth_id).all()
        
        role_ids = [r.role_id for r in user_roles]
        return {
            "auth_id": current_auth_id,
            "assigned_role_ids": role_ids,
            "is_already_coach": 2 in role_ids
        }

# def register_user(data):
#     data = request.get_json()
#     email = data.get('email')
#     password = data.get('password')

#     # check if user already exists
#     existing_user = UserAuths.query.filter_by(email=email).first()
#     if existing_user:
#         return jsonify({"error": "An account with this email already exists."}), 400
    
#     # create new user record
#     new_user = UserAuths(email=data['email'], password=data['password'])
#     db.session.add(new_user)
#     db.session.commit()
    
#     # assign client role to new sign-ups
#     client_role = Roles.query.filter_by(name='client').first()
#     if client_role:
#         role_link = UserRoles(user_id=new_user.auth_id, role_id=client_role.role_id)
#         db.session.add(role_link)
#         db.session.commit()
        
#     return {"message": "User registered successfully", "user_id": new_user.auth_id}, 201

# def login_user(data):
#     user = UserAuths.query.filter_by(email=data['email']).first()
    
#     # Check if user exists and password matches
#     if user and user.password == data['password']:
#         token = create_access_token(identity=str(user.auth_id))
#         return {"access_token": token}, 200
        
#     return {"error": "Invalid email or password"}, 401

# def promote_to_coach(auth_id):
#     # admin logic to change roles
#     coach_role = Roles.query.filter_by(name='coach').first()
    
#     if not coach_role:
#         return {"error": "Coach role not found in database"}, 404

#     # logic to link user to role
#     new_assignment = UserRoles(user_id=auth_id, role_id=coach_role.role_id)
    
#     try:
#         db.session.add(new_assignment)
#         db.session.commit()
#         return {"message": f"User {auth_id} is now a coach"}, 200
#     except Exception:
#         db.session.rollback()
#         return {"error": "Promotion failed. User might already be a coach."}, 400