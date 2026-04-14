from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy import and_, func, or_

from db import db
from models import (
    Exercises,
    Users,
    WorkoutPlanAssignments,
    WorkoutPlanDayExercises,
    WorkoutPlanDays,
    WorkoutPlans,
)
from models.calendar_workouts import CalendarWorkouts
from models.workout_plan_assignments import (
    AssignmentStatusEnum,
    AssignmentTypeEnum,
    RepeatRuleEnum,
)
from schemas.workout_schema import (
    CalendarOccurrenceSchema,
    DayExerciseCreateSchema,
    DayExerciseUpdateSchema,
    ExerciseCreateSchema,
    ExerciseListQuerySchema,
    ExerciseUpdateSchema,
    PlanAssignmentSchema,
    PlanBrowseQuerySchema,
    PlanCalendarSchema,
    PlanCopySchema,
    PlanCreateSchema,
    PlanDayCreateSchema,
    PlanDayUpdateSchema,
    PlanUpdateSchema,
)

workout_blp = Blueprint(
    "Workouts",
    __name__,
    url_prefix="/workouts",
    description="Exercises, workout plans, scheduling, and browse/copy",
)


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


def _exercise_visible_to_user(ex: Exercises, user_id: int) -> bool:
    if not ex.is_active:
        return False
    if ex.created_by_user_id is None:
        return True
    if ex.is_public:
        return True
    if ex.created_by_user_id == user_id:
        return True
    return False


def _plan_readable(plan: WorkoutPlans, user_id: int) -> bool:
    if plan.owner_user_id == user_id:
        return True
    return bool(plan.is_public)


def _plan_writable(plan: WorkoutPlans, user_id: int) -> bool:
    return plan.owner_user_id == user_id


def _serialize_exercise(ex: Exercises) -> dict:
    return {
        "exercise_id": ex.exercise_id,
        "name": ex.name,
        "muscle_group": ex.muscle_group,
        "equipment": ex.equipment,
        "training_type": ex.training_type,
        "description": ex.description,
        "is_active": ex.is_active,
        "created_at": ex.created_at.isoformat() if ex.created_at else None,
        "created_by_user_id": ex.created_by_user_id,
        "is_public": ex.is_public,
        "is_catalog_default": ex.created_by_user_id is None,
    }


def _serialize_plan_day(
    day: WorkoutPlanDays, include_exercises: bool, user_id: int
) -> dict:
    out = {
        "plan_day_id": day.plan_day_id,
        "plan_id": day.plan_id,
        "day_label": day.day_label,
        "sort_order": day.sort_order,
        "weekday": day.weekday,
        "session_time": day.session_time.isoformat() if day.session_time else None,
    }
    if include_exercises:
        rows = (
            WorkoutPlanDayExercises.query.filter_by(day_id=day.plan_day_id)
            .order_by(WorkoutPlanDayExercises.sort_order)
            .all()
        )
        out["exercises"] = []
        for row in rows:
            ex = Exercises.query.get(row.exercise_id)
            if not ex or not _exercise_visible_to_user(ex, user_id):
                continue
            out["exercises"].append(
                {
                    "day_exercise_id": row.day_exercise_id,
                    "exercise_id": row.exercise_id,
                    "exercise": _serialize_exercise(ex),
                    "sets": row.sets,
                    "reps": row.reps,
                    "weight": float(row.weight) if row.weight is not None else None,
                    "duration_minutes": row.duration_minutes,
                    "notes": row.notes,
                    "sort_order": row.sort_order,
                }
            )
    return out


def _serialize_plan(plan: WorkoutPlans, user_id: int, detail: bool) -> dict:
    owner = Users.query.get(plan.owner_user_id)
    out = {
        "plan_id": plan.plan_id,
        "owner_user_id": plan.owner_user_id,
        "owner_name": (
            f"{owner.first_name} {owner.last_name}" if owner else None
        ),
        "name": plan.name,
        "description": plan.description,
        "is_public": bool(plan.is_public),
        "copied_from_plan_id": plan.copied_from_plan_id,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }
    if detail:
        days = (
            WorkoutPlanDays.query.filter_by(plan_id=plan.plan_id)
            .order_by(WorkoutPlanDays.sort_order)
            .all()
        )
        out["days"] = [_serialize_plan_day(d, True, user_id) for d in days]
    return out


