from datetime import datetime
from sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AccountDeletionInfo(db.Model):
    __tablename__="account_deletion_info"
    id = db.Column(db.Integer, primary_key=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(255), nullable=True)
    detailed_reason = db.Column(db.Text, nullable=True)

