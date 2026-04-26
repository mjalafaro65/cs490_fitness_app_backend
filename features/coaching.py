from datetime import datetime
from operator import or_
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos, Roles, CoachDocuments, DailySurvey, WorkoutPlanAssignments, MealPlanAssignments, CoachFavorites, CoachHireRequests, PaymentPlans, CoachClientRelationships, PaymentMethods, Invoices, CoachAvailability, WorkoutPlans, WorkoutPlanDays, WorkoutPlanDayExercises, Exercises
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, not_, select, desc
from schemas.coach_schema import CoachProfileSchema, CoachProfileQuerySchema, CoachDocumentSchema, CoachBrowsingSchema, ManageClientSchema, SpecialtySchema , AssignWorkoutPlanSchema, AssignMealPlanSchema, FavoriteCoachSchema, CoachBrowsingQuery, CoachAvailabilitySchema, ClientDashboardSchema, ClientListSchema, ClientWorkoutPlanCreateSchema, ClientWorkoutPlanSchema, ClientWorkoutAssignmentsSchema, WeeklyWorkoutDaySchema
from schemas.client_schema import ReviewCoachSchema, DailySurveySchema, HireRequestStatusSchema
from schemas.invoice_schema import CreateInvoiceSchema, UpdateInvoiceStatusSchema

from models.coach_hire_requests import StatusEnum
from models.invoices import StatusEnumList
from models.coach_profiles import ApprovalStatusEnum
from models.coach_client_relationships import status_enum
from .utils import create_notification
from datetime import datetime, timezone
from .conversation_services import create_conversation



# Import your schema
from schemas.coach_schema import CoachProfileSchema

coach_blp = Blueprint("Coach", __name__, url_prefix="/coach", description="Coach feat")

@coach_blp.route("/top-coach")
class TopCoach(MethodView):
    def get(self):
        """Get top coaches and reviews (filtered by APPROVED status)"""
        rating_stmt = (
            select(
                CoachReviews.coach_profile_id,
                func.avg(CoachReviews.rating).label("avg_rating"),
                func.count(CoachReviews.review_id).label("total_reviews")
            )
            .group_by(CoachReviews.coach_profile_id)
            .subquery()
        )
        
        stmt = (
            select(
                Users.user_id,
                Users.first_name,
                Users.last_name,
               func.max(CoachProfiles.bio).label("bio"),
        func.max(CoachProfiles.profile_photo).label("profile_photo"),
        Specialties.name.label("specialty_name"),
        func.max(CoachProgressPhotos.before_photo_url).label("before_photo_url"),
        func.max(CoachProgressPhotos.after_photo_url).label("after_photo_url"),
        func.max(CoachProgressPhotos.description).label("transformation_desc"),
        rating_stmt.c.avg_rating,
        rating_stmt.c.total_reviews
    )
    .join(CoachProfiles, Users.user_id == CoachProfiles.user_id) 
    .join(CoachProgressPhotos, CoachProfiles.coach_profile_id == CoachProgressPhotos.coach_profile_id)
    .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id)
    .join(rating_stmt, CoachProfiles.coach_profile_id == rating_stmt.c.coach_profile_id)
    .join(UserRoles, Users.auth_id == UserRoles.user_id)
    .filter(UserRoles.role_id == 2)
    .filter(CoachProfiles.status == 'approved') 
    # Group by the main identity columns
    .group_by(
        Users.user_id, 
        Users.first_name, 
        Users.last_name, 
        Specialties.name, 
        rating_stmt.c.avg_rating, 
        rating_stmt.c.total_reviews
    )
    .order_by(desc(rating_stmt.c.avg_rating), desc(rating_stmt.c.total_reviews))
    .limit(3)
)

        try:
            result = db.session.execute(stmt).all()

            top_coaches = [
                {
                    "user_id": row.user_id,
                    "name": f"{row.first_name} {row.last_name}",
                    "specialty": row.specialty_name,
                    "bio": row.bio,
                    "image": row.profile_photo,
                    "rating": float(round(row.avg_rating, 1)) if row.avg_rating else 0,
                    "before-photo": row.before_photo_url,
                    "after-photo": row.after_photo_url,
                    "photo-description": row.transformation_desc
                }
                for row in result
            ]

            return {"coaches": top_coaches}, 200

        except Exception as e:
            abort(500, description=f"Failed to fetch coaches: {str(e)}")

# @coach_blp.route("/profile")
# class CoachProfileView(MethodView):
#     @jwt_required()
#     @coach_blp.response(200, CoachProfileSchema)
#     def get(self):
#         """Retrieve the authenticated coach's profile details."""
#         auth_id = get_jwt_identity()
#         user = Users.query.filter_by(auth_id=auth_id).first()
        
#         if not user:
#             abort(404, description="User not found.")

#         profile = CoachProfiles.query.filter_by(user_id=user.user_id).first()
#         if not profile:
#             abort(404, description="Coach profile not found. Please complete setup first.")
            
#         return profile

#     @jwt_required()
#     @coach_blp.arguments(CoachProfileSchema)
#     @coach_blp.response(200, CoachProfileSchema)
#     def put(self, data):
#         """Update existing coach profile fields only."""
#         auth_id = get_jwt_identity()
#         user = Users.query.filter_by(auth_id=auth_id).first()
        
#         if not user:
#             abort(404, description="User not found.")

#         profile = CoachProfiles.query.filter_by(user_id=user.user_id).first()
        
#         # Refactored: No longer creates profile; only updates.
#         if not profile:
#             abort(400, description="Coach profile not found. Use /auth
# to create your profile.")

#         # Update fields dynamically
#         for key, value in data.items():
#             setattr(profile, key, value)

#         try:
#             db.session.commit()
#             return profile
#         except Exception as e:
#             db.session.rollback()
#             abort(500, description=f"Database error during update: {str(e)}")

@coach_blp.route("/specialties")
class InitSpecialties(MethodView):
    def post(self):
        """Initialize specialties in the database."""
        try:
            specialties_data = [
                {"name": "Physical Training", "type": "workout"},
                {"name": "Nutritional Coaching", "type": "nutrition"}
            ]
            
            for item in specialties_data:
                exists = Specialties.query.filter_by(name=item["name"]).first()
                if not exists:
                    new_spec = Specialties(
                        name=item["name"], 
                        coach_type=item["type"] # Ensure your Model uses 'coach_type'
                    )
                    db.session.add(new_spec)
            
            db.session.commit()
            return {"message": "Specialties initialized successfully."}, 201
            
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Failed to initialize specialties: {str(e)}")

    @coach_blp.response(200, SpecialtySchema(many=True))
    def get (sef):
        """Get all specialties"""
        specialties=db.session.execute(select(Specialties)).scalars().all()

        return specialties


