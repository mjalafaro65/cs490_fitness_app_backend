from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ActionTypeEnum(db.Enum):
    insert = 'insert'
    update = 'update'
    delete = 'delete'

class UserAuthAudit(db.Model):
    __tablename__ = 'user_auth_audit'

    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(ActionTypeEnum, nullable=False)
    action_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_by_user_id = db.Column(db.Integer)
    auth_id = db.Column(db.Integer, )
    email = db.Column(db.String(100))