def _duplicate_plan_for_user(
    source: WorkoutPlans, owner_user_id: int, new_name: str | None
) -> WorkoutPlans:
    name = new_name or f"{source.name} (copy)"
    clone = WorkoutPlans(
        owner_user_id=owner_user_id,
        name=name[:120],
        description=source.description,
        is_public=False,
        copied_from_plan_id=source.plan_id,
    )
    db.session.add(clone)
    db.session.flush()

    day_map: dict[int, int] = {}
    days = (
        WorkoutPlanDays.query.filter_by(plan_id=source.plan_id)
        .order_by(WorkoutPlanDays.sort_order)
        .all()
    )
    for d in days:
        nd = WorkoutPlanDays(
            plan_id=clone.plan_id,
            day_label=d.day_label,
            sort_order=d.sort_order,
            weekday=d.weekday,
            session_time=d.session_time,
        )
        db.session.add(nd)
        db.session.flush()
        day_map[d.plan_day_id] = nd.plan_day_id

    for old_id, new_id in day_map.items():
        lines = WorkoutPlanDayExercises.query.filter_by(day_id=old_id).all()
        for line in lines:
            db.session.add(
                WorkoutPlanDayExercises(
                    day_id=new_id,
                    exercise_id=line.exercise_id,
                    sets=line.sets,
                    reps=line.reps,
                    weight=line.weight,
                    duration_minutes=line.duration_minutes,
                    notes=line.notes,
                    sort_order=line.sort_order,
                )
            )
    return clone


@workout_blp.route("/exercises")
class ExerciseCollection(MethodView):
    @jwt_required()
    @workout_blp.arguments(ExerciseListQuerySchema, location="query")
    @workout_blp.response(200)
    def get(self, args):
        """List exercises you can add to a plan: defaults, published customs, and your own."""
        user = _current_user()
        q = Exercises.query.filter(Exercises.is_active.is_(True))
        visibility = or_(
            Exercises.created_by_user_id.is_(None),
            Exercises.is_public.is_(True),
            Exercises.created_by_user_id == user.user_id,
        )
        q = q.filter(visibility)
        if args.get("muscle_group"):
            q = q.filter(Exercises.muscle_group == args["muscle_group"])
        if args.get("equipment"):
            q = q.filter(Exercises.equipment == args["equipment"])
        if args.get("training_type"):
            q = q.filter(Exercises.training_type == args["training_type"])
        if args.get("q"):
            like = f"%{args['q']}%"
            q = q.filter(Exercises.name.like(like))
        rows = q.order_by(Exercises.name).all()
        return {"exercises": [_serialize_exercise(e) for e in rows]}

    @jwt_required()
    @workout_blp.arguments(ExerciseCreateSchema)
    @workout_blp.response(201)
    def post(self, data):
        """Create a custom exercise; set is_public to publish it alongside defaults."""
        user = _current_user()
        ex = Exercises(
            name=data["name"],
            muscle_group=data["muscle_group"],
            equipment=data["equipment"],
            training_type=data["training_type"],
            description=data.get("description"),
            is_active=True,
            created_by_user_id=user.user_id,
            is_public=bool(data.get("is_public", False)),
        )
        db.session.add(ex)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_exercise(ex)