@coach_blp.route("/coach-profile")
class CoachProfileView(MethodView):
    @jwt_required(optional=True)
    @coach_blp.arguments(CoachProfileQuerySchema, location="query")
    @coach_blp.response(200, CoachProfileSchema)
    def get(self,args):
        """
        Get coach profile.
        Coach: Calls /coach-profile (gets their own).
        Admin/Client: Calls /coach-profile?user_id=10 (gets specific user).
        """
        curr_auth_id = get_jwt_identity()


        if curr_auth_id:
            result = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).first()
            curr_user_id = result[0] if result else None
        else:
            curr_user_id=None            

       
        target_user_id = args.get("user_id")

        if not target_user_id and not curr_auth_id:
            return {"message": "user_id not obtained"}, 404

        #if target id is provided check if its the logged in user
        #######need to check if its admin or client doing the call
        if target_user_id and target_user_id != curr_user_id:
            
            profile = CoachProfiles.query.filter_by(user_id=target_user_id).first()
        
        else:
            profile = CoachProfiles.query.filter_by(user_id=curr_user_id).first()
        
        print(profile)

        if not profile:
            return {"message":"Coach profile not found."}, 404
        
        return profile
    
    
    @jwt_required()
    @coach_blp.arguments(CoachProfileSchema(load_instance=False, exclude=("status",)))
    @coach_blp.response(201, CoachProfileSchema)
    def post(self,data):
        """
        Initial Application: Client creates a coach profile with status 'pending'.
        """
        curr_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).scalar()

        if CoachProfiles.query.filter_by(user_id=curr_user_id).first():
           abort(400, message="A profile already exists for this user.")
        
        try:
            profile = CoachProfiles(**data, user_id=curr_user_id, status=ApprovalStatusEnum.pending)
            db.session.add(profile)

            create_notification(
                role_id=3,
                type_slug="coach-application",
                title="New Coach Application",
                body=f"A new profile has been submitted for review by user ID: {curr_user_id}"
            )

            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Database Error: {str(e)}") 
            abort(500, description="Database error occurred during profile creation.") 
    
    @jwt_required()
    @coach_blp.arguments(CoachProfileQuerySchema, location="query")
    @coach_blp.arguments(CoachProfileSchema(partial=True,load_instance=False))
    @coach_blp.response(200, CoachProfileSchema)
    def patch(self , query_args,updated_data):
        """
        Update existing profile. partial=True allows updating just one field.
        """
        curr_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).scalar()


        #look at role
        is_admin = db.session.query(UserRoles).join(Roles).filter(
                UserRoles.user_id == curr_auth_id,
                Roles.name == 'admin'
        ).first() is not None
        
       
        
        target_user_id = query_args.get("user_id") 
        if target_user_id is None:
            target_user_id = curr_user_id
            
            
        #if its not user or admin 
        if target_user_id != curr_user_id and not is_admin:
            abort(403, description="Unauthorized to edit this profile.")

        profile = CoachProfiles.query.filter_by(user_id=target_user_id).first_or_404()    

        #field coach cant change 
        restricted_fields = [
            "is_flagged",
            "flagged_at",
            "approved_at",
            "flagged_by_admin_user_id",
            "approved_by_admin_user_id",
            "created_at",
            "updated_at"
        ]
        

        for key, value in updated_data.items():
            # if  coach tries to change a restricted field, just ignore it
            
            if key == "status":
                current_status_upper = profile.status.lower()
                new_val = value.lower() if isinstance(value, str) else value
                if is_admin:
                    setattr(profile, key, value)
                    
                    if new_val == ApprovalStatusEnum.approved:
                        profile.approved_at = datetime.utcnow()
                        profile.approved_by_admin_user_id = curr_user_id
                        
                        create_notification(
                            user_id=profile.user_id,
                            type_slug="admin-approval",
                            title="Application Approved!",
                            body="Congratulations! Your coach profile is now live."
                        )
                elif new_val == ApprovalStatusEnum.switched or current_status_upper == ApprovalStatusEnum.switched:
                    setattr(profile, key, value)
                    
                else:
                    continue


            #handle other admin-Only fields
            elif key in restricted_fields:
                if is_admin:
                    setattr(profile, key, value)
                    create_notification(
                        user_id=profile.user_id,
                        type_slug="system-alert",
                        title="Profile Update",
                        body=f"An administrator has updated your profile status to: {value}."
                    )
                else:
                    continue
            #handle general fields (bio, experience, photo, specialty)
            else:
                setattr(profile, key, value)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(500, description="Database error occurred.")

        return profile


@coach_blp.route("/coach-profile/documents")
class CoachDocumentView(MethodView):
    @jwt_required()
    @coach_blp.arguments(CoachDocumentSchema(many=True))
    # @coach_blp.response(201, CoachDocumentSchema(many=True))
    def post(self, data):
        """
        Post coach document 
        """
        #get user id 
        curr_auth_id = get_jwt_identity()

        stmt = (
            select(CoachProfiles)
            .join(Users, CoachProfiles.user_id == Users.user_id)
            .filter(Users.auth_id == curr_auth_id)
        )
        profile = db.session.execute(stmt).scalar_one_or_none()
        
        if not profile:
            abort(404, message=f"No Profile found for AuthID: {curr_auth_id}")
        
        for doc in data:
            new_doc = CoachDocuments(
                document_type=doc['document_type'],
                document_url=doc['document_url'],
                coach_profile_id=profile.coach_profile_id
            )
            db.session.add(new_doc)
        
        db.session.commit()  

        return {"message":"Documents uploaded successfully"},200
    
    @jwt_required()
    @coach_blp.response(200, CoachDocumentSchema(many=True))
    def get(self):
        """
        Get list of documents from coach by coach 
        """
        curr_auth_id = get_jwt_identity()

        return CoachDocuments.query.join(CoachProfiles)\
            .join(Users, CoachProfiles.user_id == Users.user_id)\
            .filter(Users.auth_id == curr_auth_id).all()


