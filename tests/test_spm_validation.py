"""Validation tests for SPM workspace records; no database server is needed."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.models.spm_model import _validate


class SPMValidationTests(unittest.TestCase):
    def test_requirement_needs_id_and_title(self):
        with self.assertRaisesRegex(ValueError, "Req code"):
            _validate("requirements", {"title": "A title"})
        with self.assertRaisesRegex(ValueError, "Title is required"):
            _validate("requirements", {"req_code": "FR-X", "title": " "})

    def test_requirement_valid_values_are_normalized(self):
        result = _validate("requirements", {"req_code":"NFR-X", "title":"Mobile friendly", "kind":"Non-functional", "priority":"High", "status":"Planned"})
        self.assertEqual(result["kind"], "Non-functional")
        self.assertEqual(result["priority"], "High")

    def test_task_rejects_week_outside_planning_window(self):
        payload = {"task_code":"T-X", "title":"Bad plan", "phase":"Design", "assignee":"QA Tester", "start_week":17, "duration_days":2, "effort_days":1, "status":"To Do", "priority":"High"}
        with self.assertRaisesRegex(ValueError, "Start week must be at most 16"):
            _validate("tasks", payload)

    def test_task_rejects_negative_effort(self):
        payload = {"task_code":"T-X", "title":"Bad plan", "phase":"Design", "assignee":"QA Tester", "start_week":2, "duration_days":2, "effort_days":-1, "status":"To Do", "priority":"High"}
        with self.assertRaisesRegex(ValueError, "Effort days must be at least 0"):
            _validate("tasks", payload)

    def test_risk_rejects_likelihood_outside_1_to_3(self):
        payload = {"risk_code":"R-X", "title":"Risk", "category":"Technical", "likelihood":4, "impact":3, "status":"Identified"}
        with self.assertRaisesRegex(ValueError, "Likelihood must be at most 3"):
            _validate("risks", payload)

    def test_team_capacity_must_be_positive(self):
        payload = {"name":"QA", "role":"Testing", "capacity_days":0, "hourly_rate":0}
        with self.assertRaisesRegex(ValueError, "Capacity days must be at least 0.1"):
            _validate("team", payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
