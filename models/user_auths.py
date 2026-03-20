from datetime import datetime
from flask_login import UserMixin

from db import db

class UserAuths(db.Model, UserMixin):
    __tablename__ = 'user_auths'
    
    auth_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