@workout_blp.route("/exercises/<int:exercise_id>")
class ExerciseItem(MethodView):
    @jwt_required()
    @workout_blp.response(200)
    def get(self, exercise_id):
        """Get exercise details by ID."""
        user = _current_user()
        ex = Exercises.query.get(exercise_id)
        if not ex:
            abort(404, description="Exercise not found.")
        if not _exercise_visible_to_user(ex, user.user_id):
            abort(404, description="Exercise not found.")
        return _serialize_exercise(ex)

    @jwt_required()
    @workout_blp.arguments(ExerciseUpdateSchema)
    @workout_blp.response(200)
    def patch(self, data, exercise_id):
        """Update your custom exercise (cannot edit catalog defaults)."""
        user = _current_user()
        ex = Exercises.query.get(exercise_id)
        if not ex:
            abort(404, description="Exercise not found.")
        if ex.created_by_user_id is None:
            abort(403, description="Catalog exercises cannot be edited.")
        if ex.created_by_user_id != user.user_id:
            abort(403, description="Not allowed to edit this exercise.")
        if "name" in data and data["name"] is not None:
            ex.name = data["name"]
        if "muscle_group" in data and data["muscle_group"] is not None:
            ex.muscle_group = data["muscle_group"]
        if "equipment" in data and data["equipment"] is not None:
            ex.equipment = data["equipment"]
        if "training_type" in data and data["training_type"] is not None:
            ex.training_type = data["training_type"]
        if "description" in data:
            ex.description = data["description"]
        if "is_public" in data and data["is_public"] is not None:
            ex.is_public = bool(data["is_public"])
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_exercise(ex)

    @jwt_required()
    @workout_blp.response(200)
    def delete(self, exercise_id):
        """Deactivate your custom exercise (cannot delete catalog defaults)."""
        user = _current_user()
        ex = Exercises.query.get(exercise_id)
        if not ex:
            abort(404, description="Exercise not found.")
        if ex.created_by_user_id is None:
            abort(403, description="Catalog exercises cannot be deleted.")
        if ex.created_by_user_id != user.user_id:
            abort(403, description="Not allowed.")
        ex.is_active = False
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return {"message": "Exercise deactivated."}


@workout_blp.route("/plans")
class PlanCollection(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanCreateSchema)
    @workout_blp.response(201)
    def post(self, data):
        """Create a plan shell (name, description); add days and exercises next."""
        user = _current_user()
        plan = WorkoutPlans(
            owner_user_id=user.user_id,
            name=data["name"],
            description=data.get("description"),
            is_public=bool(data.get("is_public", False)),
        )
        db.session.add(plan)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_plan(plan, user.user_id, detail=True)


@workout_blp.route("/plans/mine")
class MyPlans(MethodView):
    @jwt_required()
    @workout_blp.response(200)
    def get(self):
        """Get all workout plans you own (private and public)."""
        user = _current_user()
        plans = (
            WorkoutPlans.query.filter_by(owner_user_id=user.user_id)
            .order_by(WorkoutPlans.updated_at.desc())
            .all()
        )
        return {
            "plans": [_serialize_plan(p, user.user_id, detail=False) for p in plans]
        }


