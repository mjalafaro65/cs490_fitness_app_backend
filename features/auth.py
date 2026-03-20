from db import db
from models.user_auth import UserAuth
from models.user_roles import UserRoles
from models.roles import Roles
from flask_jwt_extended import create_access_token

def register_user(data):
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # check if user already exists
    existing_user = UserAuth.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "An account with this email already exists."}), 400
    
    # create new user record
    new_user = UserAuth(email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    # assign client role to new sign-ups
    client_role = Roles.query.filter_by(name='client').first()
    if client_role:
        role_link = UserRoles(user_id=new_user.auth_id, role_id=client_role.role_id)
        db.session.add(role_link)
        db.session.commit()
        
    return {"message": "User registered successfully", "user_id": new_user.auth_id}, 201

def login_user(data):
    user = UserAuth.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password matches
    if user and user.password == data['password']:
        token = create_access_token(identity=str(user.auth_id))
        return {"access_token": token}, 200
        
    return {"error": "Invalid email or password"}, 401

def promote_to_coach(auth_id):
    # admin logic to change roles
    coach_role = Roles.query.filter_by(name='coach').first()
    
    if not coach_role:
        return {"error": "Coach role not found in database"}, 404

    # logic to link user to role
    new_assignment = UserRoles(user_id=auth_id, role_id=coach_role.role_id)
    
    try:
        db.session.add(new_assignment)
        db.session.commit()
        return {"message": f"User {auth_id} is now a coach"}, 200
    except Exception:
        db.session.rollback()
        return {"error": "Promotion failed. User might already be a coach."}, 400