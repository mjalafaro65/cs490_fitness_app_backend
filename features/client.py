from flask import abort, request
from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema, ProfileSchema, HireRequestCreateSchema, HireRequestStatusSchema, HireRequestListSchema, ReviewCoachSchema
from schemas.coach_schema import CoachProfileSchema
from models.coach_client_relationships import CoachClientRelationships, status_enum
from models.invoices import Invoices

from schemas.coach_schema import PaymentPlanSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select
from models import Users
from models.coach_reports import CoachReports, StatusEnum
from models.daily_survey import DailySurvey
from models.review_interactions import InteractionType
from datetime import datetime, timezone

from models.coach_hire_requests import StatusEnum
from models import ClientProfiles, PaymentPlans, CoachHireRequests, CoachProfiles, CoachReviews, CoachFavorites, ReviewInteractions
from .utils import create_notification

client_blp = Blueprint("ClientOperations", __name__, url_prefix="/client", description="Client Operations")

def _auth_id_int():
    raw = get_jwt_identity()
    if raw is None:
        abort(401, description="Not authenticated.")
    try:
        return int(raw)
    except (TypeError, ValueError):
        abort(401, description="Invalid token.")

def _current_user():
    user = Users.query.filter_by(auth_id=_auth_id_int()).first()
    if not user:
        abort(404, description="User record not found.")
    return user
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
            abort(404, description="user not found")
        
        current_user_id=user.user_id
        #make stmt
        #current_user is logged in uses from login_required
        stmt = select(DailySurvey).where(
        DailySurvey.user_id == current_user_id, 
        func.date(DailySurvey.date) == today
        )

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
    @client_blp.response(200, DailySurveySchema)
    def get(self):
        """
        Fetch today's survey data using the full DailySurveySchema.
        """
        today = date.today()
        current_auth_id = get_jwt_identity()
        
        user = Users.query.filter_by(auth_id=current_auth_id).first()
        if not user:
            abort(404, description="User not found")

       
        entry = DailySurvey.query.filter_by(user_id=user.user_id, date=today).first()

        if not entry:
            abort(404, description="No survey submitted for today.")

        return entry
    
