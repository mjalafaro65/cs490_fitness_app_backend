from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos
from db import db
from datetime import date
from flask_jwt_extended import jwt_required, get_jwt_identity
from middleware import roles_required 
from sqlalchemy import func, select, desc
from schemas.coach_schema import CoachProfileSchema, CoachProfilePostSchema

coach_blp=Blueprint("Coach", __name__, url_prefix="/coach", description="Coach feat")

@coach_blp.route("/top-coach")
class TopCoach(MethodView):
    def get(self):
        """
        Get top 3 coaches and reviews (need photos)
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
    @coach_blp.arguments(CoachProfilePostSchema, location="query")
    @coach_blp.response(200, CoachProfileSchema)
    def get(self,arg):
        """
        Get coach profile.
        Coach: Calls /coach-profile (gets their own).
        Admin: Calls /coach-profile?user_id=10 (gets specific user).
        """
        curr_id = get_jwt_identity()
        target_user_id = arg.get("user_id")

        #if target id is provided check if its the logged in user
        #######need to check if its admin doing the call
        
        if target_user_id and target_user_id != curr_id:
            UserRoles.query.get_or_404()
            profile = CoachProfiles.query.filter_by(user_id=target_user_id).first()
        else:
        #fetch profile for logged in person
            profile = CoachProfiles.query.filter_by(user_id=curr_id).first()

        if not profile:
            abort(404, message="Coach profile not found.")
        return profile
    
    @jwt_required()
    @coach_blp.arguments(CoachProfileSchema)
    @coach_blp.response(201, CoachProfileSchema)
    def post(self,data):
        """
        Initial Application: Client creates a coach profile with status 'pending'.
        """
        user_id = get_jwt_identity()

        if CoachProfiles.query.filter_by(user_id=user_id).first():

            abort(400, message="A profile already exists for this user.")

        profile = CoachProfiles(**data, user_id=user_id)
        db.session.add(profile)

        # Optional: Notify admin ????

        db.session.commit()
        return profile
    
    @jwt_required()
    @coach_blp.arguments(CoachProfileSchema(partial=True))
    @coach_blp.response(200, CoachProfileSchema)
    def patch(self,updated_data):
        """
        Update existing profile. partial=True allows updating just one field.
        """
        user_id = get_jwt_identity()
        
        target_user_id = update_data.pop("query_user_id", None) or current_user_id

    








