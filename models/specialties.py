from datetime import datetime

from db import db

class CoachTypeEnum(db.Enum):
    workout = 'workout'
    nutrition = 'nutrition'

class Specialties(db.Model):
    __tablename__ = 'specialties'
    
    specialty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    coach_type = db.Column(db.Enum(CoachTypeEnum), nullable=False)