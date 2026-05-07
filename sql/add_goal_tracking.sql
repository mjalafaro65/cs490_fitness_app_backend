-- Run against your MySQL schema when upgrading an existing database.
-- Adjust types if your deployment differs.

CREATE TABLE IF NOT EXISTS goal_progress (
    progress_id INT AUTO_INCREMENT PRIMARY KEY,
    goal_id INT NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_goal_progress_goal
        FOREIGN KEY (goal_id)
        REFERENCES goals(goal_id)
        ON DELETE CASCADE
);

-- Optional: load catalog rows via sql/seed_default_exercises.sql or python scripts/seed_default_exercises.py
