from datetime import datetime
from sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class gender_enum(db.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    Prefer_not_to_say = "prefer_not_to_say"

class ClientProfiles(db.Model):
    __tablename__ = "client_profiles"
    profile_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(gender_enum, nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
     onupdate=datetime.utcnow)
    height = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Integer, nullable=True)
