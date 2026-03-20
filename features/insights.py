from flask.views import MethodView
from flask_smorest import Blueprint
from models.daily_wellness import DailyWellness
from db import db
from datetime import date


