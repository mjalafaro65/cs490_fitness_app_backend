from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ActionTypeEnum(db.Enum):
    insert = 'insert'
    update = 'update'
    delete = 'delete'

class UsersAudit(db.Model):
    __tablename__ = 'users_audit'

    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(ActionTypeEnum, nullable=False)
    action_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_by_user_id = db.Column(db.Integer, db.ForeignKey('user_auth.auth_id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

    