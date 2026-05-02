from datetime import datetime
from db import db


class CoachAvailability(db.Model):
    __tablename__ = "coach_availability"

    availability_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    coach_profile_id = db.Column( db.Integer,  db.ForeignKey("coach_profiles.coach_profile_id" ) ,nullable=False)

    day_of_week = db.Column(db.Integer, nullable=False)  
    # 0 = Sunday, 6 = Saturday

    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    coach = db.relationship("CoachProfiles", backref="availability")