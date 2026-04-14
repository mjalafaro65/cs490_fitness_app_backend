from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from middleware import roles_required
from models import Users, UserRoles, CoachProfiles, CoachProgressPhotos, CoachDocuments
from db import db
from datetime import date, datetime, timezone
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select, desc
from schemas.workout_schema import WorkoutLogSchema


@workout_blp.route("/workout-logs")
class WorkoutLogs(MethodView):
    @jwt_required()
    @workout_blp.arguments(WorkoutLogSchema)
    @workout_blp.response(200, WorkoutLogSchema)
    def post(self, workout_log_data):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            abort(404, description="User record not found.")
        
        exercise_id = workout_log_data.get("exercise_id")
        ### May allow for entry without exercise id.
        if not exercise_id:
            abort(400, description="exercise_id is required.")
        

        return workout_log_data

class CompleteWorkout(MethodView):
    @jwt_required()
    @workout_blp.arguments(WorkoutLogSchema)
    @workout_blp.response(200, description="Workout marked as complete.")
    def post(self, workout_log_data):
        user_id = get_jwt_identity()
        user = Users.query.filter_by(auth_id=user_id).first()
        if not user:
            abort(404, description="User record not found.")

        new_log = WorkoutLogs(
            user_id=user.user_id,
            exercise_id=workout_log_data.get("exercise_id"),
            sets=workout_log_data.get("sets"),
            reps=workout_log_data.get("reps"),
            weight=workout_log_data.get("weight"),
            rpe=workout_log_data.get("rpe"),
            distance=workout_log_data.get("distance"),
            calories=workout_log_data.get("calories"),
            duration_minutes=workout_log_data.get("duration_minutes"),
            notes=workout_log_data.get("notes")
        )

        db.session.add(new_log)
        db.session.commit()

        return {"message": "Workout logged and marked as complete."}