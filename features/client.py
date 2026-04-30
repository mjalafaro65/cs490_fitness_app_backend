from flask import abort, request
from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from datetime import date
from schemas.client_schema import DailySurveySchema, ProfileSchema, HireRequestCreateSchema, HireRequestStatusSchema, HireRequestListSchema, ReviewCoachSchema, CreateGoalSchema, EditGoalSchema
from schemas.coach_schema import CoachProfileSchema
from models.coach_client_relationships import CoachClientRelationships, status_enum
from models.invoices import Invoices
from models.refund_disputes import StatusEnum_Disputes

from schemas.coach_schema import PaymentPlanSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select
from models import Users, Goals, PaymentMethods, Payments, Specialties
from models.coach_reports import CoachReports, StatusEnum
from models.daily_survey import DailySurvey
from models.review_interactions import InteractionType
from datetime import datetime, timezone
from schemas.invoice_schema import PayInvoiceSchema, CreateDisputeSchema, InitiateFireSchema, ConfirmTerminationSchema

from models.invoices import StatusEnumList
from models.payments import StatusEnum_Payments
from models.coach_hire_requests import StatusEnum
from models import ClientProfiles, PaymentPlans, CoachHireRequests, CoachProfiles, CoachReviews, CoachFavorites, ReviewInteractions, RefundDisputes, ClientProgressPhotos
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

        # TEMPORARILY DISABLED: Check if client has a relationship with the coach (active or terminated)
        # relationship = CoachClientRelationships.query.filter_by(
        #     coach_profile_id=coach_id,
        #     client_user_id=user.user_id
        # ).first()

        # if not relationship:
        #     abort(403, description="You can only review coaches you have hired or previously worked with.")

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
            print(f"Database error in review submission: {str(e)}")
            abort(500, description="Failed to submit review. Please try again.")

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

