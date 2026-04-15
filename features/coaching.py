from datetime import datetime
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos, Roles, CoachDocuments, DailySurvey, WorkoutPlanAssignments
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.coach_schema import CoachProfileSchema, CoachProfileQuerySchema, CoachDocumentSchema, CoachBrowsingSchema, SpecialtySchema , AssignWorkoutPlanSchema, AssignMealPlanSchema
from schemas.client_schema import DailySurveySchema
from models.coach_profiles import ApprovalStatusEnum
from .utils import create_notification



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
    @jwt_required()
    @coach_blp.arguments(CoachProfileQuerySchema, location="query")
    @coach_blp.response(200, CoachProfileSchema)
    def get(self,args):
        """
        Get coach profile.
        Coach: Calls /coach-profile (gets their own).
        Admin/Client: Calls /coach-profile?user_id=10 (gets specific user).
        """
        curr_auth_id = get_jwt_identity()
        result = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).first()
        curr_user_id = result[0] if result else None
        
        if not curr_user_id:
            abort(401, description="User not found.")

        target_user_id = args.get("user_id") or None

        #if target id is provided check if its the logged in user
        #######need to check if its admin or client doing the call
        print(target_user_id, curr_user_id)
        if target_user_id and target_user_id != curr_user_id:
            
            profile = CoachProfiles.query.filter_by(user_id=target_user_id).first()
        
        else:
            profile = CoachProfiles.query.filter_by(user_id=curr_user_id).first()

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
            abort(500, message="Database error occurred during profile creation.") 
    
    @jwt_required()
    @coach_blp.arguments(CoachProfileSchema(partial=True,load_instance=False))
    @coach_blp.response(200, CoachProfileSchema)
    def patch(self,updated_data):
        """
        Update existing profile. partial=True allows updating just one field.
        """
        curr_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).scalar()

        target_user_id = updated_data.pop("user_id", None) or curr_user_id

        #look at role
        is_admin = db.session.query(UserRoles).join(Roles).filter(
                UserRoles.user_id == curr_auth_id,
                Roles.name == 'admin'
        ).first()

        #if its not user or admin 
        if int(target_user_id) != int(curr_user_id) and not is_admin:
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
                val_upper = value.lower() if isinstance(value, str) else value
                if is_admin:
                    setattr(profile, key, value)
                    if val_upper == ApprovalStatusEnum.approved:
                        profile.approved_at = datetime.utcnow()
                        profile.approved_by_admin_user_id = curr_user_id
                        
                        create_notification(
                            user_id=profile.user_id,
                            type_slug="admin-approval",
                            title="Application Approved!",
                            body="Congratulations! Your coach profile is now live."
                        )
                elif val_upper == ApprovalStatusEnum.switched or current_status_upper == ApprovalStatusEnum.switched:
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
            CoachProfiles.bio
        ).join(Users, CoachProfiles.user_id == Users.user_id) \
        .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id) \
        .filter(CoachProfiles.status == ApprovalStatusEnum.approved) \
        .all()

        return results


### Filter for type of coach
@coach_blp.route("/coachbrowse/filter")
class CoachBrowseFilter(MethodView):
    @coach_blp.arguments(CoachBrowsingSchema, location="query")
    @coach_blp.response(200, CoachBrowsingSchema(many=True))
    def get(self, args):
        specialty_id = request.args.get("specialty_id")

        query = db.session.query(
            CoachProfiles.coach_profile_id,
            Users.first_name,
            Users.last_name,
            Specialties.name.label("specialty_name"),
            CoachProfiles.years_experience,
            CoachProfiles.bio
        ).join(Users, CoachProfiles.user_id == Users.user_id) \
        .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id) \
        .filter(CoachProfiles.status == ApprovalStatusEnum.approved) 
        

        if specialty_id:
            query = query.filter(CoachProfiles.specialty_id == specialty_id)

        results = query.all()
        return results

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


        
            