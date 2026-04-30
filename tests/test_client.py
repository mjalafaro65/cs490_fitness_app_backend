import pytest
from models import (Users, CoachProfiles, ClientProfiles, Specialties, 
                    CoachClientRelationships, PaymentPlans, Invoices, PaymentMethods)
from models.invoices import StatusEnumList
from models.coach_client_relationships import status_enum
from datetime import datetime
from db import db

def test_client_profile_unauthenticated(client):
    response = client.get("/client/profile")
    assert response.status_code == 401

def test_rehire_coach_logic(client, app, client_headers, coach_headers):
    """
    Test for the /client/rehire-coach endpoint using global fixtures.
    """
    from flask_jwt_extended import decode_token
    
    with app.app_context():
        client_id = decode_token(client_headers['Authorization'].split(" ")[1])['sub']
        coach_id = decode_token(coach_headers['Authorization'].split(" ")[1])['sub']

        spec = Specialties.query.filter_by(name="nutrition").first()
        if not spec:
            spec = Specialties(name="nutrition", coach_type="nutrition")
            db.session.add(spec)
            db.session.flush()

        c_profile = CoachProfiles.query.filter_by(user_id=coach_id).first()
        if not c_profile:
            c_profile = CoachProfiles(user_id=coach_id, specialty_id=spec.specialty_id, status="approved", years_experience=5)
            db.session.add(c_profile)
            db.session.flush()

        plan = PaymentPlans(
            coach_profile_id=c_profile.coach_profile_id,
            name="Rehire Monthly",
            amount=150.0,
            billing_type="recurring",
        )
        db.session.add(plan)
        db.session.flush()
        
        old_relationship = CoachClientRelationships(
            client_user_id=client_id,
            coach_profile_id=c_profile.coach_profile_id,
            payment_plan_id=plan.payment_plan_id, 
            status=status_enum.terminated
        )
        db.session.add(old_relationship)
        db.session.commit()
        
        rel_id = old_relationship.relationship_id

    response = client.post(
        "/client/rehire-coach", 
        headers=client_headers, 
        json={"relationship_id": rel_id}
    )

    assert response.status_code == 200
    assert response.json["status"] == "pending"

def test_pay_invoice_logic(client, app, client_headers, coach_headers):
    from flask_jwt_extended import decode_token
    
    with app.app_context():
        client_id = decode_token(client_headers['Authorization'].split(" ")[1])['sub']
        coach_id = decode_token(coach_headers['Authorization'].split(" ")[1])['sub']

        c_profile = CoachProfiles.query.filter_by(user_id=coach_id).first()
        
        plan = PaymentPlans(coach_profile_id=c_profile.coach_profile_id, name="Invoice Test", amount=100.0, billing_type="recurring")
        db.session.add(plan)
        db.session.flush()

        rel = CoachClientRelationships(client_user_id=client_id, coach_profile_id=c_profile.coach_profile_id, payment_plan_id=plan.payment_plan_id, status=status_enum.active)
        db.session.add(rel)
        db.session.flush()

        card = PaymentMethods(user_id=client_id, last4="4242", token="pm_test_123", is_default=True, provider="stripe", brand="Visa", expires_at=datetime(2027, 12, 1))
        db.session.add(card)
        db.session.flush()

        invoice = Invoices(
            relationship_id=rel.relationship_id,
            subtotal=100.0,
            status=StatusEnumList.issued,
            payment_method_id=card.payment_method_id,
            currency="USD"
        )
        db.session.add(invoice)
        db.session.commit()
        inv_id = invoice.invoice_id

    response = client.post("/client/pay-invoice", headers=client_headers, json={"invoice_id": inv_id})

    assert response.status_code == 200
    assert response.json["message"] == "Payment successful"

def test_confirm_fire_coach_logic(client, app, client_headers, coach_headers):
    from flask_jwt_extended import decode_token
    
    with app.app_context():
        client_id = decode_token(client_headers['Authorization'].split(" ")[1])['sub']
        coach_id = decode_token(coach_headers['Authorization'].split(" ")[1])['sub']

        c_profile = CoachProfiles.query.filter_by(user_id=coach_id).first()
        plan = PaymentPlans(coach_profile_id=c_profile.coach_profile_id, name="Pro", amount=50.0, billing_type="onetime")
        db.session.add(plan)
        db.session.flush()

        rel = CoachClientRelationships(client_user_id=client_id, coach_profile_id=c_profile.coach_profile_id, payment_plan_id=plan.payment_plan_id, status=status_enum.active)
        db.session.add(rel)
        db.session.flush()

        card = PaymentMethods(user_id=client_id, last4="1111", token="pm_fire", is_default=True, provider="stripe", brand="Visa", expires_at=datetime(2028, 1, 1))
        db.session.add(card)
        db.session.flush()

        inv1 = Invoices(relationship_id=rel.relationship_id, subtotal=50.0, status=StatusEnumList.issued, payment_method_id=card.payment_method_id, currency="USD")
        inv2 = Invoices(relationship_id=rel.relationship_id, subtotal=50.0, status=StatusEnumList.issued, payment_method_id=card.payment_method_id, currency="USD")
        db.session.add_all([inv1, inv2])
        db.session.commit()
        rel_id = rel.relationship_id

    response = client.post("/client/confirm-fire-coach", headers=client_headers, json={"relationship_id": rel_id})

    assert response.status_code == 200
    assert "Termination" in response.json["message"]
    
    with app.app_context():
        updated_rel = CoachClientRelationships.query.get(rel_id)
        assert updated_rel.status == status_enum.terminated
        voided_count = Invoices.query.filter_by(relationship_id=rel_id, status=StatusEnumList.voided).count()
        assert voided_count == 2

def test_dispute_reason_requirement(client, app, client_headers):
    """Ensures 'reason' is required in the payload, even if null."""
    payload = {"amount": 50.0, "reason": None}
    response = client.post("/dispute/create", headers=client_headers, json=payload)
    assert response.status_code != 422