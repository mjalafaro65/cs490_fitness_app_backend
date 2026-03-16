from datetime import datetime
from sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    
   role_id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(50), unique=True, nullable=False)