@workout_blp.route("/plans/browse")
class BrowsePlans(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanBrowseQuerySchema, location="query")
    @workout_blp.response(200)
    def get(self, args):
        """Browse published plans; filter by name or by exercises / characteristics."""
        user = _current_user()
        q = WorkoutPlans.query.filter(WorkoutPlans.is_public.is_(True))

        if args.get("q"):
            like = f"%{args['q']}%"
            q = q.filter(WorkoutPlans.name.like(like))

        def restrict_to_plan_ids(subq):
            return q.filter(WorkoutPlans.plan_id.in_(subq))

        if args.get("muscle_group"):
            sub = (
                db.session.query(WorkoutPlanDays.plan_id)
                .join(
                    WorkoutPlanDayExercises,
                    WorkoutPlanDayExercises.day_id == WorkoutPlanDays.plan_day_id,
                )
                .join(
                    Exercises,
                    Exercises.exercise_id == WorkoutPlanDayExercises.exercise_id,
                )
                .filter(
                    Exercises.muscle_group == args["muscle_group"],
                    Exercises.is_active.is_(True),
                )
                .distinct()
            )
            q = restrict_to_plan_ids(sub)

        if args.get("equipment"):
            sub = (
                db.session.query(WorkoutPlanDays.plan_id)
                .join(
                    WorkoutPlanDayExercises,
                    WorkoutPlanDayExercises.day_id == WorkoutPlanDays.plan_day_id,
                )
                .join(
                    Exercises,
                    Exercises.exercise_id == WorkoutPlanDayExercises.exercise_id,
                )
                .filter(
                    Exercises.equipment == args["equipment"],
                    Exercises.is_active.is_(True),
                )
                .distinct()
            )
            q = restrict_to_plan_ids(sub)

        if args.get("training_type"):
            sub = (
                db.session.query(WorkoutPlanDays.plan_id)
                .join(
                    WorkoutPlanDayExercises,
                    WorkoutPlanDayExercises.day_id == WorkoutPlanDays.plan_day_id,
                )
                .join(
                    Exercises,
                    Exercises.exercise_id == WorkoutPlanDayExercises.exercise_id,
                )
                .filter(
                    Exercises.training_type == args["training_type"],
                    Exercises.is_active.is_(True),
                )
                .distinct()
            )
            q = restrict_to_plan_ids(sub)

        raw_ids = args.get("exercise_ids")
        if raw_ids:
            try:
                id_list = [int(x.strip()) for x in raw_ids.split(",") if x.strip()]
            except ValueError:
                abort(400, description="exercise_ids must be comma-separated integers.")
            if id_list:
                match = args.get("exercise_match") or "any"
                if match == "any":
                    sub = (
                        db.session.query(WorkoutPlanDays.plan_id)
                        .join(
                            WorkoutPlanDayExercises,
                            WorkoutPlanDayExercises.day_id
                            == WorkoutPlanDays.plan_day_id,
                        )
                        .filter(
                            WorkoutPlanDayExercises.exercise_id.in_(id_list),
                        )
                        .distinct()
                    )
                    q = restrict_to_plan_ids(sub)
                else:
                    for ex_id in id_list:
                        sub = (
                            db.session.query(WorkoutPlanDays.plan_id)
                            .join(
                                WorkoutPlanDayExercises,
                                WorkoutPlanDayExercises.day_id
                                == WorkoutPlanDays.plan_day_id,
                            )
                            .filter(WorkoutPlanDayExercises.exercise_id == ex_id)
                            .distinct()
                        )
                        q = restrict_to_plan_ids(sub)

        plans = q.order_by(WorkoutPlans.updated_at.desc()).all()
        return {
            "plans": [_serialize_plan(p, user.user_id, detail=False) for p in plans]
        }


@workout_blp.route("/plans/<int:plan_id>")
class PlanItem(MethodView):
    @jwt_required()
    @workout_blp.response(200)
    def get(self, plan_id):
        """Get workout plan details with all days and exercises."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_readable(plan, user.user_id):
            abort(404, description="Plan not found.")
        return _serialize_plan(plan, user.user_id, detail=True)

    @jwt_required()
    @workout_blp.arguments(PlanUpdateSchema)
    @workout_blp.response(200)
    def patch(self, data, plan_id):
        """Update your workout plan (name, description, public status)."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan:
            abort(404, description="Plan not found.")
        if not _plan_writable(plan, user.user_id):
            abort(403, description="Not allowed.")
        if "name" in data and data["name"] is not None:
            plan.name = data["name"]
        if "description" in data:
            plan.description = data["description"]
        if "is_public" in data and data["is_public"] is not None:
            plan.is_public = bool(data["is_public"])
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_plan(plan, user.user_id, detail=True)


@workout_blp.route("/plans/<int:plan_id>/copy")
class PlanCopy(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanCopySchema)
    @workout_blp.response(201)
    def post(self, data, plan_id):
        """Save a personal copy of a public (or your own) plan."""
        user = _current_user()
        source = WorkoutPlans.query.get(plan_id)
        if not source:
            abort(404, description="Plan not found.")
        if not _plan_readable(source, user.user_id):
            abort(404, description="Plan not found.")
        try:
            clone = _duplicate_plan_for_user(
                source, user.user_id, data.get("name")
            )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_plan(clone, user.user_id, detail=True)


