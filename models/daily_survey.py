from datetime import datetime, date
from db import db

#will be used for both initial survey and wellness survey
class DailySurvey(db.Model):
    __tablename__ = 'daily_survey'

    survey_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    #cascade_delete = db.relationship("TargetClassName", cascade="all, delete-orphan")#
    date = db.Column(db.Date,  default=lambda: datetime.utcnow().date(), nullable=False)

    daily_goal= db.Column(db.String(45), nullable=True)
    energy_level=db.Column(db.Integer, nullable=True)
    target_focus=db.Column(db.String(45), nullable=True)


    water_oz = db.Column(db.Numeric(4, 2), default=0.0, nullable=True)
    mood_score = db.Column(db.Integer, nullable=True)
    weight_lbs = db.Column(db.Numeric(5, 2), nullable=True)
    sleep_hours = db.Column(db.Numeric(4, 2),nullable=True)


    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_dw_user_date'),
    )