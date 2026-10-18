"""Model/data-access functions for project records and estimate snapshots."""
from __future__ import annotations
import sqlite3
from database.db import get_connection
from backend.services.cost_calculator import calculate_estimate


def save_project(payload: dict, project_id: int | None = None) -> dict:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Project name is required.")
    if len(name) > 120:
        raise ValueError("Project name must be 120 characters or fewer.")
    description = str(payload.get("description", "")).strip()[:1000]
    project_type = str(payload.get("project_type", "Web Application")).strip()[:80]
    if not project_type:
        project_type = "Web Application"

    estimate = calculate_estimate(payload)
    team = payload.get("team", [])
    resources = payload.get("resources", [])
    testing = payload.get("testing", [])
    overhead = payload.get("overhead", [])

    with get_connection() as con:
        if project_id is not None:
            exists = con.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not exists:
                raise LookupError("Project was not found.")
            con.execute(
                """UPDATE projects SET name=?, description=?, project_type=?, duration_months=?,
                   hours_per_day=?, working_days_per_week=?, contingency_percent=?, actual_cost=?,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (name, description, project_type, float(payload["duration_months"]),
                 float(payload["hours_per_day"]), float(payload.get("working_days_per_week", 5)),
                 float(payload.get("contingency_percent", 0)), float(payload.get("actual_cost", 0) or 0), project_id),
            )
            con.execute("DELETE FROM team_members WHERE project_id=?", (project_id,))
            con.execute("DELETE FROM cost_items WHERE project_id=?", (project_id,))
        else:
            cur = con.execute(
                """INSERT INTO projects(name,description,project_type,duration_months,hours_per_day,
                   working_days_per_week,contingency_percent,actual_cost)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (name, description, project_type, float(payload["duration_months"]),
                 float(payload["hours_per_day"]), float(payload.get("working_days_per_week", 5)),
                 float(payload.get("contingency_percent", 0)), float(payload.get("actual_cost", 0) or 0)),
            )
            project_id = cur.lastrowid

        con.executemany(
            "INSERT INTO team_members(project_id,role_name,member_count,hourly_rate) VALUES(?,?,?,?)",
            [(project_id, str(row.get("role", "Team Member"))[:80], int(row.get("count", 0)),
              float(row.get("hourly_rate", 0))) for row in team],
        )
        rows = []
        for category, items in (("resource", resources), ("testing", testing), ("overhead", overhead)):
            rows.extend((project_id, category, str(row.get("name", category.title()))[:100], float(row.get("amount", 0) or 0)) for row in items)
        con.executemany(
            "INSERT INTO cost_items(project_id,category,item_name,amount) VALUES(?,?,?,?)", rows
        )
        con.execute(
            """INSERT INTO estimates(project_id,personnel_cost,resource_cost,testing_cost,overhead_cost,
               direct_cost,contingency_percent,contingency_amount,total_cost,variance)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (project_id, estimate["personnel_cost"], estimate["resource_cost"], estimate["testing_cost"],
             estimate["overhead_cost"], estimate["direct_cost"], estimate["contingency_percent"],
             estimate["contingency_amount"], estimate["total_cost"], estimate["variance"]),
        )
        con.commit()
    return get_project(project_id)


def get_project(project_id: int) -> dict | None:
    with get_connection() as con:
        project = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project:
            return None
        data = dict(project)
        data["team"] = [dict(x) for x in con.execute(
            "SELECT role_name AS role, member_count AS count, hourly_rate FROM team_members WHERE project_id=? ORDER BY id", (project_id,)
        )]
        items = [dict(x) for x in con.execute(
            "SELECT category, item_name AS name, amount FROM cost_items WHERE project_id=? ORDER BY id", (project_id,)
        )]
        data["resources"] = [{"name": x["name"], "amount": x["amount"]} for x in items if x["category"] == "resource"]
        data["testing"] = [{"name": x["name"], "amount": x["amount"]} for x in items if x["category"] == "testing"]
        data["overhead"] = [{"name": x["name"], "amount": x["amount"]} for x in items if x["category"] == "overhead"]
        estimate = con.execute("SELECT * FROM estimates WHERE project_id=? ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
        data["estimate"] = dict(estimate) if estimate else None
        data["estimate_history"] = [dict(x) for x in con.execute(
            "SELECT id,total_cost,created_at FROM estimates WHERE project_id=? ORDER BY id DESC LIMIT 5", (project_id,)
        )]
        return data


def list_projects(search: str = "") -> list[dict]:
    with get_connection() as con:
        if search.strip():
            ids = [row[0] for row in con.execute(
                "SELECT id FROM projects WHERE name LIKE ? OR project_type LIKE ? ORDER BY updated_at DESC, id DESC",
                (f"%{search.strip()}%", f"%{search.strip()}%"),
            )]
        else:
            ids = [row[0] for row in con.execute("SELECT id FROM projects ORDER BY updated_at DESC, id DESC")]
    return [get_project(project_id) for project_id in ids]


def delete_project(project_id: int) -> bool:
    with get_connection() as con:
        cur = con.execute("DELETE FROM projects WHERE id=?", (project_id,))
        con.commit()
        return cur.rowcount > 0
