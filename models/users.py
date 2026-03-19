from datetime import datetime


from db import db

class Users(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    disabled_at = db.Column(db.DateTime, nullable=True)
    disabled_by_admin_user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    