@coach_blp.route("/coach-profile/documents/<int:doc_id>")
class CoachDocumentDetailView(MethodView):
    @jwt_required()
    @coach_blp.response(200, CoachDocumentSchema)
    def get(self, doc_id):
        """
        Get the details of ONE specific document. Used by admin and coach
        """

        curr_auth_id = get_jwt_identity()

        stmt = (
            select(CoachDocuments)
            .join(CoachProfiles)
            .join(Users, CoachProfiles.user_id == Users.user_id)
            .filter(
                Users.auth_id == curr_auth_id,
                CoachDocuments.document_id == doc_id
            )
        )
        
        result = db.session.execute(stmt).scalar()
        
        if not result:
            abort(404, description="Document not found or access denied.")
            
        return result
    
    @jwt_required()
    @coach_blp.arguments(CoachDocumentSchema) 
    @coach_blp.response(200, CoachDocumentSchema)
    def patch(self, update_data, doc_id):
        """
        Update a specific document (example--Coach updating a URL) by coach 
        """
        curr_auth_id = get_jwt_identity()

        #Find the document and verify ownership
        stmt = (
            select(CoachDocuments)
            .join(CoachProfiles)
            .join(Users, CoachProfiles.user_id == Users.user_id)
            .filter(
                Users.auth_id == curr_auth_id,
                CoachDocuments.document_id == doc_id
            )
        )
        document = db.session.execute(stmt).scalar()

        if not document:
            abort(404, description="Document not found or access denied.")

        #Apply the updates
        if 'document_url' in update_data:
            document.document_url = update_data['document_url']
        if 'document_type' in update_data:
            document.document_type = update_data['document_type']
            
        # Reset status to pending if they update the file
        document.status = "pending" 

        db.session.commit()
        return document

    @jwt_required()
    def delete(self, doc_id):
        """
        Delete one specific document. 
        """

        curr_auth_id = get_jwt_identity()

        #Find the document and verify ownership in one query
        stmt = (
            select(CoachDocuments)
            .join(CoachProfiles)
            .join(Users, CoachProfiles.user_id == Users.user_id)
            .filter(
                Users.auth_id == curr_auth_id,
                CoachDocuments.document_id == doc_id
            )
        )
        document = db.session.execute(stmt).scalar()

        #If not found or not theirs
        if not document:
            abort(404, description="Document not found or access denied.")

        
        db.session.delete(document)
        db.session.commit()

        # Return success message 
        return {"message": f"Document {doc_id} has been deleted."}, 200


@coach_blp.route("/coachbrowse")
class CoachBrowse(MethodView):
    @coach_blp.response(200, CoachBrowsingSchema(many=True))
    def get(self):
        results = db.session.query(
            CoachProfiles.coach_profile_id,
            Users.first_name,
            Users.last_name,
            Users.user_id,
            Specialties.name.label("specialty_name"),
            CoachProfiles.years_experience,
            CoachProfiles.bio,
             CoachProfiles.profile_photo
        ).join(Users, CoachProfiles.user_id == Users.user_id) \
        .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id) \
        .filter( or_(
        CoachProfiles.status == ApprovalStatusEnum.approved,
        CoachProfiles.status == ApprovalStatusEnum.switched
            )
                ) \
        .all()

        return results


# # Filter for type of coach
# @coach_blp.route("/coachbrowse/filter")
# class CoachBrowseFilter(MethodView):
#     @coach_blp.arguments(CoachBrowsingQuery, location="query")
#     @coach_blp.response(200, CoachBrowsingSchema(many=True))
#     def get(self, args):
#         specialty_id = args.get("specialty_id")

#         query = db.session.query(
#             CoachProfiles.coach_profile_id,
#             Users.first_name,
#             Users.last_name,
#             Specialties.name.label("specialty_name"),
#             CoachProfiles.years_experience,
#             CoachProfiles.bio
#         ).join(Users, CoachProfiles.user_id == Users.user_id) \
#         .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id) \
#         .filter(CoachProfiles.status == ApprovalStatusEnum.approved) 
        

#         if specialty_id:
#             query = query.filter(CoachProfiles.specialty_id == specialty_id)

#         results = query.all()
#         return results


@coach_blp.route("/coachbrowse/filters")
class CoachBrowseFilter(MethodView):
    """
        Searching based on arguments bellow
    """

    @coach_blp.arguments(CoachBrowsingQuery, location="query")
    @coach_blp.response(200, CoachBrowsingSchema(many=True))
    def get(self, query_args):

        specialty_id = query_args.get("specialty_id")
        min_price = query_args.get("min_price")
        max_price = query_args.get("max_price")
        day_of_week = query_args.get("day_of_week")

        query = db.session.query(
            CoachProfiles.coach_profile_id,
            Users.first_name,
            Users.last_name,
            Users.user_id, 
            Specialties.name.label("specialty_name"),
            CoachProfiles.years_experience,
            CoachProfiles.bio,
            CoachProfiles.profile_photo
        )\
        .join(Users, CoachProfiles.user_id == Users.user_id)\
        .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id)\
        .outerjoin(PaymentPlans)\
        .outerjoin(CoachAvailability)\
        .filter(CoachProfiles.status == ApprovalStatusEnum.approved)

        if min_price is not None:
            query = query.filter(PaymentPlans.amount >= min_price)

        if max_price is not None:
            query = query.filter(PaymentPlans.amount <= max_price)

        if day_of_week is not None:
            query = query.filter(CoachAvailability.day_of_week == day_of_week)

        if specialty_id:
            query = query.filter(CoachProfiles.specialty_id == specialty_id)

        return query.distinct().all()
        

        
@coach_blp.route("/coach/availability")
class CoachAvailabilityView(MethodView):

    @jwt_required()
    @coach_blp.arguments(CoachAvailabilitySchema)
    @coach_blp.response(201, CoachAvailabilitySchema)
    def post(self, data):
        """
        Coach sets their availability
        """
        curr_auth_id = 20

        user = Users.query.filter_by(auth_id=curr_auth_id).first()
        if not user:
            abort(401, description="User not found")

        coach = CoachProfiles.query.filter_by(user_id=user.user_id).first()
        if not coach:
            abort(404, description="Coach profile not found")

        day_of_week = data["day_of_week"]
        start_time = data["start_time"]
        end_time = data["end_time"]

        if start_time >= end_time:
            abort(400, description="Start time must be before end time")

        if day_of_week < 0 or day_of_week > 6:
            abort(400, description="day_of_week must be 0–6")
        
        
        overlap = CoachAvailability.query.filter(
            CoachAvailability.coach_profile_id == coach.coach_profile_id,
            CoachAvailability.day_of_week == day_of_week,
            not_(
                or_(
                    end_time <= CoachAvailability.start_time,
                    start_time >= CoachAvailability.end_time
                )
            )
        ).first()
        if overlap:
            abort(400, description="Time slot overlaps with existing availability")

        availability = CoachAvailability(
            coach_profile_id=coach.coach_profile_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )

        db.session.add(availability)
        db.session.commit()

        return availability
    

    @jwt_required()
    @coach_blp.response(200, CoachAvailabilitySchema(many=True))
    def get(self):
        curr_auth_id =get_jwt_identity()

        user = Users.query.filter_by(auth_id=curr_auth_id).first()
        if not user:
            abort(401, description="User not found")

        coach = CoachProfiles.query.filter_by(user_id=user.user_id).first()
        if not coach:
            abort(404, description="Coach profile not found")

        availability = CoachAvailability.query.filter_by(
            coach_profile_id=coach.coach_profile_id
        ).all()

        return availability

@coach_blp.route("/coach/availability/<int:availability_id>")
class CoachAvailabilityEditView(MethodView):

    @jwt_required()
    @coach_blp.arguments(CoachAvailabilitySchema)
    @coach_blp.response(200, CoachAvailabilitySchema)
    def put(self, data, availability_id):
        """
        VCoach updates their availability
        """

        user = Users.query.filter_by(auth_id=get_jwt_identity()).first()
        coach = CoachProfiles.query.filter_by(user_id=user.user_id).first()

        availability = CoachAvailability.query.filter_by(
            availability_id=availability_id,
            coach_profile_id=coach.coach_profile_id
        ).first()

        if not availability:
            abort(404, description="Not found")

        start_time = data["start_time"]
        end_time = data["end_time"]

        if end_time <= start_time:
            abort(400, description="End time must be after start time")

        # update only if valid
        availability.day_of_week = data["day_of_week"]
        availability.start_time = start_time
        availability.end_time = end_time

        db.session.commit()

        return availability
        
    @jwt_required()
    def delete(self, availability_id):

        user = Users.query.filter_by(auth_id=get_jwt_identity()).first()
        coach = CoachProfiles.query.filter_by(user_id=user.user_id).first()

        availability = CoachAvailability.query.filter_by(
            availability_id=availability_id,
            coach_profile_id=coach.coach_profile_id
        ).first()

        if not availability:
            abort(404, description="Not found")

        db.session.delete(availability)
        db.session.commit()

        return {"message": "Deleted successfully"}


    
@coach_blp.route("/coach/<int:coach_profile_id>/availability")
class CoachAvailabilityPublicView(MethodView):
     

    @coach_blp.response(200, CoachAvailabilitySchema(many=True))
    def get(self, coach_profile_id):
        """
        Visitor gets coach availability
        """

        availability = CoachAvailability.query.filter_by(
            coach_profile_id=coach_profile_id
        ).all()

        if not availability:
            return []

        return availability

        



### Coach Recommendation
### Recommends based on goal type
""" 
Goal types are enums and specialty_ids are ints so some jury rigging 
is required to compare them.
# Specialty_id
# 1 = weight
# 2 = strength
# 3 = performance
# 4 = nutrition
# 5 = mobility
# 6 = consistency
# 7 = recovery
# 8 = custom

# goal_type enums
weight
strength
performance
nutrition
mobility
consistency
recovery
custom

"""


@coach_blp.route("/coachrecommendations")
class CoachRecommendations(MethodView):
    @jwt_required()
    @coach_blp.response(200, CoachBrowsingSchema(many=True))
    def get(self):
        current_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=current_auth_id).scalar()
        if not curr_user_id:
            abort(404, description="User not found.")
        
        goal_to_specialty_map = {
            "weight": 1,
            "strength": 2,
            "performance": 3,
            "nutrition": 4,
            "mobility": 5,
            "consistency": 6,
            "recovery": 7,
            "custom": 8
        }

        latest_survey = (
            DailySurvey.query
            .filter_by(client_id=curr_user_id)
            .order_by(DailySurvey.date.desc())
            .first()
        )

        query = db.session.query(
            CoachProfiles.coach_profile_id,
            Users.first_name,
            Users.last_name,
            Specialties.name.label("specialty_name"),
            CoachProfiles.years_experience,
            CoachProfiles.bio
        ).join(Users, CoachProfiles.user_id == Users.user_id) \
         .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id)

        if latest_survey and latest_survey.goal_type:
            target_specialty_id = goal_to_specialty_map.get(latest_survey.goal_type.name)
            
            if target_specialty_id:
                query = query.filter(CoachProfiles.specialty_id == target_specialty_id)

        return query.all()
        




