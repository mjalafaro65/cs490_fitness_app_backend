from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import Users, CoachReviews, UserRoles, CoachProfiles, Specialties, CoachProgressPhotos
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc

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
                CoachProfiles.bio,
                CoachProfiles.profile_photo,
                Specialties.name.label("specialty_name"),
                CoachProgressPhotos.before_photo_url,
                CoachProgressPhotos.after_photo_url,
                CoachProgressPhotos.description.label("transformation_desc"),
                rating_stmt.c.avg_rating,
                rating_stmt.c.total_reviews
            )
            # Corrected join to use user_id
            .join(CoachProfiles, Users.user_id == CoachProfiles.user_id) 
            .join(CoachProgressPhotos, CoachProfiles.coach_profile_id == CoachProgressPhotos.coach_profile_id)
            .join(Specialties, CoachProfiles.specialty_id == Specialties.specialty_id)
            .join(rating_stmt, CoachProfiles.coach_profile_id == rating_stmt.c.coach_profile_id)
            .join(UserRoles, Users.auth_id == UserRoles.user_id)
            .filter(UserRoles.role_id == 2)
            .filter(CoachProfiles.approval_status == 'APPROVED') # Only show approved coaches
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
            abort(500, message=f"Failed to fetch coaches: {str(e)}")

@coach_blp.route("/profile")
class CoachProfileView(MethodView):
    @jwt_required()
    @coach_blp.response(200, CoachProfileSchema)
    def get(self):
        """Retrieve the authenticated coach's profile details."""
        auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=auth_id).first()
        
        if not user:
            abort(404, message="User not found.")

        profile = CoachProfiles.query.filter_by(user_id=user.user_id).first()
        if not profile:
            abort(404, message="Coach profile not found. Please complete setup first.")
            
        return profile

    @jwt_required()
    @coach_blp.arguments(CoachProfileSchema)
    @coach_blp.response(200, CoachProfileSchema)
    def put(self, data):
        """Update existing coach profile fields only."""
        auth_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=auth_id).first()
        
        if not user:
            abort(404, message="User not found.")

        profile = CoachProfiles.query.filter_by(user_id=user.user_id).first()
        
        # Refactored: No longer creates profile; only updates.
        if not profile:
            abort(400, message="Coach profile not found. Use /auth/setup to create your profile.")

        # Update fields dynamically
        for key, value in data.items():
            setattr(profile, key, value)

        try:
            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"Database error during update: {str(e)}")

@coach_blp.route("/init-specialties")
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
            abort(500, message=f"Failed to initialize specialties: {str(e)}")