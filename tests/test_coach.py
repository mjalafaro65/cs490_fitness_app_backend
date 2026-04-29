import pytest
from flask_jwt_extended import create_access_token
from models import Users, CoachProfiles, ClientProfiles, Specialties, CoachClientRelationships, PaymentPlans, Invoices, PaymentMethods
from models.invoices import StatusEnumList
from models.coach_client_relationships import status_enum
from datetime import datetime
from db import db

