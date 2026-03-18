from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ActionEnum(db.Enum):
    insert = 'insert'
    update = 'update'
    delete = 'delete'

class StatusEnum(db.Enum):
    pending = 'pending'
    completed = 'completed'
    failed = 'failed'
    refunded = 'refunded'

class PaymentAudit(db.Model):
    __tablename__ = 'payment_audit'
    
    audit_id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(ActionEnum, nullable=False)
    action_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    payment_id = db.Column(db.Integer)
    invoice_id = db.Column(db.Integer)
    payer_user_id = db.Column(db.Integer)
    amount = db.Column(db.Numeric(10,2))
    status = db.Column(StatusEnum)
    processed_at = db.Column(db.DateTime, nullable=True)

