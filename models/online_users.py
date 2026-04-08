from datetime import datetime

from db import db

class OnlineUsers(db.Model):
    __tablename__ = 'online_users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False)
    socket_id = db.Column(db.String(255), nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_online = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    user = db.relationship('Users', foreign_keys=[user_id], backref='online_status')
