from http.client import HTTPException

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db import db
from models import UserAuths, UserRoles, Roles, Users
from models import Notifications, NotificationTypes
from middleware import roles_required 
from schemas.auth_schema import RegisterSchema, UserSetupSchema

# Create the Blueprint
auth_blp = Blueprint("Authentication", __name__, url_prefix="/auth", description="Operations for User Auth")

@auth_blp.route("/register")
class UserRegister(MethodView):
    @auth_blp.arguments(RegisterSchema)
    @auth_blp.response(201)
    def post(self, data):
        # 1. Check if user already exists
        if UserAuths.query.filter_by(email=data["email"]).first():
            abort(400, message="An account with this email already exists.")

        # 2. Create the Auth record
        # Note: We should add generate_password_hash(data["password"]) here later for security!
        new_user = UserAuths(email=data["email"], password=data["password"])
        
        try:
            db.session.add(new_user)
            db.session.commit()

            # 3. Assign default 'client' role
            client_role = Roles.query.filter_by(name='client').first()
            if client_role:
                role_link = UserRoles(user_id=new_user.auth_id, role_id=client_role.role_id)
                db.session.add(role_link)
                db.session.commit()

            access_token = create_access_token(identity=str(new_user.auth_id))
            return {"message": "User registered successfully", "user_id": new_user.auth_id, "token": access_token}
            
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Registration failed: {str(e)}")

@auth_blp.route("/setup")
class UserSetup(MethodView):
    @jwt_required()
    @auth_blp.arguments(UserSetupSchema())
    def post(self, data):
        current_auth_id=get_jwt_identity()

        #not client 
        auth_rol_re=UserRoles.query.filter_by(user_id=current_auth_id, role_id=1).first()

        if not auth_rol_re:
            abort(403, message="Only for clients accounts")
        
        
        #handle users table
        existing_user=Users.query.filter_by(auth_id=current_auth_id).first()

        if  existing_user: 
            abort(400,message="Client profile exists")
            
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
            return {"message": "Setup successful", "auth_id": user.user_id}, 201 
    
        except Exception as e:
            db.session.rollback()
            abort(500, message= f"Error occur during set up: {str(e)}") 

        
@auth_blp.route("/login")
class UserLogin(MethodView):
    @auth_blp.arguments(RegisterSchema)
    def post(self,data):        
        
        user = UserAuths.query.filter_by(email=data.get("email")).first()
        
        # Check if user exists and password matches
        if user and user.password == data.get("password"):
            # Create JWT Token
            token = create_access_token(identity=str(user.auth_id))
            return {"access_token": token}, 200
        
        abort(401, message="Invalid email or password")

@auth_blp.route("/me")
class UserMe(MethodView):
    @jwt_required()
    def get(self):
        """
        returns user auth info based on JWT identity

        """
        current_auth_id = get_jwt_identity()
        user_roles = UserRoles.query.filter_by(user_id=current_auth_id).all()

        roles = [entry.role_id for entry in user_roles]
        return {
             #this is auth_id
            "logged_in_as": current_auth_id,
            "roles": roles,
            "message": "Token is valid and middleware is active"
        }, 200
    @jwt_required()
    def delete(self):
        """
        Deletes the logged-in user's account based on JWT identity
        """
        current_auth_id=get_jwt_identity()

        user_auth=UserAuths.query.get_or_404(current_auth_id)

        try:
            db.session.delete(user_auth)
            db.session.commit()
            return {"message": "Account successfully deleted"}, 200
        except:
            db.session.rollback()
            abort(500, message="Could not delete account")


@auth_blp.route("/promote/<int:auth_id>")
class AdminPromote(MethodView):
    @jwt_required()
    @roles_required('admin')
    def post(self, auth_id):
        coach_role = Roles.query.filter_by(name='coach').first()
        
        if not coach_role:
            abort(404, message="Coach role not found in database")

        # Check if they are already a coach to avoid duplicates
        existing_role = UserRoles.query.filter_by(user_id=auth_id, role_id=coach_role.role_id).first()
        if existing_role:
            return {"message": "User is already a coach"}, 200


        new_assignment = UserRoles(user_id=auth_id, role_id=coach_role.role_id)
        
        try:
            db.session.add(new_assignment)

            notif_type = NotificationTypes.query.filter_by(slug='admin-approval').first()
            if notif_type:
                new_notif = Notifications(
                    user_id=auth_id,
                    notification_type_id=notif_type.notification_type_id,
                    title="Promotion Approved!",
                    body="Congratulations! An admin has promoted you to the Coach role.",
                    is_read=False
                )
                db.session.add(new_notif)

            db.session.commit()
            return {"message": f"User with auth_id {auth_id} is now a coach"}, 200
        except Exception:
            db.session.rollback()
            abort(400, message="Promotion failed.")
        




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