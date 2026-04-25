from datetime import datetime
from db import db

class UserLoginActivity(db.Model):
    __tablename__ = "user_login_activity"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    # 1 = client, 2 = coach, 3 = admin
    role_at_login = db.Column(db.Integer, nullable=False)

    last_active_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

   