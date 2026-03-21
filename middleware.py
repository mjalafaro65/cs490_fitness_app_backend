from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from db import db
from models.user_roles import UserRoles
from models.roles import Roles

def roles_required(*allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request() # Ensure logged in
            current_user_id = get_jwt_identity() # Get auth_id
            
            # Join UserRoles and Roles to see if they have right name
            user_has_access = db.session.query(UserRoles).join(Roles, UserRoles.role_id == Roles.role_id).filter(
                UserRoles.user_id == current_user_id,
                Roles.name.in_(allowed_roles)
            ).first()

            if not user_has_access:
                return jsonify({"error": f"Unauthorized. Requires one of: {allowed_roles}"}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper