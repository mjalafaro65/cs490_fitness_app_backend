from datetime import datetime
from sqlalchemy import func
from db import db

class Users(db.Model):
    __tablename__ = "users"
    
    user_id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.Integer, db.ForeignKey("user_auths.auth_id"), unique=True, nullable=False)

    ### Cascade to delete all related data when a user is purged.
    # auth = db.relationship(
    #     "UserAuths", 
    #     backref="user", 
    #     cascade="all, delete-orphan", 
    #     single_parent=True
    #
    # payment_plan_overrides = db.relationship(
    #     "ClientPaymentPlanOverrides", 
    #     cascade="all, delete-orphan"
    # )
    # client_profiles = db.relationship(
    #     "ClientProfiles", 
    #     cascade="all, delete-orphan"
    # )
    # coach_client_relationships = db.relationship(
    #     "CoachClientRelationships",
    #     foreign_keys="CoachClientRelationships.client_user_id",
    #     cascade="all, delete-orphan"
    # )
    # coach_hire_requests = db.relationship(
    #     "CoachHireRequests",
    #     cascade="all, delete-orphan"
    # )
    # coach_profiles = db.relationship(
    #     "CoachProfiles",
    #     foreign_keys="CoachProfiles.user_id",
    #     cascade="all, delete-orphan"
    # )
    # coach_reports = db.relationship(
    #     "CoachReports",
    #     cascade="all, delete-orphan"
    # )
    # coach_reviews = db.relationship(
    #     "CoachReviews",
    #     cascade="all, delete-orphan"
    # )
    daily_surveys = db.relationship(
        "DailySurvey",
        cascade="all, delete-orphan"
    )
    goals = db.relationship(
        "Goals",
        foreign_keys="Goals.for_user_id",
        cascade="all, delete-orphan"
    )
    meal_logs = db.relationship(
        "MealLogs",
    )
    # meal_plan_assignments = db.relationship(
    #     "MealPlanAssignments",
    #     foreign_keys="MealPlanAssignments.user_id",
    #     cascade="all, delete-orphan"
    # )
    # meal_plans = db.relationship(
    #     "MealPlans",
    # )
    # messages = db.relationship(
    #     "Messages",
    #     cascade="all, delete-orphan"
    # )
    notifications = db.relationship(
        "Notifications",
    )
    # payment_methods = db.relationship(
    #     "PaymentMethods",
    #     cascade="all, delete-orphan"
    # )
    # payments = db.relationship(
    #     "Payments",
    #     cascade="all, delete-orphan"
    # )
    # refund_disputes = db.relationship(
    #     "RefundDisputes",
    #     foreign_keys="RefundDisputes.opened_by_user_id",
    #     cascade="all, delete-orphan"
    # )
    # review_flags = db.relationship(
    #     "ReviewFlags",
    #     cascade="all, delete-orphan"
    # )
    # review_interactions = db.relationship(
    #     "ReviewInteractions",
    #     cascade="all, delete-orphan"
    # )
    # # saved_coaches = db.relationship(
    #     "SavedCoaches",
    #     cascade="all, delete-orphan"
    # )
    # shared_plans_with = db.relationship(
    #     "SharedPlans",
    #     foreign_keys="SharedPlans.shared_with_user_id",
    #     cascade="all, delete-orphan"
    # )
    # shared_plans_by = db.relationship(
    #     "SharedPlans",
    #     foreign_keys="SharedPlans.shared_by_user_id",
    #     cascade="all, delete-orphan"
    # )
    workout_logs = db.relationship(
        "WorkoutLogs",
    )
    # workout_plan_assignments_assigned_to = db.relationship(
    #     "WorkoutPlanAssignments",
    #     foreign_keys="WorkoutPlanAssignments.assigned_to_user_id",
    #     cascade="all, delete-orphan"
    # )
    # workout_plan_assignments_assigned_by = db.relationship(
    #     "WorkoutPlanAssignments",
    #     foreign_keys="WorkoutPlanAssignments.assigned_by_user_id",
    #     cascade="all, delete-orphan"
    # )
    # workout_plans = db.relationship(
    #     "WorkoutPlans",
    #     cascade="all, delete-orphan"
    # )


    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    disabled_at = db.Column(db.DateTime, nullable=True)
    disabled_by_admin_user_id = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    conversation_links = db.relationship(
        "ConversationParticipants",
        back_populates="user"
    )
    
    