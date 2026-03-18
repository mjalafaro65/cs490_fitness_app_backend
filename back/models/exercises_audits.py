from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ActionTypeEnum(db.Model):
    insert = 'insert
    update = 'update'
    delete = 'delete'

class ExerciseAudits(db.Model):
    __tablename__ = 'exercise_audits'

    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(ActionTypeEnum, nullable=False)
    ### Says foreign key in Dbeaver. Possible mistake?
    action_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    exercise_id = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(120))
    muscle_group = db.Column(db.String(60))
    equipment = db.Column(db.String(60))
    is_active = db.Column(db.Boolean)

    