@client_blp.route("/create-goal")
class CreateGoalView(MethodView):
    @jwt_required()
    @client_blp.arguments(CreateGoalSchema)
    @client_blp.response(201, CreateGoalSchema)
    def post(self, data):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        goal = Goals(
            for_user_id=data['for_user_id'],
            created_by_user_id=user.user_id,
            goal_type=data['goal_type'],
            title=data['title'],
            target_value=data['target_value'],
            unit=data['unit'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            status=data['status'],
            description=data.get('description')
        )

        try:
            db.session.add(goal)
            db.session.commit()
            return goal
        except Exception as e:
            db.session.rollback()
            abort(500, description="Failed to create goal.")

@client_blp.route("/goal/<int:goal_id>")
class EditGoalView(MethodView):
    @jwt_required()
    @client_blp.arguments(EditGoalSchema)
    @client_blp.response(200, EditGoalSchema)
    def patch(self, data, goal_id):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            return {"message": "User not found"}, 404

        goal = Goals.query.get_or_404(goal_id)
        if goal.created_by_user_id != user.user_id and goal.for_user_id != user.user_id:
            abort(403, description="You do not have permission to edit this goal.")

        if data:
            for key, value in data.items():
                setattr(goal, key, value)
            goal.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return goal
        except Exception:
            db.session.rollback()
            abort(500, description="An error occurred while updating the goal.")



@client_blp.route("/invoices")
class ClientInvoiceList(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        client_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        query = (
            select(Invoices, Users.first_name, Users.last_name)
            .join(CoachClientRelationships, Invoices.relationship_id == CoachClientRelationships.relationship_id)
            .join(CoachProfiles, CoachClientRelationships.coach_profile_id == CoachProfiles.coach_profile_id)
            .join(Users, CoachProfiles.user_id == Users.user_id)
            .where(CoachClientRelationships.client_user_id == client_user.user_id)
            .order_by(Invoices.created_at.desc())
        )

        results = db.session.execute(query).all()

        return {
            "invoices": [
                {
                    "invoice_id": inv.invoice_id,
                    "coach_name": f"{fname} {lname}",
                    "amount": float(inv.subtotal),
                    "status": inv.status.value,
                    "created_at": inv.created_at.isoformat(),
                    "pay_date": inv.pay_date.isoformat() if inv.pay_date else None,
                    "is_payable": inv.status in [StatusEnumList.issued, StatusEnumList.past_due]
                } for inv, fname, lname in results
            ]
        }
    

@client_blp.route("/pay-invoice")
class PayInvoice(MethodView):
    @jwt_required()
    @client_blp.arguments(PayInvoiceSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        client_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        invoice = db.session.execute(
            select(Invoices)
            .join(CoachClientRelationships, Invoices.relationship_id == CoachClientRelationships.relationship_id)
            .where(
                Invoices.invoice_id == data["invoice_id"],
                CoachClientRelationships.client_user_id == client_user.user_id
            )
        ).scalar_one_or_none()

        if not invoice:
            abort(404, description="Invoice not found or unauthorized")
        if invoice.status == StatusEnumList.paid:
            return {"message": "Invoice already paid"}, 400

        input_last4 = data.get("last4")
        if input_last4:
            selected_card = PaymentMethods.query.filter_by(
                user_id=client_user.user_id,
                last4=input_last4,
                is_active=True
            ).first()
        else:
            selected_card = PaymentMethods.query.filter_by(
                user_id=client_user.user_id,
                is_default=True,
                is_active=True
            ).first()

        if not selected_card:
            abort(400, description="No valid active payment method found.")

        now_utc = datetime.now(timezone.utc)
        new_payment = Payments(
            invoice_id=invoice.invoice_id,
            payer_user_id=client_user.user_id,
            amount=invoice.subtotal,
            status="succeeded",
            is_auto_pay=False,
            provider=selected_card.provider, 
            provider_ref=selected_card.token, 
            created_at=now_utc,
            processed_at=now_utc
        )

        invoice.status = StatusEnumList.paid
        invoice.pay_date = now_utc
        invoice.payment_method_id = selected_card.payment_method_id

        db.session.add(new_payment)
        
        relationship = CoachClientRelationships.query.get(invoice.relationship_id)
        coach_profile = CoachProfiles.query.get(relationship.coach_profile_id)
        
        create_notification(
            user_id=coach_profile.user_id,
            type_slug="payment-received",
            title="Payment Received",
            body=f"Client {client_user.first_name} paid invoice #{invoice.invoice_id} for ${invoice.subtotal}."
        )

        db.session.commit()

        return {
            "message": "Payment successful",
            "provider": new_payment.provider,
            "provider_ref": new_payment.provider_ref,
            "amount": float(invoice.subtotal)
        }, 200
    

@client_blp.route("/my-payments")
class ClientPaymentList(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        payments = Payments.query.filter_by(payer_user_id=client.user_id).order_by(Payments.created_at.desc()).all()

        return {
            "payments": [
                {
                    "payment_id": p.payment_id,
                    "amount": float(p.amount),
                    "status": p.status.value,
                    "date": p.processed_at.isoformat() if p.processed_at else p.created_at.isoformat(),
                    "can_dispute": (datetime.utcnow() - p.created_at).days <= 7 # Policy: 7 days
                } for p in payments
            ]
        }
            

@client_blp.route("/dispute-payment")
class CreateDispute(MethodView):
    @jwt_required()
    @client_blp.arguments(CreateDisputeSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        payment = Payments.query.get_or_404(data["payment_id"])
        
        if payment.payer_user_id != client.user_id:
            abort(403, description="Unauthorized: This is not your payment record.")
        
        now = datetime.now(timezone.utc)
        pay_date = payment.created_at.replace(tzinfo=timezone.utc)
        days_diff = (now - pay_date).days
        
        if days_diff > 7:
            return {
                "message": "Policy Error: Disputes must be filed within 7 days of payment.",
                "days_since_payment": days_diff
            }, 400

        new_dispute = RefundDisputes(
            payment_id=payment.payment_id,
            opened_by_user_id=client.user_id,
            reason=data["reason"],
            status=StatusEnum_Disputes.open, 
            created_at=now
        )
        
        db.session.add(new_dispute)
        
        
        db.session.commit()

        return {
            "message": "Dispute submitted successfully.",
            "dispute_id": new_dispute.refund_dispute_id,
            "status": new_dispute.status.value
        }, 201
    

@client_blp.route("/my-coaches")
class ClientCoachList(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        results = db.session.execute(
            select(
                CoachClientRelationships.relationship_id, 
                Users.first_name, 
                Users.last_name, 
                Specialties.name.label("specialty_name"), 
                CoachClientRelationships.started_at,
                CoachClientRelationships.coach_profile_id
            )
            .join(CoachProfiles, CoachClientRelationships.coach_profile_id == CoachProfiles.coach_profile_id)
            .join(Users, CoachProfiles.user_id == Users.user_id)
            .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id)
            .where(
                CoachClientRelationships.client_user_id == client.user_id,
                CoachClientRelationships.status == status_enum.active
            )
            .distinct() 
        ).all()

        return {
            "active_relationships": [
                {
                    "relationship_id": r.relationship_id,
                    "coach_name": f"{r.first_name} {r.last_name}",
                    "specialty": r.specialty_name, 
                    "started_at": r.started_at.isoformat(),
                    "coach_profile_id": r.coach_profile_id
                } for r in results
            ]
        }
    

@client_blp.route("/initiate-fire-coach")
class InitiateFireCoach(MethodView):
    @jwt_required()
    @client_blp.arguments(InitiateFireSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        rel = CoachClientRelationships.query.filter_by(
            relationship_id=data["relationship_id"],
            client_user_id=client.user_id
        ).first_or_404()

        if rel.status != status_enum.active:
            return {
                "message": "This relationship is already inactive.",
                "status": "blocked"
            }, 400

        create_notification(
            user_id=client.user_id,
            type_slug="termination-warning",
            title="Termination Initiated",
            body=(
                "You have initiated the process to end your coaching relationship. "
                "Please confirm to finalize. Note: Access to training plans will be revoked "
                "and recurring billing will stop immediately upon confirmation."
            )
        )

        return {
            "warning": "Termination Warning",
            "consequences": [
                "Immediate loss of access to custom training plans.",
                "All future automated payments will be cancelled.",
                "Upcoming sessions will be removed from your schedule."
            ],
            "proceed_to_confirmation": True,
            "relationship_id": rel.relationship_id
        }
    


@client_blp.route("/confirm-fire-coach")
class ConfirmFireCoach(MethodView):
    @jwt_required()
    @client_blp.arguments(ConfirmTerminationSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        rel = CoachClientRelationships.query.filter_by(
            relationship_id=data["relationship_id"],
            client_user_id=client.user_id
        ).first_or_404()

        unpaid_invoices = Invoices.query.filter_by(
            relationship_id=rel.relationship_id,
            status=StatusEnumList.issued 
        ).all()

        for inv in unpaid_invoices:
            inv.status = StatusEnumList.voided

        rel.status = status_enum.terminated
        rel.termination_reason = data.get("reason")
        rel.ended_at = datetime.now(timezone.utc)

        db.session.commit()

        coach_profile = CoachProfiles.query.get(rel.coach_profile_id)
        
        create_notification(
            user_id=coach_profile.user_id,
            type_slug="relationship-terminated",
            title="Relationship Ended",
            body=f"Client {client.first_name} {client.last_name} has ended the coaching relationship. Any pending invoices have been voided."
        )

        create_notification(
            user_id=client.user_id,
            type_slug="termination-confirmed",
            title="Coach Fired Successfully",
            body="The relationship has been terminated and your pending billing for this coach was voided."
        )

        return {
            "message": "Termination processed successfully. Invoices voided.",
            "status": "terminated"
        }
    

@client_blp.route("/rehire-coach")
class RehireCoach(MethodView):
    @jwt_required()
    @client_blp.arguments(InitiateFireSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        old_rel = CoachClientRelationships.query.filter_by(
            relationship_id=data["relationship_id"],
            client_user_id=client.user_id,
            status=status_enum.terminated 
        ).first_or_404()

        coach_profile = CoachProfiles.query.get(old_rel.coach_profile_id)
        if not coach_profile:
            return {"message": "This coach is no longer available for rehire."}, 404

        old_rel.status = status_enum.active 
        old_rel.termination_reason = None 
        old_rel.ended_at = None
        
        db.session.commit()

        create_notification(
            user_id=coach_profile.user_id,
            type_slug="rehire",
            title="New Rehire",
            body=f"Your former client {client.first_name} {client.last_name} wants to work with you again!"
        )

        return {
            "message": "Rehire previously fired coach",
            "status": "pending"
        }
            
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

@client_blp.route("/progress-photos")
class ClientProgressPhotosView(MethodView):
    @jwt_required()
    def get(self):
        """
        Get client's progress photos
        """
        user = _current_user()
        
        progress_photos = ClientProgressPhotos.query.filter_by(client_id=user.user_id).first()
        
        if progress_photos:
            return {
                "before_photo_url": progress_photos.before_photo_url,
                "after_photo_url": progress_photos.after_photo_url
            }
        else:
            return {
                "before_photo_url": None,
                "after_photo_url": None
            }
    
    @jwt_required()
    def post(self):
        """
        Save or update client's progress photos
        """
        user = _current_user()
        data = request.get_json()
        
        before_url = data.get('before_photo_url')
        after_url = data.get('after_photo_url')
        
        progress_photos = ClientProgressPhotos.query.filter_by(client_id=user.user_id).first()
        
        if progress_photos:
            # Update existing record
            if before_url is not None:
                progress_photos.before_photo_url = before_url
            if after_url is not None:
                progress_photos.after_photo_url = after_url
            progress_photos.updated_at = datetime.utcnow()
        else:
            # Create new record
            progress_photos = ClientProgressPhotos(
                client_id=user.user_id,
                before_photo_url=before_url,
                after_photo_url=after_url
            )
            db.session.add(progress_photos)
        
        try:
            db.session.commit()
            return {"message": "Progress photos saved successfully"}
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error: {str(e)}")
