"""Unit tests for workout visibility / plan access helpers (no database)."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from features.workouts import (
    _exercise_visible_to_user,
    _plan_readable,
    _plan_writable,
)


def _ex(
    *,
    active: bool = True,
    creator: int | None = None,
    public: bool = False,
):
    return SimpleNamespace(
        is_active=active,
        created_by_user_id=creator,
        is_public=public,
    )


class ExerciseVisibilityTest(unittest.TestCase):
    def test_catalog_visible_to_anyone(self):
        ex = _ex(creator=None)
        self.assertTrue(_exercise_visible_to_user(ex, 1))
        self.assertTrue(_exercise_visible_to_user(ex, 999))

    def test_inactive_hidden(self):
        ex = _ex(active=False, creator=None)
        self.assertFalse(_exercise_visible_to_user(ex, 1))

    def test_private_custom_only_owner(self):
        ex = _ex(creator=5, public=False)
        self.assertTrue(_exercise_visible_to_user(ex, 5))
        self.assertFalse(_exercise_visible_to_user(ex, 6))

    def test_public_custom_visible(self):
        ex = _ex(creator=5, public=True)
        self.assertTrue(_exercise_visible_to_user(ex, 99))


class PlanAccessTest(unittest.TestCase):
    def test_owner_reads_writes(self):
        plan = SimpleNamespace(owner_user_id=3, is_public=False)
        self.assertTrue(_plan_readable(plan, 3))
        self.assertTrue(_plan_writable(plan, 3))

    def test_public_readable_not_writable_for_other(self):
        plan = SimpleNamespace(owner_user_id=3, is_public=True)
        self.assertTrue(_plan_readable(plan, 99))
        self.assertFalse(_plan_writable(plan, 99))

    def test_private_other_denied(self):
        plan = SimpleNamespace(owner_user_id=3, is_public=False)
        self.assertFalse(_plan_readable(plan, 99))


if __name__ == "__main__":
    unittest.main()
