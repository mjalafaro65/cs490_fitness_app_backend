from flask import abort, request
from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema, ProfileSchema, ReviewCoachSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select
from models import Users
from models.daily_survey import DailySurvey
from models import ClientProfiles, CoachReviews

client_blp = Blueprint("ClientOperations", __name__, url_prefix="/client", description="Client Operations")

@client_blp.route("/daily-survey")
class DailySurveyView(MethodView):
    @jwt_required()
    @client_blp.arguments(DailySurveySchema)
    @client_blp.response(200,DailySurveySchema)
    def post(self, data):
        """
        Input or update daily surveys: initial and wellness

        *no need to pass client id in url, it will be obtained from jwt
        """
        today=date.today()

        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            return {"msg":"user not found"},404
        
        current_user_id=user.user_id
        #make stmt
        #current_user is logged in uses from login_required
        stmt=select(DailySurvey).filter_by(user_id=current_user_id , date=today)

        #execute 
        entry=db.session.execute(stmt).scalar_one_or_none()

        if not entry:   
            #create new
            entry= DailySurvey(user_id=current_user_id , date=today, **data)
            db.session.add(entry)
        else:
            #update 
            for key, value in data.items():
                if value is not None:
                    setattr(entry, key, value)

        db.session.commit()
        return entry
    
    @jwt_required()
    def get(self):
        """
        Check if the user has already submitted a survey today.
        """
        today = date.today()
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        if not user:
            return {"msg": "User not found"}, 404

        # Check for an existing entry for today
        stmt = select(DailySurvey).filter_by(user_id=user.user_id, date=today)
        entry = db.session.execute(stmt).scalar_one_or_none()

        if entry:
            # You can return the data or just a simple boolean
            return {
                "completed": True, 
                "date": today.isoformat(),
                "survey_id": entry.survey_id
            }, 200
        
        return {"completed": False}, 200

@client_blp.route("/profile")
class ClientProfileView(MethodView):
    @jwt_required()
    @client_blp.response(200, ProfileSchema)
    def get(self):
        """Retrieve the authenticated client's profile details."""
        current_auth_id = get_jwt_identity()
        
        # find user record linked to Auth ID
        
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        if not user:
            abort(404, description="User record not found.")

        # use user.user_id to find the profile
        profile = ClientProfiles.query.filter_by(client_id=user.user_id).first()
        
        if not profile:
            abort(404, description="Profile not found. Please complete setup.")
            
        return profile

    @jwt_required()
    @client_blp.arguments(ProfileSchema)
    @client_blp.response(200, ProfileSchema)
    def put(self, data):
        """Update the authenticated client's metrics and bio."""
        current_auth_id = get_jwt_identity()
        
        from models import Users
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        
        if not user:
            abort(404, description="User record not found.")
        
        profile = ClientProfiles.query.filter_by(client_id=user.user_id).first()
        
        if not profile:
            abort(400, description="Profile not found. Use /auth/setup to create your profile.")

        for key, value in data.items():
            setattr(profile, key, value)

        try:
            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error: {str(e)}")


### Delete Daily records 
@client_blp.route("/delete-daily")
class DeleteDailyView(MethodView):
    @jwt_required()
    @client_blp.response(200, DailySurveySchema)
    def patch(self):
        current_auth_id = get_jwt_identity()
        
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            abort(404, description="User record not found.")
        
        today = date.today()
        daily_survey = DailySurvey.query.filter_by(
            client_id=user.user_id, 
            date=today
        ).first()
        
        if not daily_survey:
            abort(404, description="No log found for today to reset.")

        daily_survey.daily_goal = None
        daily_survey.target_focus = None
        try:
            db.session.commit()
            return daily_survey
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error: {str(e)}")

### Edit Daily records
@client_blp.route("/edit-daily")
class EditDailyView(MethodView):
    @jwt_required()
    @client_blp.arguments(DailySurveySchema)
    @client_blp.response(200, DailySurveySchema)
    def patch(self, data):
        current_auth_id = get_jwt_identity()
        
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            abort(404, description="User record not found.")
        
        today = date.today()
        daily_survey = DailySurvey.query.filter_by(
            client_id=user.user_id, 
            date=today
        ).first()
        
        if not daily_survey:
            abort(404, description="Today's log not found. Create one first.")

        for key, value in data.items():
            setattr(daily_survey, key, value)

        try:
            db.session.commit()
            return daily_survey
        except Exception as e:
            db.session.rollback()
            abort(500, description="Failed to update the daily log.")

### Client Reviews Coach
@client_blp.route("/review-coach/<int:coach_id>")
class ReviewCoachView(MethodView):
    @jwt_required()
    @client_blp.arguments(ReviewCoachSchema)
    @client_blp.response(200, ReviewCoachSchema)
    def post(self, data, coach_id):
        current_auth_id = get_jwt_identity()

        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            abort(404, description="User record not found.")

        coach = CoachProfiles.query.get(coach_id)
        if not coach:
            abort(404, description="Coach profile not found.")

        existing_review = CoachReviews.query.filter_by(
            coach_profile_id=coach_id,
            client_user_id=user.user_id
        ).first()

        if existing_review:
            abort(400, description="You have already submitted a review for this coach.")

        review = CoachReviews(
            coach_profile_id=coach_id,
            client_user_id=user.user_id,
            rating=data['rating'],
            comment=data.get('comment')
        )

        try:
            db.session.add(review)
            db.session.commit()
            return review
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error: {str(e)}")

### Manage Personal Reviews
@client_blp.route("/my-reviews")
class ClientReviewsView(MethodView):
    @jwt_required()
    @client_blp.response(200, ReviewCoachSchema(many=True))
    def get(self):
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            abort(404, description="User record not found.")
        
        return CoachReviews.query.filter_by(client_user_id=user.user_id).all()

### Editing Client's own review
@client_blp.route("/my-reviews/<int:review_id>")
class EditReviewView(MethodView):
    @jwt_required()
    @client_blp.arguments(ReviewCoachSchema(partial=True))
    @client_blp.response(200, ReviewCoachSchema)
    def patch(self, data, review_id):
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            abort(404, description="User record not found.")

        review = CoachReviews.query.filter_by(
            review_id=review_id, 
            client_user_id=user.user_id
        ).first()
        if not review:
            abort(404, description="Review not found.")

        for key, value in data.items():
            setattr(review, key, value)

        db.session.commit()
        return review