@client_blp.route("/survey-status")
class CheckSurvey(MethodView):  
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
        stmt = select(DailySurvey).where(
        DailySurvey.user_id == user.user_id, 
        func.date(DailySurvey.date) == today
        )
        entry = db.session.execute(stmt).scalar_one_or_none()

        if entry:
                  
            if entry.updated_at.date() == today and  entry.updated_at != entry.created_at:
                return {
                "completed": True, 
                "updated:": True,
                "date": today.isoformat(),
                "survey_id": entry.survey_id
                }, 200
            else:
                return {
                    "completed": True, 
                    "updated": False,
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
            return {"msg":"User record not found."}, 404

        # use user.user_id to find the profile
        profile = ClientProfiles.query.filter_by(client_id=user.user_id).first()
        
        if not profile:
            return {"msg":"Profile not found. Please complete setup."}, 404
            
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




@client_blp.route("/coach-payment-plans/<int:coach_profile_id>")
class ClientPaymentPlanListView(MethodView):
    @client_blp.response(200, PaymentPlanSchema(many=True))
    def get(self,coach_profile_id):
        profile = CoachProfiles.query.get_or_404(coach_profile_id)
         
        plans = PaymentPlans.query.join(
            CoachProfiles,
            PaymentPlans.coach_profile_id == CoachProfiles.coach_profile_id
        ).filter(
            PaymentPlans.is_active == True,
            CoachProfiles.status == "approved",
            CoachProfiles.user_id == profile.user_id
        ).all()

        return plans




@client_blp.route("/hire-request")
class ClientHireRequestCreateView(MethodView):
    @jwt_required()
    @client_blp.arguments(HireRequestCreateSchema)
    @client_blp.response(201, HireRequestStatusSchema)
    def post(self, data):
        current_auth_id= get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()

        
        coach_profile_id = data["coach_profile_id"]
        payment_plan_id = data["payment_plan_id"]
        auto_pay_enabled = data.get("auto_pay_enabled", False)

        print(f"DEBUG: Processing request for User {user.user_id} -> Coach {coach_profile_id}")

        coach_profile = db.session.execute(
            select(CoachProfiles).where(
                CoachProfiles.coach_profile_id == coach_profile_id
            )
        ).scalar_one_or_none()

        if not coach_profile:
            abort(404, description="Coach profile not found")

        status_str = str(coach_profile.status).lower()
        if "approved" not in status_str:
            print(f"FAILED: Coach status is '{status_str}'")
            abort(400, description="Coach is not available")

        payment_plan = db.session.execute(
            select(PaymentPlans).where(
                PaymentPlans.payment_plan_id == payment_plan_id
            )
        ).scalar_one_or_none()

        if not payment_plan:
            abort(404, description="Payment plan not found")

        if payment_plan.coach_profile_id != coach_profile_id:
            abort(400, description="Invalid payment plan for this coach")

        existing_pending = db.session.execute(
            select(CoachHireRequests).where(
                CoachHireRequests.client_user_id == user.user_id,
                CoachHireRequests.coach_profile_id == coach_profile_id,
                CoachHireRequests.status == "pending"
            )
        ).scalar_one_or_none()

        if existing_pending:
            abort(409, description="Pending request already exists")

        new_request = CoachHireRequests(
            client_user_id=user.user_id,
            coach_profile_id=coach_profile_id,
            payment_plan_id=payment_plan_id,
            status="pending",
            auto_pay_enabled=auto_pay_enabled
        )

        create_notification(
                user_id=user.user_id,
                type_slug="coach-request",
                title="New Coach Hire",
                body=f"Your new requests has been received and the coach will be made aware"
            )

        try:
            db.session.add(new_request)
            db.session.commit()
            db.session.refresh(new_request) 
            print(f"SUCCESS: Created Request ID {new_request.request_id}")
            return new_request
        except Exception as e:
            db.sesssion.rollback()
            print(f"DATABASE ERROR: {str(e)}")
            abort(500, description="Internal database error")



@client_blp.route("/hire-request/<int:request_id>")
class ClientHireRequestDetailView(MethodView):
    @jwt_required()
    @client_blp.response(200, HireRequestStatusSchema)
    def delete(self, request_id):
        current_user =_current_user()

        hire_request = db.session.execute(
            select(CoachHireRequests).where(
                CoachHireRequests.request_id == request_id
            )
        ).scalar_one_or_none()

        if not hire_request:
            abort(404, description="Hire request not found")

        if int(hire_request.client_user_id) != int(current_user.user_id):
            abort(403, description="Not your request")

        current_status_str = hire_request.status.value

        
        if "pending" not in current_status_str:
            return {
                "message": f"Only pending requests can be canceled. Current: {current_status_str}"
            }, 400
        try:
            hire_request.status = StatusEnum.canceled

            create_notification(
                user_id=current_user.user_id,
                type_slug="coach-request-canceled",
                title="Cancel Coach Request",
                body=f"Your coach hire request has been canceled"
            )
            
            db.session.commit()
            print(f"SUCCESS: Request {request_id} set to canceled")
            return hire_request
        except Exception as e:
            db.session.rollback()
            print(f"COMMIT ERROR: {str(e)}")
            abort(500, description="Could not update status.")
    


@client_blp.route("/hire-requests")
class ClientHireRequestListView(MethodView):
    @jwt_required()
    @client_blp.response(200, HireRequestListSchema(many=True))
    def get(self):
        current_user= _current_user()
    
        requests = db.session.execute(
            select(CoachHireRequests)
            .where(CoachHireRequests.client_user_id == current_user.user_id)
            .order_by(CoachHireRequests.created_at.desc())
        ).scalars().all()

        print(requests)
        return requests

    



@client_blp.route("/hire-request/<int:request_id>/status")
class ClientHireRequestStatusView(MethodView):
    @jwt_required()
    @client_blp.response(200, HireRequestStatusSchema)
    def get(self, request_id):
        current_user_id = _current_user()

        hire_request = db.session.execute(
            select(CoachHireRequests).where(
                CoachHireRequests.request_id == request_id
            )
        ).scalar_one_or_none()

        if not hire_request:
            abort(404, description="Hire request not found")

        if int(hire_request.client_user_id) != int(current_user_id.user_id):
            #print(hire_request.client_user_id + " != " + current_user_id)
            abort(403, description="Not allowed ")

        return hire_request
    



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
        print(existing_review)

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
        
        reviews = CoachReviews.query.filter_by(client_user_id=user.user_id).all()
        
        # Add interaction counts and user's interaction to each review
        for review in reviews:
            # Get user's interaction for this review
            user_interaction = ReviewInteractions.query.filter_by(
                review_id=review.review_id, user_id=user.user_id
            ).first()
            review.user_interaction = user_interaction.interaction_type.value if user_interaction else None
        
        return reviews

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

### Coach Favorites Management
@client_blp.route("/favorites/coaches/<int:coach_id>")
class CoachFavoriteView(MethodView):

    @jwt_required()
    def post(self, coach_id):
        """Add coach to favorites"""
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()

        if not user:
            abort(404, description="User record not found.")

        coach = CoachProfiles.query.get(coach_id)
        if not coach:
            abort(404, description="Coach not found.")

        existing_favorite = CoachFavorites.query.filter_by(
            user_id=user.user_id,
            coach_profile_id=coach_id
        ).first()

        if existing_favorite:
            abort(400, description="Coach already favorited.")

        favorite = CoachFavorites(
            user_id=user.user_id,
            coach_profile_id=coach_id
        )

        db.session.add(favorite)

        try:
            db.session.commit()
            return {"message": "Coach added to favorites successfully"}
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))

    @jwt_required()
    def delete(self, coach_id):
        """Remove coach from favorites"""
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()

        if not user:
            abort(404, description="User record not found.")

        favorite = CoachFavorites.query.filter_by(
            user_id=user.user_id,
            coach_profile_id=coach_id
        ).first()

        if not favorite:
            abort(404, description="Favorite not found.")

        db.session.delete(favorite)

        try:
            db.session.commit()
            return {"message": "Coach removed from favorites successfully"}
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))


