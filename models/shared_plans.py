from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class ShareTypeEnum(db.Enum):
    view = 'view'
    copy = 'copy'

class SavedPlan(db.Model):
    __tablename__ = 'saved_plans'
    
    saved_plan_id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.plan_id'), nullable=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    share_type = db.Column(db.Enum(ShareTypeEnum))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)