@workout_blp.route("/plans/<int:plan_id>/days")
class PlanDays(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanDayCreateSchema)
    @workout_blp.response(201)
    def post(self, data, plan_id):
        """Add a training day to the weekly layout (optional weekday and time)."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_writable(plan, user.user_id):
            abort(404, description="Plan not found.")
        day = WorkoutPlanDays(
            plan_id=plan.plan_id,
            day_label=data["day_label"],
            sort_order=data["sort_order"],
            weekday=data.get("weekday"),
            session_time=data.get("session_time"),
        )
        db.session.add(day)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_plan_day(day, True, user.user_id)


@workout_blp.route("/plans/<int:plan_id>/days/<int:day_id>")
class PlanDayItem(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanDayUpdateSchema)
    @workout_blp.response(200)
    def patch(self, data, plan_id, day_id):
        """Update training day details (label, weekday, time, order)."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_writable(plan, user.user_id):
            abort(404, description="Plan not found.")
        day = WorkoutPlanDays.query.filter_by(
            plan_day_id=day_id, plan_id=plan_id
        ).first()
        if not day:
            abort(404, description="Day not found.")
        if "day_label" in data and data["day_label"] is not None:
            day.day_label = data["day_label"]
        if "sort_order" in data and data["sort_order"] is not None:
            day.sort_order = data["sort_order"]
        if "weekday" in data:
            day.weekday = data["weekday"]
        if "session_time" in data:
            day.session_time = data["session_time"]
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return _serialize_plan_day(day, True, user.user_id)

    @jwt_required()
    @workout_blp.response(200)
    def delete(self, plan_id, day_id):
        """Remove training day and all its exercises."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_writable(plan, user.user_id):
            abort(404, description="Plan not found.")
        day = WorkoutPlanDays.query.filter_by(
            plan_day_id=day_id, plan_id=plan_id
        ).first()
        if not day:
            abort(404, description="Day not found.")
        WorkoutPlanDayExercises.query.filter_by(day_id=day_id).delete()
        db.session.delete(day)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return {"message": "Day removed."}


@workout_blp.route("/plans/<int:plan_id>/days/<int:day_id>/exercises")
class PlanDayExercises(MethodView):
    @jwt_required()
    @workout_blp.arguments(DayExerciseCreateSchema)
    @workout_blp.response(201)
    def post(self, data, plan_id, day_id):
        """Add exercise to training day with sets, reps, weight, and notes."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_writable(plan, user.user_id):
            abort(404, description="Plan not found.")
        day = WorkoutPlanDays.query.filter_by(
            plan_day_id=day_id, plan_id=plan_id
        ).first()
        if not day:
            abort(404, description="Day not found.")
        ex = Exercises.query.get(data["exercise_id"])
        if not ex or not _exercise_usable(ex, user.user_id):
            abort(400, description="Exercise not available.")
        weight = data.get("weight")
        if weight is not None and isinstance(weight, Decimal):
            weight = weight
        line = WorkoutPlanDayExercises(
            day_id=day.plan_day_id,
            exercise_id=ex.exercise_id,
            sets=data["sets"],
            reps=data["reps"],
            weight=weight,
            duration_minutes=data.get("duration_minutes"),
            notes=data.get("notes"),
            sort_order=data["sort_order"],
        )
        db.session.add(line)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return {
            "day_exercise_id": line.day_exercise_id,
            "exercise_id": line.exercise_id,
            "exercise": _serialize_exercise(ex),
            "sets": line.sets,
            "reps": line.reps,
            "weight": float(line.weight) if line.weight is not None else None,
            "duration_minutes": line.duration_minutes,
            "notes": line.notes,
            "sort_order": line.sort_order,
        }


def _exercise_usable(ex: Exercises, user_id: int) -> bool:
    return _exercise_visible_to_user(ex, user_id)


