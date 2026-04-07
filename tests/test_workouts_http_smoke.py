"""Lightweight HTTP checks (imports the Flask app; needs DATABASE_URL in the environment)."""
from __future__ import annotations

import os
import unittest


@unittest.skipUnless(
    os.environ.get("DATABASE_URL"),
    "Set DATABASE_URL (same as for running the server) to run smoke tests.",
)
class WorkoutHTTPSmokeTest(unittest.TestCase):
    def test_exercises_list_unauthorized(self):
        from app import app

        client = app.test_client()
        rv = client.get("/workouts/exercises")
        self.assertEqual(rv.status_code, 401)


if __name__ == "__main__":
    unittest.main()
