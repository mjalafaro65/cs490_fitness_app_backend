from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, Notifications, UserRoles
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, or_, select, desc
from schemas.notif_schema import NotificationResponseSchema

notif_blp=Blueprint("Notifications", __name__, url_prefix="/notifications", description="Notifications feat")

@notif_blp.route("/all")
class NotificationsView(MethodView):
    @jwt_required()
    @notif_blp.response(200, NotificationResponseSchema(many=True))
    def get(self):
        """Get all notifications for a specific user"""
        curr_auth_id = get_jwt_identity()
        
        user = Users.query.filter_by(auth_id=curr_auth_id).first()
        

        # get roles via relationship
        user = Users.query.filter_by(auth_id=curr_auth_id).first()
        if not user:
            abort(401, description="User not found.")
        role_ids = [r.role_id for r in user.roles]

                
        stmt = (
            select(Notifications)
            .where(
                or_(
                    Notifications.user_id == user.user_id,
                    Notifications.role_id.in_(role_ids)
                )
            )
            .order_by(Notifications.is_read.asc(), Notifications.created_at.desc())
        )

        notifications = db.session.execute(stmt).scalars().all()
        return notifications or []
    


