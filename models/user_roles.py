from datetime import datetime

from db import db

class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('user_auths.auth_id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), primary_key=True)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)