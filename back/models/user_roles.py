from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('user_auth.auth_id'), primary_key=True)
    role_id = db.Column(db.Integer, primary_key=True)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)