@client_blp.route("/favorites/coaches")
class FavoriteCoachesView(MethodView):

    @jwt_required()
    @client_blp.response(200, CoachProfileSchema(many=True) )
    def get(self):
        """Get user's favorite coaches"""
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()

        if not user:
            abort(404, description="User record not found.")

        favorites = CoachFavorites.query.filter_by(
            user_id=user.user_id
        ).all()

        coach_ids = [f.coach_profile_id for f in favorites]

        if not coach_ids:
            return []

        return CoachProfiles.query.filter(
            CoachProfiles.coach_profile_id.in_(coach_ids)
        ).all()


### Review Interactions
@client_blp.route("/reviews/<int:review_id>/interact")
class ReviewInteractionView(MethodView):

    @jwt_required()
    @client_blp.arguments({
        "interaction_type": {
            "type": "string",
            "required": True,
            "enum": ["helpful", "unhelpful"]
        }
    })
    def post(self, data, review_id):
        """Add or update helpful/unhelpful reaction"""
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()

        if not user:
            abort(404, description="User record not found.")

        review = CoachReviews.query.get(review_id)
        if not review:
            abort(404, description="Review not found.")

        interaction_type = data["interaction_type"]

        existing = ReviewInteractions.query.filter_by(
            review_id=review_id,
            user_id=user.user_id
        ).first()

        if existing:
            old_type = existing.interaction_type.value

            # undo old count
            if old_type == "helpful":
                review.helpful_count -= 1
            else:
                review.unhelpful_count -= 1

            existing.interaction_type = InteractionType(interaction_type)

        else:
            existing = ReviewInteractions(
                review_id=review_id,
                user_id=user.user_id,
                interaction_type=InteractionType(interaction_type)
            )
            db.session.add(existing)

        # apply new count
        if interaction_type == "helpful":
            review.helpful_count += 1
        else:
            review.unhelpful_count += 1

        try:
            db.session.commit()
            return {"message": "Interaction recorded successfully"}
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))

    @jwt_required()
    def delete(self, review_id):
        """Remove interaction from review"""
        current_auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=current_auth_id).first()

        if not user:
            abort(404, description="User record not found.")

        interaction = ReviewInteractions.query.filter_by(
            review_id=review_id,
            user_id=user.user_id
        ).first()

        if not interaction:
            return {"message": "No interaction found"}, 200

        review = CoachReviews.query.get(review_id)

        if interaction.interaction_type.value == "helpful":
            review.helpful_count -= 1
        else:
            review.unhelpful_count -= 1

        db.session.delete(interaction)

        try:
            db.session.commit()
            return {"message": "Interaction removed successfully"}
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
            
            
# <<<<<<< Coach-favorite-feature
# ### Coach Favorites Management
# @client_blp.route("/favorites/coaches/<int:coach_id>")
# class CoachFavoriteView(MethodView):
#     @jwt_required()
#     def post(self, coach_id):
#         """Add coach to favorites (uses coach's user_id)"""
# =======
# ### Review Interactions
# @client_blp.route("/reviews/<int:review_id>/interact")
# class ReviewInteractionView(MethodView):
#     @jwt_required()
#     @client_blp.arguments({"interaction_type": {"type": "string", "required": True, "enum": ["helpful", "unhelpful"]}})
#     def post(self, data, review_id):
#         """Add helpful/unhelpful reaction to review"""
# >>>>>>> develop
#         current_auth_id = get_jwt_identity()
#         user = Users.query.filter_by(auth_id=current_auth_id).first()
#         if not user:
#             abort(404, description="User record not found.")
        
