-- Run against your MySQL schema when upgrading an existing database.
-- Adjust types if your deployment differs.

ALTER TABLE exercises
  ADD COLUMN created_by_user_id INT NULL,
  ADD COLUMN is_public TINYINT(1) NOT NULL DEFAULT 0,
  ADD CONSTRAINT fk_exercises_created_by_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id);

ALTER TABLE workout_plans
  ADD COLUMN copied_from_plan_id INT NULL,
  ADD CONSTRAINT fk_workout_plans_copied_from
    FOREIGN KEY (copied_from_plan_id) REFERENCES workout_plans(plan_id);

ALTER TABLE workout_plan_days
  ADD COLUMN weekday INT NULL,
  ADD COLUMN session_time TIME NULL;

-- Optional: load catalog rows via sql/seed_default_exercises.sql or python scripts/seed_default_exercises.py
