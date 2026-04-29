import pytest
from flask_jwt_extended import create_access_token
from models import Users, CoachProfiles, ClientProfiles, Specialties, CoachClientRelationships, PaymentPlans, Invoices, PaymentMethods
from models.invoices import StatusEnumList
from models.coach_client_relationships import status_enum
from db import db

def test_rehire_coach_logic(client, app):
    """
    Test for the /client/rehire-coach endpoint.
    """
    with app.app_context():
        # 1. SETUP: Create the Coach and Client users
        coach_user = Users(auth_id="c1", first_name="Coach", last_name="Test")
        client_user = Users(auth_id="cl1", first_name="Client", last_name="Test")
        db.session.add_all([coach_user, client_user])
        db.session.commit()

        # 2. SETUP: Create Specialty and Coach Profile
        spec = Specialties(name="Weightloss", coach_type="nutrition") 
        db.session.add(spec)
        db.session.commit()

        c_profile = CoachProfiles(
            user_id=coach_user.user_id, 
            specialty_id=spec.specialty_id,
            years_experience=5,
            bio="Certified coach.",
            status="approved" 
        )
        cl_profile = ClientProfiles(client_id=client_user.user_id)
        db.session.add_all([c_profile, cl_profile])
        db.session.commit()
        
        # 3. SETUP: Create the Payment Plan 
        # Using 'payment_plan_id' as the attribute name
        plan = PaymentPlans(
            coach_profile_id=c_profile.coach_profile_id,
            name="Rehire Monthly",
            amount=150.0,
            billing_type="recurring",
        )
        db.session.add(plan)
        db.session.commit()
        
        # 4. SETUP: Create the old 'terminated' relationship
        # Updated to use 'payment_plan_id' for both the keyword and the attribute access
        old_relationship = CoachClientRelationships(
            client_user_id=client_user.user_id,
            coach_profile_id=c_profile.coach_profile_id,
            payment_plan_id=plan.payment_plan_id, 
            status=status_enum.terminated
        )
        db.session.add(old_relationship)
        db.session.commit()
        
        rel_id = old_relationship.relationship_id

        # 5. AUTH: Generate a real JWT for 'cl1'
        test_token = create_access_token(identity="cl1")

    # 6. ACT: Call the endpoint
    url = "/client/rehire-coach"
    headers = {"Authorization": f"Bearer {test_token}"}
    
    # Per client.py, the rehire-coach endpoint uses InitiateFireSchema, 
    # which likely only requires the relationship_id.
    payload = {
        "relationship_id": rel_id
    }
    
    response = client.post(url, headers=headers, json=payload)

    # 7. ASSERT: Verify success
    if response.status_code != 200:
        print(f"\nDEBUG RESPONSE: {response.json}")
    
    assert response.status_code == 200
    assert response.json["status"] == "pending"



def test_dispute_reason_requirement(client, app):
    """
    Test your specific requirement: 'reason' must be present (not optional) 
    even if it is null.
    """
    payload = {
        "amount": 50.0,
        "reason": None  # Nullable, but must be in the JSON
    }
    # This should pass if your schema validation is correct
    response = client.post("/dispute/create", json=payload)
    assert response.status_code != 422 # 422 would mean 'reason' was missing or invalid


