from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Notifications(db.Model):
    __tablename__ = 'notifications'
    
    notif_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    notif_type_id = db.Column(db.Integer, db.ForeignKey('notification_types.notif_id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)