@workout_blp.route("/plans/<int:plan_id>/days/<int:day_id>/exercises/<int:de_id>")
class PlanDayExerciseItem(MethodView):
    @jwt_required()
    @workout_blp.arguments(DayExerciseUpdateSchema)
    @workout_blp.response(200)
    def patch(self, data, plan_id, day_id, de_id):
        """Update exercise details (sets, reps, weight, duration, notes). de_id = day_exercise_id from response."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_writable(plan, user.user_id):
            abort(404, description="Plan not found.")
        line = WorkoutPlanDayExercises.query.filter_by(
            day_exercise_id=de_id, day_id=day_id
        ).first()
        if not line:
            abort(404, description="Line not found.")
        day = WorkoutPlanDays.query.filter_by(
            plan_day_id=day_id, plan_id=plan_id
        ).first()
        if not day:
            abort(404, description="Day not found.")
        if "sets" in data and data["sets"] is not None:
            line.sets = data["sets"]
        if "reps" in data and data["reps"] is not None:
            line.reps = data["reps"]
        if "weight" in data:
            line.weight = data["weight"]
        if "duration_minutes" in data:
            line.duration_minutes = data["duration_minutes"]
        if "notes" in data:
            line.notes = data["notes"]
        if "sort_order" in data and data["sort_order"] is not None:
            line.sort_order = data["sort_order"]
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        ex = Exercises.query.get(line.exercise_id)
        return {
            "day_exercise_id": line.day_exercise_id,
            "exercise_id": line.exercise_id,
            "exercise": _serialize_exercise(ex) if ex else None,
            "sets": line.sets,
            "reps": line.reps,
            "weight": float(line.weight) if line.weight is not None else None,
            "duration_minutes": line.duration_minutes,
            "notes": line.notes,
            "sort_order": line.sort_order,
        }

    @jwt_required()
    @workout_blp.response(200)
    def delete(self, plan_id, day_id, de_id):
        """Remove exercise from training day. de_id = day_exercise_id from response."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_writable(plan, user.user_id):
            abort(404, description="Plan not found.")
        line = WorkoutPlanDayExercises.query.filter_by(
            day_exercise_id=de_id, day_id=day_id
        ).first()
        if not line:
            abort(404, description="Line not found.")
        db.session.delete(line)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return {"message": "Removed."}


@workout_blp.route("/plans/<int:plan_id>/assignments")
class PlanAssignments(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanAssignmentSchema)
    @workout_blp.response(201)
    def post(self, data, plan_id):
        """Attach a plan to your account with repeat metadata (schedule shell)."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_readable(plan, user.user_id):
            abort(404, description="Plan not found.")
        repeat_raw = data.get("repeat_rule") or "weekly"
        try:
            repeat_rule = RepeatRuleEnum(repeat_raw)
        except ValueError:
            abort(400, description="Invalid repeat_rule.")
        row = WorkoutPlanAssignments(
            plan_id=plan.plan_id,
            assigned_to_user_id=user.user_id,
            assigned_by_user_id=user.user_id,
            assignment_type=AssignmentTypeEnum.self,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            repeat_rule=repeat_rule,
            status=AssignmentStatusEnum.active,
        )
        db.session.add(row)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return {
            "assignment_id": row.assignment_id,
            "plan_id": row.plan_id,
            "assigned_to_user_id": row.assigned_to_user_id,
            "repeat_rule": row.repeat_rule.value if row.repeat_rule else None,
            "start_date": row.start_date.isoformat() if row.start_date else None,
            "end_date": row.end_date.isoformat() if row.end_date else None,
            "status": row.status.value if row.status else None,
        }


@workout_blp.route("/plans/<int:plan_id>/calendar")
class PlanCalendar(MethodView):
    @jwt_required()
    @workout_blp.arguments(PlanCalendarSchema)
    @workout_blp.response(201)
    def post(self, data, plan_id):
        """Place concrete sessions on the calendar for specific plan days."""
        user = _current_user()
        plan = WorkoutPlans.query.get(plan_id)
        if not plan or not _plan_readable(plan, user.user_id):
            abort(404, description="Plan not found.")
        created = []
        for occ in data["occurrences"]:
            pid = occ["plan_day_id"]
            day = WorkoutPlanDays.query.filter_by(
                plan_day_id=pid, plan_id=plan_id
            ).first()
            if not day:
                abort(400, description=f"Invalid plan_day_id {pid} for this plan.")
            cw = CalendarWorkouts(
                for_user_id=user.user_id,
                plan_day_id=pid,
                coach_id=user.user_id,
                scheduled_start=occ["scheduled_start"],
                scheduled_end=occ["scheduled_end"],
                status="scheduled",
            )
            db.session.add(cw)
            db.session.flush()
            created.append(cw.calendar_workout_id)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(500, description=str(e))
        return {"calendar_workout_ids": created}
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