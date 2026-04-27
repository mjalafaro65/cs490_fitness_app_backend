from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from datetime import date
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy import func
from datetime import datetime, timedelta
from models import (
    Users,
    DailySurvey,
    CalendarWorkouts,
    WorkoutLogs,
    WorkoutLogEntries,
    Exercises,
    Goals,MealLogs,Meals
    
)

insights_blp  = Blueprint("insights", __name__, url_prefix="/insights")


# survey — mood, energy, sleep, water, weight
@insights_blp.route("/survey")
class SurveyProgressView(MethodView):
    @jwt_required()
    def get(self):
        
        auth_id = get_jwt_identity()

        client_id = request.args.get("client_id", type=int)
        user = resolve_target_user(auth_id, client_id)

        days = request.args.get("days", 30, type=int)
        since = datetime.utcnow() - timedelta(days=days)

        surveys = (
            DailySurvey.query
            .filter(
                DailySurvey.user_id == user.user_id,
                DailySurvey.date >= since.date()
            )
            .order_by(DailySurvey.date.asc())
            .all()
        )

        print("SINCE:", since.date())
        print("SURVEYS FOUND:", len(surveys))
        for s in surveys:
            print("ROW:", s.date, s.mood_score)
                

        history = [
            {
                "date": s.date.isoformat(),
                "mood_score": s.mood_score,
                "energy_level": s.energy_level,
                "sleep_hours": float(s.sleep_hours) if s.sleep_hours else None,
                "water_oz": float(s.water_oz) if s.water_oz else None,
                "weight_lbs": float(s.weight_lbs) if s.weight_lbs else None,
                "notes": s.notes,
            }
            for s in surveys
        ]

        # simple averages for summary cards
        filled = [s for s in surveys if s.mood_score is not None]
        avg_mood   = round(sum(s.mood_score for s in filled) / len(filled), 1) if filled else None
        filled_e   = [s for s in surveys if s.energy_level is not None]
        avg_energy = round(sum(s.energy_level for s in filled_e) / len(filled_e), 1) if filled_e else None
        filled_sl  = [s for s in surveys if s.sleep_hours is not None]
        avg_sleep  = round(sum(float(s.sleep_hours) for s in filled_sl) / len(filled_sl), 1) if filled_sl else None

        # weight change (first vs last recorded)
        weights = [s for s in surveys if s.weight_lbs is not None]
        weight_change = None
        if len(weights) >= 2:
            weight_change = round(float(weights[-1].weight_lbs) - float(weights[0].weight_lbs), 1)

        return {
            "user_id": user.user_id,
            "period_days": days,
            "summary": {
                "avg_mood": avg_mood,
                "avg_energy": avg_energy,
                "avg_sleep_hours": avg_sleep,
                "weight_change_lbs": weight_change,
                "total_entries": len(surveys),
            },
            "history": history,
        }, 200


# ─────────────────────────────────────────────
# 2. WORKOUTS — completion rate, streaks
# ─────────────────────────────────────────────
@insights_blp.route("/workouts")
class WorkoutProgressView(MethodView):
    @jwt_required()
    def get(self):
        auth_id = get_jwt_identity()
        client_id = request.args.get("client_id", type=int)
        user = resolve_target_user(auth_id, client_id)      

        days = request.args.get("days", 30, type=int)
        since = datetime.utcnow() - timedelta(days=days)

        workouts = (
            CalendarWorkouts.query
            .filter(
                CalendarWorkouts.for_user_id == user.user_id,
                CalendarWorkouts.scheduled_start >= since
            )
            .order_by(CalendarWorkouts.scheduled_start.asc())
            .all()
        )

        total     = len(workouts)
        completed = sum(1 for w in workouts if w.status == "completed")
        skipped   = sum(1 for w in workouts if w.status == "skipped")
        scheduled = sum(1 for w in workouts if w.status == "scheduled")
        canceled  = sum(1 for w in workouts if w.status == "canceled")

        completion_rate = round(completed / total * 100, 1) if total else 0

        # current streak — consecutive completed days going back from today
        completed_dates = sorted(set(
            w.scheduled_start.date()
            for w in workouts if w.status == "completed"
        ), reverse=True)

        streak = 0
        check = datetime.utcnow().date()
        for d in completed_dates:
            if d == check or d == check - timedelta(days=1):
                streak += 1
                check = d
            else:
                break

        history = [
            {
                "date": w.scheduled_start.date().isoformat(),
                "scheduled_start": w.scheduled_start.isoformat(),
                "scheduled_end": w.scheduled_end.isoformat() if w.scheduled_end else None,
                "status": w.status,
                "plan_day_id": w.plan_day_id,
            }
            for w in workouts
        ]

        return {
            "user_id": user.user_id,
            "period_days": days,
            "summary": {
                "total": total,
                "completed": completed,
                "skipped": skipped,
                "scheduled": scheduled,
                "canceled": canceled,
                "completion_rate": completion_rate,
                "current_streak_days": streak,
            },
            "history": history,
        }, 200


