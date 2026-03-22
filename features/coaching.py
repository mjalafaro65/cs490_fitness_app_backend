from flask.views import MethodView
from flask_smorest import Blueprint,abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos
from db import db
from datetime import date
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc

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


