from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from middleware import roles_required
from models import Users, UserRoles, CoachProfiles, CoachProgressPhotos, CoachDocuments, CoachReviews, AccountDeletionInfo, ClientProfiles
from db import db
from datetime import date, datetime, timezone
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.coach_schema import CoachProfileSchema, CoachDocumentSchema
from schemas.admin_schema import AdminDocumentReviewSchema, AdminCheckReviewsSchema, AdminPurgeUserSchema
from schemas.user_schema import UserInfoSchema, UserQuerySchema
from models.coach_profiles import ApprovalStatusEnum
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from models.coach_documents import StatusEnum



admin_blp=Blueprint("Admin", __name__, url_prefix="/admin", description="Admin features")

@admin_blp.route("/coach-applications")
class CoachApplications(MethodView):
    @roles_required("admin")
    @admin_blp.response(200, CoachProfileSchema(many=True))
    def get(self):
        """
        Get pending coach applications
        """
        return CoachProfiles.query.filter_by(status=ApprovalStatusEnum.pending).all()
    

@admin_blp.route("/coach-applications/<int:coach_pf_id>")
class CoachApplications(MethodView):
    @roles_required("admin")
    @admin_blp.response(200, CoachProfileSchema)
    def get(self,coach_pf_id):
        """
        Get pending coach application
        """
        return CoachProfiles.query.filter_by(status=ApprovalStatusEnum.pending,coach_profile_id=coach_pf_id).first_or_404()


@admin_blp.route("/coach-documents")
class CoachDocumentsAdminView(MethodView):
    @roles_required("admin")
    @admin_blp.doc(parameters=[{'name': 'user_id', 'in': 'query', 'type': 'integer'}])
    @admin_blp.response(200, CoachDocumentSchema(many=True))
    def get(self):
        """
        Get all pending uploads OR filter by coach via ?user_id=X
        """
        target_user_id = request.args.get('user_id', type=int)
        if target_user_id:
            stmt = (
                select(CoachDocuments)
                .join(CoachProfiles)
                .filter(CoachProfiles.user_id == target_user_id)
                .order_by(CoachDocuments.uploaded_at.desc(),CoachDocuments.coach_profile_id)
            )
        else:
            stmt = select(CoachDocuments).filter(CoachDocuments.status == StatusEnum.pending)

        docs=db.session.execute(stmt).scalars().all()
        if not docs:
            abort(404, description="No documents associated with id.")

        return docs
    
@admin_blp.route("/coach-documents/<int:doc_id>")
class AdminDocumentActionView(MethodView):
    @jwt_required()
    @admin_blp.arguments(AdminDocumentReviewSchema) 
    @admin_blp.response(200, CoachDocumentSchema)
    def patch(self, update_data, doc_id):
        """
        Admin reviews the document
        """

        document = CoachDocuments.query.get_or_404(doc_id)

        document.status = update_data.get('status')
        document.notes = update_data.get('notes')

        admin_auth_id = get_jwt_identity()
        admin_user_id = db.session.query(Users.user_id).filter_by(auth_id=admin_auth_id).scalar()
        
        document.reviewed_by_admin_user_id = admin_user_id
        document.reviewed_at = datetime.now(timezone.utc)

        db.session.commit()
        return document
    

@admin_blp.route("/manage-reviews")
class AdminReviewsView(MethodView):
    @roles_required("admin")
    @admin_blp.response(200, AdminCheckReviewsSchema(many=True))
    def get(self):
        review_id = request.args.get('review_id', type=int)
        coach_profile_id = request.args.get('coach_profile_id', type=int)
        client_user_id = request.args.get('client_user_id', type=int)
        query = CoachReviews.query

        if review_id:
            query = query.filter(CoachReviews.review_id == review_id)
        if coach_profile_id:
            query = query.filter(CoachReviews.coach_profile_id == coach_profile_id)
        if client_user_id:
            query = query.filter(CoachReviews.client_user_id == client_user_id)

        return query.all()

@admin_blp.route("/manage-reviews/<int:review_id>")
class AdminReviewActionView(MethodView):
    @roles_required("admin")
    @admin_blp.arguments(AdminCheckReviewsSchema(partial=True)) 
    @admin_blp.response(200, AdminCheckReviewsSchema)
    def patch(self, update_data, review_id):
        review = CoachReviews.query.get_or_404(review_id)

        review.is_flagged = update_data.get('is_flagged', review.is_flagged)
        review.is_visible = update_data.get('is_visible', review.is_visible)

        db.session.commit()
        return review

@admin_blp.route("/purge-user")
class AdminPurgeUserView(MethodView):
    @roles_required("admin")
    @admin_blp.arguments(AdminPurgeUserSchema)
    @admin_blp.response(200, description="User and all related data purged.")
    def delete(self, update_data):
        user_id = update_data.get('user_id')
        user = Users.query.get_or_404(user_id)

        db.session.delete(user)
        db.session.commit()
        return {"message": "User purged successfully."}  
    
@admin_blp.route("/users")
class AdminUsersView(MethodView):
    @admin_blp.arguments(UserQuerySchema, location="query")
    @admin_blp.response(200, UserInfoSchema(many=True))
    def get(self, args):
        
        """
        Get users with filters + pagination
        """

        user_id = request.args.get("user_id", type=int)
        is_active = request.args.get("is_active", type=int) 
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=20, type=int)

        query = Users.query

        if user_id:
            query = query.filter(Users.user_id == user_id)

        if is_active is not None:
            query = query.filter(Users.is_active == bool(is_active))

        query = query.order_by(Users.created_at.desc())

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return paginated.items
    
@admin_blp.route("/users/stats")
class AdminUserStatsView(MethodView):
    @roles_required("admin")
    def get(self):

        total_users = Users.query.count()

        active_users = Users.query.filter_by(is_active=True).count()

        inactive_users = Users.query.filter_by(is_active=False).count()
        
        deleted_users = AccountDeletionInfo.query.count()
        
        client_users = ClientProfiles.query.count()

        # users created in last 7 days
        last_7_days = datetime.now(timezone.utc) - timedelta(days=7)

        new_c_users= ClientProfiles.query.filter(
            ClientProfiles.created_at >= last_7_days
        ).count()
        
        del_count = AccountDeletionInfo.query.filter(
            AccountDeletionInfo.requested_at >= last_7_days
        ).count()

        # non admin

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "deleted_users": deleted_users,
            "new_client_users_last_7": new_c_users,
            "deletions_last_7_days": del_count,
            "client_users": client_users,         
        }