import os
import pytest
from models import Users, UserRoles, UserAuths, Roles, CoachProfiles, Specialties, PaymentPlans
import uuid

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "True"

from app import app as flask_app
from db import db

@pytest.fixture(scope="session", autouse=True)
def setup_test_config():
    flask_app.config.update({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
    })

@pytest.fixture
def app():
    with flask_app.app_context():
        ### SAFETY CHECK: TO PREVENT TABLE DESTRUCTION
        if "aivencloud" in str(db.engine.url):
            pytest.exit("\n\nCRITICAL ERROR: ENGINE POINTING TO CLOUD DB.\n")
            
        db.create_all()
        yield flask_app
        db.session.remove()
        # Keep this commented out for now!
        # db.drop_all() 

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def coach_headers(client, app):
    """
    Creates a fully setup Coach and returns auth headers using the 'token' key.
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"coach_{unique_id}@test.com"
    password = "password123"

    with app.app_context():
        if not Roles.query.get(2):
            db.session.add(Roles(role_id=2, name="coach"))
        
        spec = Specialties.query.filter_by(name="nutrition").first()
        if not spec:
            spec = Specialties(name="nutrition", coach_type="nutrition")
            db.session.add(spec)
            db.session.flush()

        auth = UserAuths(email=email, password=password)
        db.session.add(auth)
        db.session.flush() 

        user = Users(auth_id=auth.auth_id, first_name="Test", last_name="Coach")
        db.session.add(user)
        db.session.flush()

        db.session.add(UserRoles(user_id=user.user_id, role_id=2))
        
        profile = CoachProfiles(
            user_id=user.user_id, 
            bio="Certified Coach",
            years_experience=5,
            specialty_id=spec.specialty_id
        )
        db.session.add(profile)
        db.session.flush()

        plan = PaymentPlans(
            coach_profile_id=profile.coach_profile_id,
            name="Standard Plan",
            amount=50.0,
            billing_type="monthly",
            is_active=True
        )
        db.session.add(plan)
        db.session.commit()

    login_res = client.post('/auth/login', json={
        "email": email,
        "password": password
    })
    
    data = login_res.get_json()
    
    if 'token' not in data:
        pytest.fail(f"LOGIN FAILED. Body: {data}")
    
    return {"Authorization": f"Bearer {data['token']}"}

@pytest.fixture
def client_headers(client, app):
    """Creates a unique client with Role ID 1 and returns auth headers."""
    unique_id = str(uuid.uuid4())[:8]
    email = f"client_{unique_id}@test.com"
    password = "password123"

    with app.app_context():
        if not Roles.query.get(1):
            db.session.add(Roles(role_id=1, name="client"))
            
        auth = UserAuths(email=email, password=password)
        db.session.add(auth)
        db.session.flush()

        user = Users(auth_id=auth.auth_id, first_name="Test", last_name="Client")
        db.session.add(user)
        db.session.flush()

        db.session.add(UserRoles(user_id=user.user_id, role_id=1))
        db.session.commit()

    login_res = client.post('/auth/login', json={
        "email": email,
        "password": password
    })
    
    data = login_res.get_json()
    
    if 'token' not in data:
        pytest.fail(f"CLIENT LOGIN FAILED: {data}")
        
    return {"Authorization": f"Bearer {data['token']}"}