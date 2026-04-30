import pytest
import uuid
from datetime import datetime, timedelta
from flask_jwt_extended import decode_token
from models import (Users, CoachProfiles, CoachHireRequests, 
                    CoachClientRelationships, PaymentPlans, 
                    Specialties, PaymentMethods)
from models.coach_hire_requests import StatusEnum 
from db import db

# --- HELPER FIXTURES TO LINK DB OBJECTS TO AUTH ---

@pytest.fixture
def current_coach_user(app, coach_headers):
    with app.app_context():
        token = coach_headers['Authorization'].split(" ")[1]
        user_id = decode_token(token)['sub']
        return Users.query.get(user_id)

@pytest.fixture
def current_client_user(app, client_headers):
    with app.app_context():
        token = client_headers['Authorization'].split(" ")[1]
        user_id = decode_token(token)['sub']
        return Users.query.get(user_id)

@pytest.fixture
def payment_method(app, current_client_user):
    method = PaymentMethods(
        user_id=current_client_user.user_id,
        token=f"tok_{uuid.uuid4().hex[:8]}", 
        provider="stripe",
        last4="4242",
        brand="Visa",
        expires_at=datetime.utcnow() + timedelta(days=365),
        is_default=True
    )
    db.session.add(method)
    db.session.commit()
    return method

@pytest.fixture
def coach_profile(app, current_coach_user):
    """Links a profile using the confirmed 'nutrition' specialty."""
    profile = CoachProfiles.query.filter_by(user_id=current_coach_user.user_id).first()
    if not profile:
        specialty = Specialties.query.filter_by(name="nutrition").first()
        if not specialty:
            specialty = Specialties(name="nutrition", coach_type="nutrition")
            db.session.add(specialty)
            db.session.flush()

        profile = CoachProfiles(
            user_id=current_coach_user.user_id, 
            bio="Test Coach Bio",
            years_experience=5,
            specialty_id=specialty.specialty_id
        )
        db.session.add(profile)
        db.session.commit()
    return profile

@pytest.fixture
def payment_plan(coach_profile):
    """Creates a plan using 'payment_plan_id' mapping."""
    plan = PaymentPlans(
        coach_profile_id=coach_profile.coach_profile_id,
        name="Monthly Pro",
        billing_type="recurring",
        amount=100.00,
        is_active=True
    )
    db.session.add(plan)
    db.session.commit()
    return plan


# --- TESTS ---

def test_coach_accept_hire_request_lifecycle(client, coach_headers, current_client_user, payment_plan, payment_method):
    """Uses the global coach_headers to test the full acceptance flow."""
    
    hire_req = CoachHireRequests(
        client_user_id=current_client_user.user_id,
        coach_profile_id=payment_plan.coach_profile_id,
        payment_plan_id=payment_plan.payment_plan_id, 
        status=StatusEnum.pending,
        auto_pay_enabled=True 
    )
    db.session.add(hire_req)
    db.session.commit()

    response = client.post(
        f"/coach/hire-request/{hire_req.request_id}/accept",
        headers=coach_headers
    )

    assert response.status_code == 200
    
    rel = CoachClientRelationships.query.filter_by(client_user_id=current_client_user.user_id).first()
    assert rel is not None
    assert rel.status.value == "active"

def test_coach_deny_hire_request(client, coach_headers, current_client_user, payment_plan):
    """Tests the rejection branch using global coach headers."""
    
    hire_req = CoachHireRequests(
        client_user_id=current_client_user.user_id,
        coach_profile_id=payment_plan.coach_profile_id,
        payment_plan_id=payment_plan.payment_plan_id,
        status=StatusEnum.pending,
        auto_pay_enabled=False
    )
    db.session.add(hire_req)
    db.session.commit()

    response = client.post(
        f"/coach/hire-request/{hire_req.request_id}/deny",
        headers=coach_headers
    )

    assert response.status_code == 200
    updated_req = CoachHireRequests.query.get(hire_req.request_id)
    assert updated_req.status.value == "denied"