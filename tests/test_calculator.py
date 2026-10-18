import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.services.cost_calculator import calculate_estimate


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "duration_months": 1,
            "hours_per_day": 8,
            "working_days_per_week": 5,
            "contingency_percent": 10,
            "actual_cost": 0,
            "team": [{"role": "Developer", "count": 1, "hourly_rate": 100}],
            "resources": [{"name": "Cloud", "amount": 1000}],
            "testing": [{"name": "QA", "amount": 500}],
            "overhead": [{"name": "Admin", "amount": 250}],
        }

    def test_personnel_formula_and_total(self):
        result = calculate_estimate(self.payload)
        self.assertEqual(result["personnel_cost"], 17320.0)
        self.assertEqual(result["direct_cost"], 19070.0)
        self.assertEqual(result["contingency_amount"], 1907.0)
        self.assertEqual(result["total_cost"], 20977.0)

    def test_invalid_duration_rejected(self):
        self.payload["duration_months"] = 0
        with self.assertRaisesRegex(ValueError, "duration"):
            calculate_estimate(self.payload)

    def test_contingency_bounds_rejected(self):
        self.payload["contingency_percent"] = 150
        with self.assertRaisesRegex(ValueError, "Contingency"):
            calculate_estimate(self.payload)

    def test_actual_variance(self):
        self.payload["actual_cost"] = 25000
        result = calculate_estimate(self.payload)
        self.assertEqual(result["variance"], 4023.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