# 3. STRENGTH — exercise volume over time

@insights_blp.route("/strength")
class StrengthProgressView(MethodView):
    @jwt_required()
    def get(self):
        auth_id = get_jwt_identity()
        client_id = request.args.get("client_id", type=int)
        user = resolve_target_user(auth_id, client_id)  

        days        = request.args.get("days", 90, type=int)
        exercise_id = request.args.get("exercise_id", type=int)  # optional filter
        since       = datetime.utcnow() - timedelta(days=days)

        query = (
            db.session.query(WorkoutLogs, WorkoutLogEntries, Exercises)
            .join(WorkoutLogEntries, WorkoutLogs.workout_log_id == WorkoutLogEntries.workout_log_id)
            .join(Exercises, WorkoutLogEntries.exercise_id == Exercises.exercise_id)
            .filter(
                WorkoutLogs.user_id == user.user_id,
                WorkoutLogs.logged_at >= since
            )
            .order_by(WorkoutLogs.logged_at.asc())
        )

        if exercise_id:
            query = query.filter(WorkoutLogEntries.exercise_id == exercise_id)

        rows = query.all()

        # group by exercise for frontend charting
        from collections import defaultdict
        by_exercise = defaultdict(list)

        for log, entry, exercise in rows:
            sets   = entry.sets or 0
            reps   = entry.reps or 0
            weight = float(entry.weight) if entry.weight else 0
            volume = sets * reps * weight  # total volume load

            by_exercise[exercise.name].append({
                "date": log.logged_at.date().isoformat(),
                "sets": entry.sets,
                "reps": entry.reps,
                "weight": float(entry.weight) if entry.weight else None,
                "volume": round(volume, 2),
                "notes": entry.notes,
            })

        # personal bests per exercise
        pbs = {}
        for name, sessions in by_exercise.items():
            weights = [s["weight"] for s in sessions if s["weight"]]
            pbs[name] = max(weights) if weights else None

        return {
            "user_id": user.user_id,
            "period_days": days,
            "personal_bests": pbs,
            "exercises": dict(by_exercise),
        }, 200


