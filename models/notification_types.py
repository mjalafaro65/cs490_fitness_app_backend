from datetime import datetime
import enum
from db import db

class PrioEnum(enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'

class NotificationTypes(db.Model):
    __tablename__ = 'notification_types'
    
    notif_id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)    
    display_name = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.Enum(PrioEnum), nullable=False)