@coach_blp.route("/assign-workout/plan")
class AssignWorkoutPlan(MethodView):
    @jwt_required()
    @coach_blp.arguments(AssignWorkoutPlanSchema)
    @coach_blp.response(200, AssignWorkoutPlanSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        coach_profile = CoachProfiles.query.filter_by(user_id=coach_user.user_id).first()
        if not coach_profile:
            abort(403, description="Only registered coaches can assign workout plans.")

        plan_id = data['plan_id']
        client_id = data['assigned_to_client_id']

        assign = WorkoutPlanAssignments(
            plan_id=plan_id,
            assigned_to_client_id=client_id,
            assigned_by_coach_id=coach_profile.coach_profile_id,
            repeat_rules=data['repeat_rules'],
            status=data['status'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            created_at=datetime.utcnow()
        )

        try:
            db.session.add(assign)
            db.session.commit()
            return assign
        except Exception as e:
            db.session.rollback()
            abort(500, description="Failed to assign workout plan.")

@coach_blp.route("/assign-meal/plan")
class AssignMealPlan(MethodView):
    @jwt_required()
    @coach_blp.arguments(AssignMealPlanSchema)
    @coach_blp.response(200, AssignMealPlanSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()

        coach_profile = CoachProfiles.query.filter_by(user_id=coach_user.user_id).first()
        if not coach_profile:
            abort(403, description="Only registered coaches can assign meal plans.")

        plan_id = data['meal_plan_id']
        client_id = data['user_id']

        assign = MealPlanAssignments(
            meal_plan_id=plan_id,
            user_id=client_id,
            assigned_by_user_id=coach_profile.coach_profile_id,
            repeat_rule=data['repeat_rule'],
            status=data['status'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            created_at=datetime.utcnow()
        )

        try:
            db.session.add(assign)
            db.session.commit()
            return assign
        except Exception as e:
            db.session.rollback()
            abort(500, description="Failed to assign meal plan.")
  
@coach_blp.route("/<int:coach_id>/reviews")       
class CoachReviewsPublic(MethodView):

    @coach_blp.response(200, ReviewCoachSchema(many=True))
    def get(self, coach_id):
        return CoachReviews.query.filter_by(
            coach_profile_id=coach_id
        ).all()
    

@coach_blp.route("/pending-requests")
class CoachPendingRequestsView(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        coach_profile = db.session.execute(
            select(CoachProfiles).where(CoachProfiles.user_id == coach_user.user_id)
        ).scalar_one_or_none()

        if not coach_profile:
            abort(404, description="Coach profile not found")

        results = db.session.execute(
            select(
                CoachHireRequests, 
                PaymentPlans.name, 
                PaymentPlans.billing_type
            )
            .join(PaymentPlans, CoachHireRequests.payment_plan_id == PaymentPlans.payment_plan_id)
            .where(
                CoachHireRequests.coach_profile_id == coach_profile.coach_profile_id,
                CoachHireRequests.status == StatusEnum.pending
            )
        ).all()

        return [{
            "request_id": row.CoachHireRequests.request_id,
            "client_user_id": row.CoachHireRequests.client_user_id,
            "status": row.CoachHireRequests.status.value,
            "created_at": row.CoachHireRequests.created_at.isoformat(),
            "plan_name": row.name,          
            "billing_type": row.billing_type.value 
        } for row in results]
            


@coach_blp.route("/hire-request/<int:request_id>")
class CoachHireRequestDetailView(MethodView):
    @jwt_required()
    def get(self, request_id):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        coach_profile = db.session.execute(
            select(CoachProfiles).where(CoachProfiles.user_id == coach_user.user_id)
        ).scalar_one_or_none()

        result = db.session.execute(
            select(
                CoachHireRequests, 
                Users.first_name, 
                Users.last_name, 
                Users.phone_number, 
                Users.is_active,
                PaymentPlans.name,
                PaymentPlans.billing_type
            )
            .join(Users, CoachHireRequests.client_user_id == Users.user_id)
            .join(PaymentPlans, CoachHireRequests.payment_plan_id == PaymentPlans.payment_plan_id)
            .where(
                CoachHireRequests.request_id == request_id,
                CoachHireRequests.coach_profile_id == coach_profile.coach_profile_id
            )
        ).first()

        if not result:
            abort(403, description="Request not found or access denied")

        return {
            "request_id": result.CoachHireRequests.request_id,
            "client_name": f"{result.first_name} {result.last_name}",
            "phone_number": result.phone_number,
            "client_is_active": result.is_active,
            "plan_name": result.name,
            "billing_type": result.billing_type.value,
            "status": result.CoachHireRequests.status.value,
            "created_at": result.CoachHireRequests.created_at.isoformat()
        }
    


@coach_blp.route("/hire-request/<int:request_id>/accept")
class CoachAcceptHireRequest(MethodView):
    @jwt_required()
    def post(self, request_id):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        coach_profile = db.session.execute(
            select(CoachProfiles).where(CoachProfiles.user_id == coach_user.user_id)
        ).scalar_one_or_none()

        hire_request = db.session.execute(
            select(CoachHireRequests).where(
                CoachHireRequests.request_id == request_id,
                CoachHireRequests.coach_profile_id == coach_profile.coach_profile_id
            )
        ).scalar_one_or_none()

        if not hire_request:
            abort(404, description="Hire request not found")

        if hire_request.status != StatusEnum.pending:
            abort(400, description="Request is no longer pending")


        hire_request.status = StatusEnum.accepted
        hire_request.decided_at = db.func.now()

        new_relationship = CoachClientRelationships(
            coach_profile_id=hire_request.coach_profile_id,
            client_user_id=hire_request.client_user_id,
            payment_plan_id=hire_request.payment_plan_id,
            status="active", 
            started_at=db.func.now()
        )
        
        db.session.add(new_relationship)
        
        db.session.flush()
        
        
        #create conversation
        create_conversation(
            participant_ids=[
                hire_request.client_user_id,
                coach_profile.user_id
            ],
            conversation_type="relationship",
            relationship_id=new_relationship.relationship_id
        )
        

        create_notification(
                user_id=hire_request.client_user_id,
                type_slug="coach-request-accepted",
                title="Accepted Coach Request",
                body=f"Your coach hire request has been canceled"
            )
        
        
        db.session.commit()


        return {
            "message": "Client accepted and relationship activated",
            "relationship_id": new_relationship.relationship_id
        }
    

@coach_blp.route("/hire-request/<int:request_id>/deny")
class CoachDenyHireRequest(MethodView):
    @jwt_required()
    def post(self, request_id):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        coach_profile = db.session.execute(
            select(CoachProfiles).where(CoachProfiles.user_id == coach_user.user_id)
        ).scalar_one_or_none()

        hire_request = db.session.execute(
            select(CoachHireRequests).where(
                CoachHireRequests.request_id == request_id,
                CoachHireRequests.coach_profile_id == coach_profile.coach_profile_id
            )
        ).scalar_one_or_none()

        if not hire_request or hire_request.status != StatusEnum.pending:
            abort(400, description="Request cannot be denied (already processed or not found)")

        hire_request.status = StatusEnum.denied
        hire_request.decided_at = db.func.now()
        
        db.session.commit()

        create_notification(
            user_id=hire_request.client_user_id,
            type_slug="coach-request-denied",
            title="Request Denied",
            body=f"Coach {coach_user.first_name} is unable to take on new clients at this time. Your request has been declined."
        )

        return {
            "message": "Coach denied request",
            "request_id": hire_request.request_id
        }
    



@coach_blp.route("/show-client-relationships")
class CoachActiveRosterView(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        coach_profile = db.session.execute(
            select(CoachProfiles).where(CoachProfiles.user_id == coach_user.user_id)
        ).scalar_one_or_none()
        
        if not coach_profile:
            return []

        results = db.session.execute(
            select(
                CoachClientRelationships.relationship_id,
                CoachClientRelationships.status,
                Users.user_id, 
                Users.first_name, 
                Users.last_name, 
                PaymentPlans.payment_plan_id,
                PaymentPlans.name, 
                PaymentPlans.billing_type
            )
            .join(Users, CoachClientRelationships.client_user_id == Users.user_id)
            .join(PaymentPlans, CoachClientRelationships.payment_plan_id == PaymentPlans.payment_plan_id)
            .where(
                CoachClientRelationships.coach_profile_id == coach_profile.coach_profile_id,
            )
        ).all()

        active_roster = []
        for row in results:
            active_roster.append({
               
                    "relationship_id": row.relationship_id,
                    "user": {
                        "user_id": row.user_id,
                        "first_name": row.first_name,
                        "last_name": row.last_name,
                    },
                    "plan": {
                        "plan_id": row.payment_plan_id,
                        "name": row.name,
                        "billing_type": row.billing_type.value
                    },
                    "status": row.status.value
                
            })

        return active_roster
    


@coach_blp.route("/manage-client")
class CoachManageClientStatus(MethodView):
    @jwt_required()
    @coach_blp.arguments(ManageClientSchema) 
    def post(self, data):
        rel_id = data.get("relationship_id")
        new_status_str = data.get("status", "").lower()

        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        coach_profile = db.session.execute(
            select(CoachProfiles).where(CoachProfiles.user_id == coach_user.user_id)
        ).scalar_one_or_none()

        relationship = db.session.execute(
            select(CoachClientRelationships).where(
                CoachClientRelationships.relationship_id == rel_id,
                CoachClientRelationships.coach_profile_id == coach_profile.coach_profile_id
            )
        ).scalar_one_or_none()

        if not relationship:
            abort(404, description="Relationship not found or access denied")

        relationship.status = status_enum[new_status_str]

        if relationship.status == status_enum.terminated:
            relationship.ended_at = db.func.now()
        else:
            relationship.ended_at = None

        db.session.commit()

        create_notification(
            user_id=relationship.client_user_id,
            type_slug="relationship-update",
            title="Relationship Status Changed",
            body=f"Coach {coach_user.first_name} has updated your status to: {new_status_str}."
        )

        return {
            "message": f"Coach changed client relationship to {relationship.status.value}",
            "coach_client_relationship": relationship.relationship_id
        }
    

@coach_blp.route("/generate-invoice")
class CoachGenerateInvoice(MethodView):
    @jwt_required()
    @coach_blp.arguments(CreateInvoiceSchema)
    def post(self, data):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        rel_id = data.get("relationship_id")
        input_amount = data.get("amount")

        result = db.session.execute(
            select(CoachClientRelationships)
            .where(
                CoachClientRelationships.relationship_id == rel_id,
                CoachClientRelationships.status == status_enum.active, #
                CoachClientRelationships.coach_profile_id.in_(
                    select(CoachProfiles.coach_profile_id).where(CoachProfiles.user_id == coach_user.user_id)
                )
            )
        ).scalar_one_or_none()

        if not result:
            abort(404, description="Active relationship not found or unauthorized")

        rel = result

        payment_method = db.session.execute(
            select(PaymentMethods).where(PaymentMethods.user_id == rel.client_user_id)
        ).scalar_one_or_none()

        current_status = StatusEnumList.issued 
        now_utc = datetime.now(timezone.utc) 

        new_invoice = Invoices(
            relationship_id=rel.relationship_id, 
            payment_method_id=payment_method.payment_method_id if payment_method else None, 
            status=current_status, 
            currency="USD", 
            subtotal=input_amount, 
            created_at=now_utc, 
            issued_at=now_utc 
        )

        db.session.add(new_invoice)
        db.session.flush() 

        create_notification(
            user_id=rel.client_user_id,
            type_slug="invoice-update",
            title="Invoice Generated",
            body=f"New invoice for ${input_amount} issued by Coach {coach_user.first_name}."
        )

        db.session.commit()

        return {
            "message": "Invoice generated and client notified",
            "invoice_id": new_invoice.invoice_id, #
            "status": new_invoice.status.value, #
            "amount": float(input_amount)
        }, 201
    

@coach_blp.route("/invoices")
class CoachInvoiceList(MethodView):
    @jwt_required()
    def get(self):
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        query = (
            select(Invoices, Users.first_name, Users.last_name)
            .join(CoachClientRelationships, Invoices.relationship_id == CoachClientRelationships.relationship_id)
            .join(Users, CoachClientRelationships.client_user_id == Users.user_id)
            .where(
                CoachClientRelationships.coach_profile_id.in_(
                    select(CoachProfiles.coach_profile_id).where(CoachProfiles.user_id == coach_user.user_id)
                )
            )
            .order_by(Invoices.created_at.desc())
        )

        results = db.session.execute(query).all()

        return {
            "invoices": [
                {
                    "invoice_id": inv.invoice_id,
                    "relationship_id": inv.relationship_id,
                    "client_name": f"{fname} {lname}",
                    "amount": float(inv.subtotal),
                    "status": inv.status.value,
                    "created_at": inv.created_at.isoformat()
                } for inv, fname, lname in results
            ]
        }


@coach_blp.route("/update-status")
class UpdateInvoiceStatus(MethodView):
    @jwt_required()
    @coach_blp.arguments(UpdateInvoiceStatusSchema)
    def patch(self, data):
        invoice = Invoices.query.get_or_404(data["invoice_id"])
        
        if invoice.status == StatusEnumList.paid:
            return {"message": "Invoice already paid. Suggest refund workflow."}, 400

        relationship = CoachClientRelationships.query.get(invoice.relationship_id)

        old_status = invoice.status.value
        invoice.status = data["new_status"]
        db.session.commit()
        
        if relationship:
            create_notification(
                user_id=relationship.client_user_id,
                type_slug="invoice-update",
                title="Invoice Status Changed",
                body=f"Your invoice #{invoice.invoice_id} has been updated from {old_status} to {invoice.status.value}."
            )

        return {
            "message": f"Status updated to {invoice.status.value}",
            "invoice_id": invoice.invoice_id
        }
      
@coach_blp.route("/favorite")
class FavoriteCoach(MethodView):
    @jwt_required()
    @coach_blp.arguments(FavoriteCoachSchema)
    @coach_blp.response(200, FavoriteCoachSchema)
    def post(self, data):
        auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=auth_id).first_or_404()
        existing_favorite = CoachFavorites.query.filter_by(
            user_id=user.user_id,
            coach_profile_id=data['coach_profile_id']
        ).first()

        if existing_favorite:
            try:
                db.session.delete(existing_favorite)
                db.session.commit()
                return {"message": "Removed from favorites"}, 200 
            except Exception:
                db.session.rollback()
                abort(500, description="Failed to remove favorite.")

        favorite = CoachFavorites(
            user_id=user.user_id,
            coach_profile_id=data['coach_profile_id'],
            created_at=datetime.utcnow()
        )

        try:
            db.session.add(favorite)
            db.session.commit()
            return favorite
        except Exception as e:
            db.session.rollback()
            abort(500, description="Failed to favorite coach.")


@coach_blp.route("/clients/<int:client_id>/workouts/plan")
class ClientWorkoutPlanCreation(MethodView):
    @jwt_required()
    @coach_blp.arguments(ClientWorkoutPlanCreateSchema)
    @coach_blp.response(201, ClientWorkoutPlanSchema)
    def post(self, client_id, data):
        """Create complete workout plan for client with weekly schedule"""
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        coach_profile = get_coach_profile_from_user(coach_user)
        
        if not coach_profile:
            abort(403, description="Coach profile required.")
        
        # Verify coach is employed by client
        if not is_coach_employed_by_client(coach_user.user_id, client_id):
            abort(403, description="Not authorized to create workouts for this client.")
        
        # Create workout plan
        workout_plan = WorkoutPlans(
            owner_user_id=coach_user.user_id,
            name=data['name'],
            description=data.get('description'),
            is_public=False
        )
        db.session.add(workout_plan)
        db.session.flush()  # Get plan_id
        
        # Create workout days based on weekly schedule
        for day_schedule in data['weekly_schedule']:
            workout_day = WorkoutPlanDays(
                plan_id=workout_plan.plan_id,
                weekday=day_schedule['weekday'],
                session_time=day_schedule.get('session_time')
            )
            db.session.add(workout_day)
            db.session.flush()  # Get day_id
            
            # Add exercises to the day
            for exercise_data in day_schedule['exercises']:
                day_exercise = WorkoutPlanDayExercises(
                    day_id=workout_day.plan_day_id,
                    exercise_id=exercise_data['exercise_id'],
                    sets=exercise_data['sets'],
                    reps=exercise_data['reps'],
                    weight=exercise_data.get('weight'),
                    duration_minutes=exercise_data.get('duration_minutes'),
                    notes=exercise_data.get('notes'),
                    sort_order=exercise_data.get('sort_order', 1)
                )
                db.session.add(day_exercise)
        
        # Create assignment
        assignment = WorkoutPlanAssignments(
            plan_id=workout_plan.plan_id,
            assigned_to_user_id=client_id,
            assigned_by_user_id=coach_user.user_id,
            assignment_type='coach',
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            repeat_rule=data.get('repeat_rule', 'weekly'),
            status='active'
        )
        db.session.add(assignment)
        
        try:
            db.session.commit()
            
            # Return complete response
            response_data = {
                'plan_id': workout_plan.plan_id,
                'name': workout_plan.name,
                'description': workout_plan.description,
                'owner_user_id': workout_plan.owner_user_id,
                'created_at': workout_plan.created_at,
                'weekly_schedule': data['weekly_schedule'],
                'assignment_id': assignment.assignment_id,
                'assigned_to_client_id': client_id,
                'assigned_by_coach_id': coach_profile.coach_profile_id,
                'start_date': data['start_date'],
                'end_date': data.get('end_date'),
                'repeat_rule': data.get('repeat_rule', 'weekly'),
                'status': 'active'
            }
            return response_data
            
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Failed to create workout plan: {str(e)}")


@coach_blp.route("/clients/<int:client_id>/workouts/assigned")
class ClientWorkoutAssignments(MethodView):
    @jwt_required()
    @coach_blp.response(200, ClientWorkoutAssignmentsSchema)
    def get(self, client_id):
        """Get all workout assignments for client"""
        current_auth_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=current_auth_id).first_or_404()
        
        # Verify coach is employed by client
        if not is_coach_employed_by_client(coach_user.user_id, client_id):
            abort(403, description="Not authorized to view this client's workouts.")
        
        # Get all assignments for client created by this coach
        assignments = db.session.query(
            WorkoutPlanAssignments, WorkoutPlans
        ).join(
            WorkoutPlans, WorkoutPlanAssignments.plan_id == WorkoutPlans.plan_id
        ).filter(
            WorkoutPlanAssignments.assigned_to_user_id == client_id,
            WorkoutPlanAssignments.assigned_by_user_id == coach_user.user_id
        ).all()
        
        assignment_list = []
        active_count = 0
        completed_count = 0
        
        for assignment, plan in assignments:
            assignment_data = {
                'plan_id': plan.plan_id,
                'name': plan.name,
                'description': plan.description,
                'owner_user_id': plan.owner_user_id,
                'created_at': plan.created_at,
                'weekly_schedule': [],  # Would need to fetch from WorkoutPlanDays
                'assignment_id': assignment.assignment_id,
                'assigned_to_client_id': client_id,
                'assigned_by_coach_id': coach_user.user_id,
                'start_date': assignment.start_date,
                'end_date': assignment.end_date,
                'repeat_rule': assignment.repeat_rule.value if assignment.repeat_rule else None,
                'status': assignment.status.value if assignment.status else None
            }
            
            assignment_list.append(assignment_data)
            
            if assignment.status == 'active':
                active_count += 1
            elif assignment.status == 'completed':
                completed_count += 1
        
        return {
            'assignments': assignment_list,
            'total_active': active_count,
            'total_completed': completed_count
        }
            
            
# Dashboard Helper Functions
def is_coach_employed_by_client(coach_user_id, client_user_id):
    """Check if coach has active employment relationship with client"""
    coach_profile = CoachProfiles.query.filter_by(user_id=coach_user_id).first()
    if not coach_profile:
        return False
    
    relationship = CoachClientRelationships.query.filter_by(
        coach_profile_id=coach_profile.coach_profile_id,
        client_user_id=client_user_id,
        status=status_enum.active
    ).first()
    
    return relationship is not None

def get_coach_profile_from_user(user):
    """Get coach profile from user object"""
    return CoachProfiles.query.filter_by(user_id=user.user_id).first()

def calculate_progress_summary(client_user_id, days=30):
    """Calculate progress summary for client over specified days"""
    from datetime import date, timedelta
    
    start_date = date.today() - timedelta(days=days)
    
    # Daily Survey averages
    surveys = DailySurvey.query.filter(
        DailySurvey.user_id == client_user_id,
        DailySurvey.date >= start_date
    ).all()
    
    avg_energy = func.avg(DailySurvey.energy_level).filter(
        DailySurvey.user_id == client_user_id,
        DailySurvey.date >= start_date,
        DailySurvey.energy_level.isnot(None)
    ).scalar() or 0
    
    avg_mood = func.avg(DailySurvey.mood_score).filter(
        DailySurvey.user_id == client_user_id,
        DailySurvey.date >= start_date,
        DailySurvey.mood_score.isnot(None)
    ).scalar() or 0
    
    avg_sleep = func.avg(DailySurvey.sleep_hours).filter(
        DailySurvey.user_id == client_user_id,
        DailySurvey.date >= start_date,
        DailySurvey.sleep_hours.isnot(None)
    ).scalar() or 0
    
    # Workout completion rate
    total_workouts = WorkoutLogs.query.filter(
        WorkoutLogs.user_id == client_user_id,
        WorkoutLogs.created_at >= start_date
    ).count()
    
    # Nutrition logging rate
    total_meals = MealLogs.query.filter(
        MealLogs.user_id == client_user_id,
        MealLogs.created_at >= start_date
    ).count()
    
    # Goals status
    active_goals = Goals.query.filter_by(
        for_user_id=client_user_id,
        status='active'
    ).count()
    
    completed_goals = Goals.query.filter_by(
        for_user_id=client_user_id,
        status='completed'
    ).count()
    
    return {
        'avg_energy_level': float(avg_energy) if avg_energy else 0,
        'avg_mood_score': float(avg_mood) if avg_mood else 0,
        'avg_sleep_hours': float(avg_sleep) if avg_sleep else 0,
        'workout_completion_rate': min(total_workouts / max(days * 0.7, 1), 1.0),  # Assume 70% target
        'nutrition_logging_rate': min(total_meals / max(days * 3, 1), 1.0),  # 3 meals/day target
        'active_goals_count': active_goals,
        'completed_goals_count': completed_goals,
        'total_workouts_completed': total_workouts,
        'days_tracked': len(set(s.date for s in surveys))
    }

def get_recent_activity(client_user_id, days=7):
    """Get recent activity for client"""
    from datetime import date, timedelta
    
    start_date = date.today() - timedelta(days=days)
    activities = []
    
    # Recent surveys
    surveys = DailySurvey.query.filter(
        DailySurvey.user_id == client_user_id,
        DailySurvey.date >= start_date
    ).order_by(DailySurvey.date.desc()).limit(5).all()
    
    for survey in surveys:
        activities.append({
            'date': survey.date,
            'activity_type': 'survey',
            'description': f'Daily wellness survey completed',
            'details': {
                'energy_level': survey.energy_level,
                'mood_score': survey.mood_score
            }
        })
    
    # Recent workouts
    workouts = WorkoutLogs.query.filter(
        WorkoutLogs.user_id == client_user_id,
        WorkoutLogs.created_at >= start_date
    ).order_by(WorkoutLogs.created_at.desc()).limit(5).all()
    
    for workout in workouts:
        activities.append({
            'date': workout.created_at.date(),
            'activity_type': 'workout',
            'description': f'Workout completed',
            'details': {
                'sets': workout.sets,
                'reps': workout.reps
            }
        })
    
    # Sort by date
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:10]  # Return last 10 activities

def get_goals_status(client_user_id):
    """Get current goals status for client"""
    goals = Goals.query.filter_by(for_user_id=client_user_id).order_by(Goals.created_at.desc()).all()
    
    goals_status = []
    for goal in goals:
        progress_percentage = 0  # Simple placeholder - could be calculated based on goal type
        if goal.status == 'completed':
            progress_percentage = 100
        
        goals_status.append({
            'goal_id': goal.goal_id,
            'description': goal.description,
            'status': goal.status,
            'progress_percentage': progress_percentage,
            'created_at': goal.created_at,
            'target_date': goal.target_date
        })
    
    return goals_status

# Dashboard Endpoints
@coach_blp.route("/dashboard/clients")
class CoachClientDashboard(MethodView):
    @jwt_required()
    @coach_blp.response(200, ClientListSchema)
    def get(self):
        """Get list of employed clients with basic progress overview"""
        coach_user_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=coach_user_id).first()
        
        if not coach_user:
            abort(404, description="Coach user not found.")
        
        coach_profile = get_coach_profile_from_user(coach_user)
        if not coach_profile:
            abort(404, description="Coach profile not found.")
        
        # Get active relationships
        relationships = CoachClientRelationships.query.filter_by(
            coach_profile_id=coach_profile.coach_profile_id,
            status=status_enum.active
        ).all()
        
        clients_data = []
        for relationship in relationships:
            client_user = Users.query.get(relationship.client_user_id)
            if not client_user:
                continue
            
            # Calculate progress summary
            progress_summary = calculate_progress_summary(client_user.user_id, days=30)
            
            # Get recent activity
            recent_activity = get_recent_activity(client_user.user_id, days=7)
            
            # Get goals status
            goals_status = get_goals_status(client_user.user_id)
            
            clients_data.append({
                'client_info': {
                    'user_id': client_user.user_id,
                    'first_name': client_user.first_name,
                    'last_name': client_user.last_name,
                    'relationship_start_date': relationship.started_at,
                    'relationship_status': relationship.status.value
                },
                'progress_summary': progress_summary,
                'recent_activity': recent_activity,
                'goals_status': goals_status
            })
        
        return {'clients': clients_data}

@coach_blp.route("/dashboard/clients/<int:client_id>/progress")
class ClientProgressDetail(MethodView):
    @jwt_required()
    @coach_blp.response(200, ClientDashboardSchema)
    def get(self, client_id):
        """Get detailed progress data for specific client"""
        coach_user_id = get_jwt_identity()
        coach_user = Users.query.filter_by(auth_id=coach_user_id).first()
        
        if not coach_user:
            abort(404, description="Coach user not found.")
        
        # Verify employment relationship
        if not is_coach_employed_by_client(coach_user.user_id, client_id):
            abort(403, description="Not authorized to view this client's progress.")
        
        client_user = Users.query.get(client_id)
        if not client_user:
            abort(404, description="Client not found.")
        
        # Get relationship details
        coach_profile = get_coach_profile_from_user(coach_user)
        relationship = CoachClientRelationships.query.filter_by(
            coach_profile_id=coach_profile.coach_profile_id,
            client_user_id=client_id,
            status=status_enum.active
        ).first()
        
        if not relationship:
            abort(404, description="Client relationship not found.")
        
        # Calculate detailed progress
        progress_summary = calculate_progress_summary(client_user.user_id, days=90)
        recent_activity = get_recent_activity(client_user.user_id, days=30)
        goals_status = get_goals_status(client_user.user_id)
        
        return {
            'client_info': {
                'user_id': client_user.user_id,
                'first_name': client_user.first_name,
                'last_name': client_user.last_name,
                'relationship_start_date': relationship.started_at,
                'relationship_status': relationship.status.value
            },
            'progress_summary': progress_summary,
            'recent_activity': recent_activity,
            'goals_status': goals_status
        }
