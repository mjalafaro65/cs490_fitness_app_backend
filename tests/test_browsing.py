# tests/test_browsing.py

from models.users import Users
from models.specialties import Specialties
from models.coach_profiles import CoachProfiles, ApprovalStatusEnum
from db import db
from flask_jwt_extended import create_access_token

def test_coach_browse_endpoint(client, app):
    with app.app_context():
        test_user = Users(
            auth_id="test123", 
            first_name="tester", 
            last_name="Test", 
            email="tester@test.com"
        )
        db.session.add(test_user)
        
        specialty = Specialties(name="Strength & Testing")
        db.session.add(specialty)
        db.session.flush()
        
        coach = CoachProfiles(
            user_id=test_user.user_id,
            specialty_id=specialty.specialty_id,
            years_experience=3,
            bio="Ready to help you hit your Tests.",
            status=ApprovalStatusEnum.APPROVED
        )
        db.session.add(coach)
        db.session.commit()
        
        access_token = create_access_token(identity="test123")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = client.get("/coachbrowse", headers=headers)
    
    assert response.status_code == 200
    
    data = response.json
    
    assert len(data) == 1
    assert data[0]["first_name"] == "tester"
    assert data[0]["specialty_name"] == "Strength & Testing"
    assert data[0]["years_experience"] == 3
    assert data[0]["is_favorited"] == False