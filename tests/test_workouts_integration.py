"""
Optional HTTP-level checks against a real DATABASE_URL.

Enable with:
  set WORKOUT_INTEGRATION_TEST=1
  python -m unittest tests.test_workouts_integration -v

Or with pytest:
  set WORKOUT_INTEGRATION_TEST=1
  pytest tests/test_workouts_integration.py -v
"""
from __future__ import annotations

import os
import unittest
import uuid


@unittest.skipUnless(
    os.environ.get("WORKOUT_INTEGRATION_TEST") == "1",
    "Set WORKOUT_INTEGRATION_TEST=1 and configure DATABASE_URL to run integration tests.",
)
class WorkoutAPIIntegrationTest(unittest.TestCase):
    def setUp(self):
        from app import app

        self.app = app
        self.client = app.test_client()
        suffix = uuid.uuid4().hex[:8]
        self._email = f"workout_test_{suffix}@example.com"
        self._password = "secret12"

    def _register_and_setup(self):
        rv = self.client.post(
            "/auth/register",
            json={"email": self._email, "password": self._password},
        )
        self.assertIn(rv.status_code, (200, 201), rv.get_data(as_text=True))
        payload = rv.get_json()
        token = payload.get("token") or payload.get("access_token")
        self.assertIsNotNone(token, payload)
        rv2 = self.client.post(
            "/auth/setup",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "Test",
                "last_name": "User",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "height": 180,
                "weight": 80,
            },
        )
        self.assertIn(rv2.status_code, (200, 201), rv2.get_data(as_text=True))
        return token

    def test_exercises_list_authenticated(self):
        token = self._register_and_setup()
        rv = self.client.get(
            "/workouts/exercises",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(rv.status_code, 200, rv.get_data(as_text=True))
        data = rv.get_json()
        self.assertIn("exercises", data)
        self.assertIsInstance(data["exercises"], list)


if __name__ == "__main__":
    unittest.main()
