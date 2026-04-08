-- Optional: seed catalog rows (created_by_user_id NULL) when not using the Python seeder.
-- Run after sql/add_workout_catalog_and_week.sql if those columns were added separately.
-- Skips duplicates by name for catalog rows only (safe to re-run only if no duplicate names in catalog).

INSERT INTO exercises (name, muscle_group, equipment, training_type, description, is_active, created_by_user_id, is_public)
SELECT 'Push-up', 'chest', 'bodyweight', 'strength', 'Hands and feet on floor; keep body straight.', 1, NULL, 0
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM exercises e WHERE e.name = 'Push-up' AND e.created_by_user_id IS NULL);

INSERT INTO exercises (name, muscle_group, equipment, training_type, description, is_active, created_by_user_id, is_public)
SELECT 'Barbell bench press', 'chest', 'barbell', 'strength', 'Flat bench; control the eccentric.', 1, NULL, 0
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM exercises e WHERE e.name = 'Barbell bench press' AND e.created_by_user_id IS NULL);

INSERT INTO exercises (name, muscle_group, equipment, training_type, description, is_active, created_by_user_id, is_public)
SELECT 'Pull-up', 'back', 'bodyweight', 'strength', 'Overhand grip; chest to bar range.', 1, NULL, 0
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM exercises e WHERE e.name = 'Pull-up' AND e.created_by_user_id IS NULL);

INSERT INTO exercises (name, muscle_group, equipment, training_type, description, is_active, created_by_user_id, is_public)
SELECT 'Barbell row', 'back', 'barbell', 'strength', 'Hinged torso; pull to lower ribs.', 1, NULL, 0
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM exercises e WHERE e.name = 'Barbell row' AND e.created_by_user_id IS NULL);

INSERT INTO exercises (name, muscle_group, equipment, training_type, description, is_active, created_by_user_id, is_public)
SELECT 'Barbell squat', 'legs', 'barbell', 'strength', 'Depth to parallel or below; bracing required.', 1, NULL, 0
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM exercises e WHERE e.name = 'Barbell squat' AND e.created_by_user_id IS NULL);