# 4 NUTRITION — calorie and macro trends
@insights_blp.route("/nutrition")
class NutritionProgressView(MethodView):
    @jwt_required()
    def get(self):
        auth_id = get_jwt_identity()
        client_id = request.args.get("client_id", type=int)
        user = resolve_target_user(auth_id, client_id) 
        days  = request.args.get("days", 30, type=int)
        since = datetime.utcnow() - timedelta(days=days)

        rows = (
            db.session.query(MealLogs, Meals)
            .join(Meals, MealLogs.meal_id == Meals.meal_id)
            .filter(
                MealLogs.user_id == user.user_id,
                MealLogs.logged_at >= since
            )
            .order_by(MealLogs.logged_at.asc())
            .all()
        )

        # group by date for daily totals
        from collections import defaultdict
        daily = defaultdict(lambda: {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals": []})

        for ml, m in rows:
            servings = float(ml.servings)
            date_key = ml.logged_at.date().isoformat()

            calories  = int(m.calories  * servings) if m.calories  else 0
            protein_g = float(m.protein_g * servings) if m.protein_g else 0
            carbs_g   = float(m.carbs_g   * servings) if m.carbs_g   else 0
            fat_g     = float(m.fat_g     * servings) if m.fat_g     else 0

            daily[date_key]["calories"]  += calories
            daily[date_key]["protein_g"] += round(protein_g, 1)
            daily[date_key]["carbs_g"]   += round(carbs_g, 1)
            daily[date_key]["fat_g"]     += round(fat_g, 1)
            daily[date_key]["meals"].append({
                "meal_name": m.name,
                "servings": servings,
                "calories": calories,
                "protein_g": round(protein_g, 1),
                "carbs_g": round(carbs_g, 1),
                "fat_g": round(fat_g, 1),
            })

        history = [{"date": date, **data} for date, data in sorted(daily.items())]

        # overall averages
        if history:
            avg_calories  = round(sum(d["calories"]  for d in history) / len(history), 1)
            avg_protein   = round(sum(d["protein_g"] for d in history) / len(history), 1)
            avg_carbs     = round(sum(d["carbs_g"]   for d in history) / len(history), 1)
            avg_fat       = round(sum(d["fat_g"]     for d in history) / len(history), 1)
        else:
            avg_calories = avg_protein = avg_carbs = avg_fat = None

        return {
            "user_id": user.user_id,
            "period_days": days,
            "summary": {
                "avg_daily_calories": avg_calories,
                "avg_protein_g": avg_protein,
                "avg_carbs_g": avg_carbs,
                "avg_fat_g": avg_fat,
                "days_logged": len(history),
            },
            "history": history,
        }, 200



# 5. GOALS — active goals + progress

@insights_blp.route("/goals")
class GoalsProgressView(MethodView):
    @jwt_required()
    def get(self):
        auth_id = get_jwt_identity()
        client_id = request.args.get("client_id", type=int)
        user = resolve_target_user(auth_id, client_id) 

        goals = (
            Goals.query
            .filter_by(for_user_id=user.user_id)
            .order_by(Goals.created_at.desc())
            .all()
        )

        # get latest weight from daily survey for weight goals
        latest_survey = (
            DailySurvey.query
            .filter(
                DailySurvey.user_id == user.user_id,
                DailySurvey.weight_lbs.isnot(None)
            )
            .order_by(DailySurvey.date.desc())
            .first()
        )
        current_weight = float(latest_survey.weight_lbs) if latest_survey else None

        def calc_progress(goal):
            """Returns 0-100 percentage where possible."""
            if goal.goal_type == "weight" and goal.target_value and current_weight:
                # need start weight — pull first survey on/after start_date
                start_survey = (
                    DailySurvey.query
                    .filter(
                        DailySurvey.user_id == user.user_id,
                        DailySurvey.date >= goal.start_date,
                        DailySurvey.weight_lbs.isnot(None)
                    )
                    .order_by(DailySurvey.date.asc())
                    .first()
                )
                if start_survey:
                    start_w  = float(start_survey.weight_lbs)
                    target_w = float(goal.target_value)
                    total_change = start_w - target_w  # losing weight
                    current_change = start_w - current_weight
                    if total_change != 0:
                        return round(min(max(current_change / total_change * 100, 0), 100), 1)
            return None

        result = [
            {
                "goal_id": g.goal_id,
                "title": g.title,
                "goal_type": g.goal_type,
                "status": g.status,
                "target_value": float(g.target_value) if g.target_value else None,
                "unit": g.unit,
                "start_date": g.start_date.isoformat() if g.start_date else None,
                "end_date": g.end_date.isoformat() if g.end_date else None,
                "description": g.description,
                "progress_pct": calc_progress(g),
                "days_remaining": (
                    (g.end_date - datetime.utcnow().date()).days
                    if g.end_date else None
                ),
            }
            for g in goals
        ]

        active    = sum(1 for g in goals if g.status == "active")
        completed = sum(1 for g in goals if g.status == "completed")

        return {
            "user_id": user.user_id,
            "summary": {
                "total": len(goals),
                "active": active,
                "completed": completed,
            },
            "goals": result,
        }, 200


# 6. SUMMARY — lightweight dashboard snapshot
@insights_blp.route("/summary")
class ProgressSummaryView(MethodView):
    @jwt_required()
    def get(self):
        auth_id = get_jwt_identity()
        client_id = request.args.get("client_id", type=int)
        user = resolve_target_user(auth_id, client_id)   
        uid = user.user_id

        # latest survey entry
        latest_survey = (
            DailySurvey.query
            .filter_by(user_id=uid)
            .order_by(DailySurvey.date.desc())
            .first()
        )

        # last completed workout
        last_workout = (
            CalendarWorkouts.query
            .filter_by(for_user_id=uid, status="completed")
            .order_by(CalendarWorkouts.scheduled_start.desc())
            .first()
        )

        # 30-day completion rate
        since = datetime.utcnow() - timedelta(days=30)
        recent_workouts = CalendarWorkouts.query.filter(
            CalendarWorkouts.for_user_id == uid,
            CalendarWorkouts.scheduled_start >= since
        ).all()
        total     = len(recent_workouts)
        completed = sum(1 for w in recent_workouts if w.status == "completed")
        completion_rate = round(completed / total * 100, 1) if total else 0

        # active goal count
        active_goals = Goals.query.filter_by(for_user_id=uid, status="active").count()

        return {
            "user_id": uid,
            "latest_weight_lbs": float(latest_survey.weight_lbs) if latest_survey and latest_survey.weight_lbs else None,
            "latest_mood": latest_survey.mood_score if latest_survey else None,
            "latest_energy": latest_survey.energy_level if latest_survey else None,
            "last_workout_date": last_workout.scheduled_start.date().isoformat() if last_workout else None,
            "completion_rate_30d": completion_rate,
            "active_goals": active_goals,
        }, 200


# helper — put this above your routes
def resolve_target_user(auth_id, client_id_param):
    """
    Returns the target user. 
    - If no client_id: returns the calling user (client viewing own data)
    - If client_id: verifies the caller is a coach with an active relationship
    """
    from models import CoachClientRelationships, CoachProfiles


    caller = Users.query.filter_by(auth_id=auth_id).first()
    print(auth_id)
    if not caller:
        abort(404, message="User not found")

    if not client_id_param:
        return caller  # client viewing their own data

    # caller is trying to view someone else — must be their coach
    client = Users.query.filter_by(user_id=client_id_param).first()
    if not client:
        abort(404, message="Client not found")

    coach_profile = CoachProfiles.query.filter_by(user_id=caller.user_id).first()
    if not coach_profile:
        abort(403, message="You are not a coach")

    relationship = CoachClientRelationships.query.filter_by(
        coach_profile_id=coach_profile.coach_profile_id,
        client_user_id=client.user_id,
        status="active"
    ).first()

    if not relationship:
        abort(403, message="No active coaching relationship with this client")

    return client