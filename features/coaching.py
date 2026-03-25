from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos, Roles, CoachDocuments
from db import db
from datetime import date
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.coach_schema import CoachProfileSchema, CoachProfileQuerySchema, CoachDocumentSchema

coach_blp=Blueprint("Coach", __name__, url_prefix="/coach", description="Coach feat")

@coach_blp.route("/top-coach")
class TopCoach(MethodView):
    def get(self):
        """
        Get top coaches and reviews (need photos)
        """
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
                CoachProfiles.bio,
                CoachProfiles.profile_photo,
                Specialties.name,
                CoachProgressPhotos.before_photo_url,
                CoachProgressPhotos.after_photo_url,
                CoachProgressPhotos.description.label("transformation_desc"),
                rating_stmt.c.avg_rating,
                rating_stmt.c.total_reviews
            )
            .join(CoachProfiles, Users.user_id == CoachProfiles.coach_profile_id)
            .join(CoachProgressPhotos, CoachProfiles.coach_profile_id == CoachProgressPhotos.coach_profile_id)
            .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id)
            .join(rating_stmt, CoachProfiles.coach_profile_id == rating_stmt.c.coach_profile_id)
            .join(UserRoles, Users.auth_id == UserRoles.user_id)
            .filter(UserRoles.role_id == 2)
            # .filter(CoachProgressPhotos.is_public == True)
            .order_by(desc(rating_stmt.c.avg_rating), desc(rating_stmt.c.total_reviews))
            .limit(3)
        )

        try:
            result = db.session.execute(stmt).all()

            # map the rows to a list of dicts
            top_coaches = [
                {
                    "user_id": row.user_id,
                    "name": f"{row.first_name} {row.last_name}",
                    "specialty": row.name,
                    "bio": row.bio,
                    "image": row.profile_photo,
                    "rating": float(round(row.avg_rating, 1)),
                    "before-photo": row.before_photo_url,
                    "after-photo":row.after_photo_url,
                    "photo-description":row.transformation_desc
                }
                for row in result
            ]

            return {"coaches": top_coaches}, 200

        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Failed to fetch coaches: {str(e)}")

@coach_blp.route("/coach-profile")
class CoachProfileView(MethodView):
    @jwt_required()
    @coach_blp.arguments(CoachProfileQuerySchema, location="query")
    @coach_blp.response(200, CoachProfileSchema)
    def get(self,args):
        """
        Get coach profile.
        Coach: Calls /coach-profile (gets their own).
        Admin: Calls /coach-profile?user_id=10 (gets specific user).
        """
        curr_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).scalar()

        if not curr_user_id:
            abort(401, message="User not found.")

        target_user_id = args.get("user_id") or None

        #if target id is provided check if its the logged in user
        #######need to check if its admin doing the call
        if target_user_id and target_user_id != curr_user_id:
            # Check if curr_id has the 'admin' role
            is_admin = db.session.query(UserRoles).join(Roles).filter(
                UserRoles.user_id == curr_auth_id,
                Roles.name == 'admin'
            ).first()

            if not is_admin:
                abort(403, message="Admin access required to view other profiles.")
            
            profile = CoachProfiles.query.filter_by(user_id=target_user_id).first()
        
        else:
            profile = CoachProfiles.query.filter_by(user_id=curr_user_id).first()

        if not profile:
            abort(404, message="Coach profile not found.")
        return profile
    
    @jwt_required()
    @coach_blp.arguments(CoachProfileSchema(load_instance=False))
    @coach_blp.response(201, CoachProfileSchema)
    def post(self,data):
        """
        Initial Application: Client creates a coach profile with status 'pending'.
        """
        curr_auth_id = get_jwt_identity()
        curr_user_id = db.session.query(Users.user_id).filter_by(auth_id=curr_auth_id).scalar()

        if CoachProfiles.query.filter_by(user_id=curr_user_id).first():

            abort(400, message="A profile already exists for this user.")

        profile = CoachProfiles(**data, user_id=curr_user_id)
        db.session.add(profile)

        # Optional: Notify admin ????

        db.session.commit()
        return profile
    
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
            abort(403, message="Unauthorized to edit this profile.")

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
                val_upper = value.upper() if isinstance(value, str) else value
                if is_admin:
                    setattr(profile, key, value)
                    if val_upper == ApprovalStatusEnum.approved:
                        profile.approved_at = datetime.utcnow()
                        profile.approved_by_admin_user_id = curr_user_id
                elif val_upper == ApprovalStatusEnum.switched:
                    setattr(profile, key, value)
                else:
                    continue


            #handle other admin-Only fields
            elif key in restricted_fields:
                if is_admin:
                    setattr(profile, key, value)
                else:
                    continue
            #handle general fields (bio, experience, photo, specialty)
            else:
                setattr(profile, key, value)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(500, message="Database error occurred.")

        return profile

@coach_blp.route("/coach-profile/documents")
class CoachDocumentView(MethodView):
    @jwt_required()
    @coach_blp.arguments(CoachDocumentSchema)
    @coach_blp.response(201, CoachDocumentSchema)
    def post(self, document_obj):
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
        profile = db.session.execute(stmt).scalar()
        
        if not profile:
            return {"message": f"No Profile found for AuthID: {curr_auth_id}"}, 404
        
        new_doc = CoachDocuments(
            document_type=document_obj['document_type'],
            document_url=document_obj['document_url'],
            coach_profile_id=profile.coach_profile_id
        )
                
        db.session.add(new_doc)
        db.session.commit()
        return new_doc
    
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
            abort(404, message="Document not found or access denied.")
            
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
            abort(404, message="Document not found or access denied.")

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
            abort(404, message="Document not found or access denied.")

        
        db.session.delete(document)
        db.session.commit()

        # Return success message 
        return {"message": f"Document {doc_id} has been deleted."}, 200
