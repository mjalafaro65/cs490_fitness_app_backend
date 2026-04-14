from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, Notifications
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.notif_schema import NotificationResponseSchema

notif_blp=Blueprint("Notifications", __name__, url_prefix="/notifications", description="Notifications feat")

@notif_blp.route("/all")
class NotificationsView(MethodView):
    @jwt_required()
    @notif_blp.response(200, NotificationResponseSchema(many=True))
    def get(self):
        """Get all notifications for a specific user"""
        curr_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).scalar()
        
        if not curr_user_id:
            abort(401, description="User not found.")

        stmt = (
            select(Notifications)
            .where(Notifications.user_id == curr_user_id)
            .order_by(Notifications.created_at.desc())
        )

        notifications = db.session.execute(stmt).scalars().all()
        
        if not notifications:
            return []

        return notifications
    


