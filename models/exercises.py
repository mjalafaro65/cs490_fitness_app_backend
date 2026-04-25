from datetime import datetime

from db import db

class Exercises(db.Model):
    __tablename__ = "exercises"

    exercise_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    muscle_group = db.Column(db.String(60), nullable=False)
    equipment = db.Column(db.String(60), nullable=False)
    training_type = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text)
    keywords = db.Column(db.Text, nullable=True)  # JSON array or comma-separated values
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # NULL creator = catalog / default exercise; set for user-created moves
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    # Published custom exercises appear alongside defaults in the shared catalog
    is_public = db.Column(db.Boolean, default=False, nullable=False)

  