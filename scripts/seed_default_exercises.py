"""
Idempotently insert catalog exercises (created_by_user_id IS NULL).

Run from project root (with DATABASE_URL and SSL files if your Config requires them):

    python scripts/seed_default_exercises.py

Requires exercises.created_by_user_id and exercises.is_public columns (see sql/add_workout_catalog_and_week.sql).
"""
from __future__ import annotations

import os
import sys

# Project root on sys.path when executed as a file
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Defaults: (name, muscle_group, equipment, training_type, description)
CATALOG: list[tuple[str, str, str, str, str]] = [
    ("Push-up", "chest", "bodyweight", "strength", "Hands and feet on floor; keep body straight."),
    ("Barbell bench press", "chest", "barbell", "strength", "Flat bench; control the eccentric."),
    ("Pull-up", "back", "bodyweight", "strength", "Overhand grip; chest to bar range."),
    ("Barbell row", "back", "barbell", "strength", "Hinged torso; pull to lower ribs."),
    ("Overhead press", "shoulders", "barbell", "strength", "Strict press; brace the core."),
    ("Lateral raise", "shoulders", "dumbbell", "strength", "Light weight; slight bend in elbows."),
    ("Barbell squat", "legs", "barbell", "strength", "High-bar or low-bar; depth to parallel or below."),
    ("Romanian deadlift", "legs", "barbell", "strength", "Hip hinge; slight knee bend."),
    ("Plank", "core", "bodyweight", "endurance", "Forearms or hands; neutral spine."),
    ("Running (easy)", "cardio", "none", "cardio", "Conversational-pace continuous run."),
    ("Kettlebell swing", "legs", "kettlebell", "power", "Hip extension drives the bell."),
    ("Cycling (moderate)", "cardio", "bike", "cardio", "Steady aerobic effort on bike."),
]


def seed() -> tuple[int, int]:
    """Returns (inserted_count, skipped_count)."""
    from app import app
    from db import db
    from models import Exercises

    inserted = 0
    skipped = 0
    with app.app_context():
        for name, muscle, equip, train_type, desc in CATALOG:
            exists = (
                Exercises.query.filter(
                    Exercises.name == name,
                    Exercises.created_by_user_id.is_(None),
                ).first()
            )
            if exists:
                skipped += 1
                continue
            db.session.add(
                Exercises(
                    name=name[:120],
                    muscle_group=muscle[:60],
                    equipment=equip[:60],
                    training_type=train_type[:60],
                    description=desc,
                    is_active=True,
                    created_by_user_id=None,
                    is_public=False,
                )
            )
            inserted += 1
        db.session.commit()
    return inserted, skipped


def main() -> None:
    ins, sk = seed()
    print(f"Catalog seed done: {ins} inserted, {sk} already present.")


if __name__ == "__main__":
    main()
