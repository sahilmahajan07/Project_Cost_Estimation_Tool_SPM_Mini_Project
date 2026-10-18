"""Cost calculation service. Kept separate from HTTP/database code for testing."""
from __future__ import annotations

WEEKS_PER_MONTH = 4.33


def calculate_estimate(payload: dict) -> dict:
    """Calculate personnel, direct, contingency and grand-total project costs.

    Personnel = sum(count * hourly_rate * hours/day * workdays/week * 4.33 * months).
    Direct = personnel + resources + testing + overhead.
    Contingency = direct * contingency percent / 100.
    Grand total = direct + contingency.
    """
    duration = float(payload.get("duration_months", 0))
    hours_per_day = float(payload.get("hours_per_day", 0))
    working_days = float(payload.get("working_days_per_week", 5))
    contingency_pct = float(payload.get("contingency_percent", 0))
    actual_cost = float(payload.get("actual_cost", 0) or 0)

    if duration <= 0:
        raise ValueError("Project duration must be greater than zero.")
    if not 0 < hours_per_day <= 24:
        raise ValueError("Working hours per day must be between 1 and 24.")
    if not 0 < working_days <= 7:
        raise ValueError("Working days per week must be between 1 and 7.")
    if not 0 <= contingency_pct <= 100:
        raise ValueError("Contingency must be between 0% and 100%.")
    if actual_cost < 0:
        raise ValueError("Actual spending cannot be negative.")

    personnel = 0.0
    for member in payload.get("team", []):
        count = int(member.get("count", 0))
        rate = float(member.get("hourly_rate", 0))
        if count < 0 or rate < 0:
            raise ValueError("Team count and hourly rates cannot be negative.")
        personnel += count * rate * hours_per_day * working_days * WEEKS_PER_MONTH * duration

    resources = _sum_items(payload.get("resources", []))
    testing = _sum_items(payload.get("testing", []))
    overhead = _sum_items(payload.get("overhead", []))
    direct = personnel + resources + testing + overhead
    contingency = direct * contingency_pct / 100
    total = direct + contingency

    return {
        "personnel_cost": round(personnel, 2),
        "resource_cost": round(resources, 2),
        "testing_cost": round(testing, 2),
        "overhead_cost": round(overhead, 2),
        "direct_cost": round(direct, 2),
        "contingency_percent": round(contingency_pct, 2),
        "contingency_amount": round(contingency, 2),
        "total_cost": round(total, 2),
        "actual_cost": round(actual_cost, 2),
        "variance": round(actual_cost - total, 2),
    }


def _sum_items(items: list[dict]) -> float:
    total = 0.0
    for item in items:
        amount = float(item.get("amount", 0) or 0)
        if amount < 0:
            raise ValueError("Cost items cannot have negative amounts.")
        total += amount
    return total