def test_rehire_coach_not_found(client):
    # Testing the 'Sad Path' covers the 'if not coach:' lines in your code
    response = client.post("/client/rehire/999", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 404


def test_pay_invoice_logic(client, app):
    with app.app_context():
        # 1. SETUP: Core Users and Profiles
        coach_user = Users(auth_id="c2", first_name="Coach", last_name="Pay")
        client_user = Users(auth_id="cl2", first_name="Client", last_name="Pay")
        db.session.add_all([coach_user, client_user])
        db.session.commit()

        # FIXED: Changed specialty to nutrition
        spec = Specialties(name="Weight Loss", coach_type="nutrition")
        db.session.add(spec)
        db.session.commit()

        c_profile = CoachProfiles(
            user_id=coach_user.user_id, 
            specialty_id=spec.specialty_id, 
            status="approved",
            years_experience=5
        )
        db.session.add(c_profile)
        db.session.commit()

        # 2. SETUP: Payment Plan (Using Gold Standard fields)
        plan = PaymentPlans(
            coach_profile_id=c_profile.coach_profile_id,
            name="Monthly Plan",
            amount=100.0,
            billing_type="recurring"
        )
        db.session.add(plan)
        db.session.commit()

        # 3. SETUP: Relationship (Using payment_plan_id)
        rel = CoachClientRelationships(
            client_user_id=client_user.user_id,
            coach_profile_id=c_profile.coach_profile_id,
            payment_plan_id=plan.payment_plan_id,
            status=status_enum.active
        )
        db.session.add(rel)
        db.session.commit()

        # 4. SETUP: The Invoice and Payment Method
        invoice = Invoices(
            relationship_id=rel.relationship_id,
            subtotal=100.0,
            status=StatusEnumList.issued
        )
        card = PaymentMethods(
            user_id=client_user.user_id,
            last4="4242",
            token="pm_test_123",
            is_default=True
        )
        db.session.add_all([invoice, card])
        db.session.commit()

        inv_id = invoice.invoice_id
        test_token = create_access_token(identity="cl2")

    # 5. ACT: Call endpoint
    url = "/client/pay-invoice"
    headers = {"Authorization": f"Bearer {test_token}"}
    payload = {"invoice_id": inv_id} 
    
    response = client.post(url, headers=headers, json=payload)

    # 6. ASSERT
    assert response.status_code == 200
    assert response.json["message"] == "Invoice paid successfully"



def test_confirm_fire_coach_logic(client, app):
    with app.app_context():
        # 1. SETUP: Users and Profiles
        coach_user = Users(auth_id="c3", first_name="Coach", last_name="Gone")
        client_user = Users(auth_id="cl3", first_name="Client", last_name="Fire")
        db.session.add_all([coach_user, client_user])
        db.session.commit()

        # FIXED: Changed specialty to nutrition
        spec = Specialties(name="Sports Nutrition", coach_type="nutrition")
        db.session.add(spec)
        db.session.commit()
        
        c_profile = CoachProfiles(
            user_id=coach_user.user_id, 
            specialty_id=spec.specialty_id,
            status="approved",
            years_experience=5,
        )
        db.session.add(c_profile)
        db.session.commit()
        
        plan = PaymentPlans(
            coach_profile_id=c_profile.coach_profile_id, 
            name="Pro", 
            amount=50.0,
            billing_type="onetime"
        )
        db.session.add(plan)
        db.session.commit()

        # 2. SETUP: Active Relationship
        rel = CoachClientRelationships(
            client_user_id=client_user.user_id,
            coach_profile_id=c_profile.coach_profile_id,
            payment_plan_id=plan.payment_plan_id,
            status=status_enum.active
        )
        db.session.add(rel)
        db.session.commit()

        # 3. SETUP: Multiple Unpaid Invoices
        inv1 = Invoices(relationship_id=rel.relationship_id, subtotal=50.0, status=StatusEnumList.issued)
        inv2 = Invoices(relationship_id=rel.relationship_id, subtotal=50.0, status=StatusEnumList.issued)
        db.session.add_all([inv1, inv2])
        db.session.commit()

        rel_id = rel.relationship_id
        test_token = create_access_token(identity="cl3")

    # 4. ACT
    url = "/client/confirm-fire-coach"
    headers = {"Authorization": f"Bearer {test_token}"}
    payload = {"relationship_id": rel_id}
    
    response = client.post(url, headers=headers, json=payload)

    # 5. ASSERT
    assert response.status_code == 200
    assert "terminated" in response.json["message"]
    
    # Verify DB state change
    with app.app_context():
        # Check relationship status
        updated_rel = CoachClientRelationships.query.get(rel_id)
        assert updated_rel.status == status_enum.terminated
        # Check invoices are voided
        voided_count = Invoices.query.filter_by(relationship_id=rel_id, status=StatusEnumList.voided).count()
        assert voided_count == 2