from datetime import datetime
import enum
from db import db

class gender_enum(enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"

class ClientProfiles(db.Model):
    __tablename__ = "client_profiles"
    client_profile_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer,db.ForeignKey('users.user_id'), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.Enum(gender_enum), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,onupdate=datetime.utcnow)
    height = db.Column(db.Numeric(5,2), nullable=True)
    weight = db.Column(db.Numeric(5,2), nullable=True)