# <<<<<<< Coach-favorite-feature
#         # Check if coach exists
#         coach = CoachProfiles.query.get(coach_id)
#         if not coach:
#             abort(404, description="Coach not found.")
        
#         # Check if already favorited
#         existing_favorite = CoachFavorites.query.filter_by(
#             user_id=user.user_id, coach_profile_id=coach_id
#         ).first()
        
#         if existing_favorite:
#             abort(400, description="Coach already favorited.")
        
#         # Add to favorites
#         favorite = CoachFavorites(
#             user_id=user.user_id,
#             coach_profile_id=coach_id
#         )
#         db.session.add(favorite)
        
#         try:
#             db.session.commit()
#             return {"message": "Coach added to favorites successfully"}
# =======
#         interaction_type = data['interaction_type']
        
#         # Check if review exists
#         review = CoachReviews.query.get(review_id)
#         if not review:
#             abort(404, description="Review not found.")
        
#         # Check if user already interacted
#         existing = ReviewInteractions.query.filter_by(
#             review_id=review_id, user_id=user.user_id
#         ).first()
        
#         if existing:
#             # Update existing interaction
#             old_type = existing.interaction_type.value
#             existing.interaction_type = InteractionType(interaction_type)
            
#             # Update counts based on change
#             if old_type == 'helpful':
#                 review.helpful_count -= 1
#             else:
#                 review.unhelpful_count -= 1
                
#             if interaction_type == 'helpful':
#                 review.helpful_count += 1
#             else:
#                 review.unhelpful_count += 1
#         else:
#             # Create new interaction
#             interaction = ReviewInteractions(
#                 review_id=review_id,
#                 user_id=user.user_id,
#                 interaction_type=InteractionType(interaction_type)
#             )
#             db.session.add(interaction)
            
#             # Update counts
#             if interaction_type == 'helpful':
#                 review.helpful_count += 1
#             else:
#                 review.unhelpful_count += 1
        
#         try:
#             db.session.commit()
#             return {"message": "Interaction recorded successfully"}
# >>>>>>> develop
#         except Exception as e:
#             db.session.rollback()
#             abort(500, description=f"Database error: {str(e)}")
    
#     @jwt_required()
# <<<<<<< Coach-favorite-feature
#     def delete(self, coach_id):
#         """Remove coach from favorites"""
# =======
#     def delete(self, review_id):
#         """Remove user's interaction from review"""
# >>>>>>> develop
#         current_auth_id = get_jwt_identity()
#         user = Users.query.filter_by(auth_id=current_auth_id).first()
#         if not user:
#             abort(404, description="User record not found.")
        
# <<<<<<< Coach-favorite-feature
#         favorite = CoachFavorites.query.filter_by(
#             user_id=user.user_id, coach_profile_id=coach_id
#         ).first()
        
#         if not favorite:
#             abort(404, description="Favorite not found.")
        
#         db.session.delete(favorite)
        
#         try:
#             db.session.commit()
#             return {"message": "Coach removed from favorites successfully"}
#         except Exception as e:
#             db.session.rollback()
#             abort(500, description=f"Database error: {str(e)}")

# @client_blp.route("/favorites/coaches")
# class FavoriteCoachesView(MethodView):
#     @jwt_required()
#     def get(self):
#         """Get user's favorite coaches"""
#         current_auth_id = get_jwt_identity()
#         user = Users.query.filter_by(auth_id=current_auth_id).first()
#         if not user:
#             abort(404, description="User record not found.")
        
#         # Get favorite coach IDs
#         favorite_coach_ids = db.session.query(CoachFavorites.coach_profile_id).filter_by(
#             user_id=user.user_id
#         ).all()
        
#         coach_ids = [fav[0] for fav in favorite_coach_ids]
        
#         if not coach_ids:
#             return []
        
#         # Get coach details
#         favorite_coaches = CoachProfiles.query.filter(
#             CoachProfiles.coach_profile_id.in_(coach_ids)
#         ).all()
        
#         return favorite_coaches
# =======
#         interaction = ReviewInteractions.query.filter_by(
#             review_id=review_id, user_id=user.user_id
#         ).first()
        
#         if interaction:
#             # Update counts
#             review = CoachReviews.query.get(review_id)
#             if interaction.interaction_type.value == 'helpful':
#                 review.helpful_count -= 1
#             else:
#                 review.unhelpful_count -= 1
            
#             db.session.delete(interaction)
            
#             try:
#                 db.session.commit()
#                 return {"message": "Interaction removed successfully"}
#             except Exception as e:
#                 db.session.rollback()
#                 abort(500, description=f"Database error: {str(e)}")
        
#         return {"message": "No interaction found to remove"}
# >>>>>>> develop
