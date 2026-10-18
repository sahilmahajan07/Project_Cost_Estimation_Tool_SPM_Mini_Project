"""Data-access and validation for the SPM workspace (requirements, plan, risks, team, SCM)."""
from __future__ import annotations
import sqlite3
from database.db import get_connection

VALID = {
    "requirements": {
        "kind": {"Functional", "Non-functional"},
        "priority": {"High", "Medium", "Low"},
        "status": {"Planned", "In Progress", "Implemented", "Tested"},
    },
    "tasks": {
        "status": {"To Do", "In Progress", "Testing / Review", "Done"},
        "priority": {"High", "Medium", "Low"},
    },
    "risks": {"status": {"Identified", "Monitoring", "Mitigating", "Closed"}},
    "team": {},
    "changes": {
        "change_type": {"Commit", "Branch", "Requirement", "Release", "Review"},
        "status": {"Planned", "In Review", "Accepted", "Completed"},
    },
}
TABLES = {"requirements": "spm_requirements", "tasks": "spm_tasks", "risks": "spm_risks", "team": "spm_team_members", "changes": "spm_changes"}
FIELDS = {
    "requirements": ("req_code", "title", "kind", "priority", "status", "description", "acceptance_criteria"),
    "tasks": ("task_code", "title", "phase", "assignee", "start_week", "duration_days", "effort_days", "status", "priority", "dependencies"),
    "risks": ("risk_code", "title", "category", "likelihood", "impact", "mitigation", "contingency", "owner", "status"),
    "team": ("name", "role", "capacity_days", "hourly_rate", "skills"),
    "changes": ("change_type", "branch_name", "summary", "author", "status"),
}
TEXT_LIMITS = {"title": 180, "description": 1500, "acceptance_criteria": 1000, "mitigation": 1200, "contingency": 1000, "skills": 600, "dependencies": 400, "summary": 1200, "name": 120, "role": 100, "assignee": 120, "owner": 120, "phase": 100, "category": 100, "branch_name": 200, "req_code": 30, "task_code": 30, "risk_code": 30, "author": 120}


def _text(payload, field, default="", required=False):
    value = str(payload.get(field, default) if payload.get(field, default) is not None else default).strip()
    if required and not value:
        raise ValueError(f"{field.replace('_', ' ').capitalize()} is required.")
    if len(value) > TEXT_LIMITS.get(field, 1500):
        raise ValueError(f"{field.replace('_', ' ').capitalize()} is too long.")
    return value


def _number(payload, field, default, minimum=None, maximum=None, integer=False):
    raw = payload.get(field, default)
    try:
        value = int(raw) if integer else float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{field.replace('_', ' ').capitalize()} must be numeric.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field.replace('_', ' ').capitalize()} must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{field.replace('_', ' ').capitalize()} must be at most {maximum}.")
    return value


def _validate(kind, payload, existing=None):
    if kind not in TABLES:
        raise ValueError("Unknown SPM resource.")
    data = dict(existing or {})
    for field in FIELDS[kind]:
        if field in payload:
            data[field] = payload[field]
    # defaults for new items
    defaults = {
        "requirements": {"kind": "Functional", "priority": "Medium", "status": "Planned", "description": "", "acceptance_criteria": ""},
        "tasks": {"phase": "Development", "assignee": "Unassigned", "start_week": 1, "duration_days": 1, "effort_days": 1, "status": "To Do", "priority": "Medium", "dependencies": ""},
        "risks": {"category": "Technical", "likelihood": 2, "impact": 2, "mitigation": "", "contingency": "", "owner": "Project Manager", "status": "Identified"},
        "team": {"hourly_rate": 0, "skills": ""},
        "changes": {"branch_name": "main", "author": "Project Team", "status": "Planned"},
    }[kind]
    for key, value in defaults.items():
        data.setdefault(key, value)
    if kind == "requirements":
        data["req_code"] = _text(data, "req_code", required=True)
        data["title"] = _text(data, "title", required=True)
        data["kind"] = _choice(data, kind, "kind")
        data["priority"] = _choice(data, kind, "priority")
        data["status"] = _choice(data, kind, "status")
        data["description"] = _text(data, "description")
        data["acceptance_criteria"] = _text(data, "acceptance_criteria")
    elif kind == "tasks":
        data["task_code"] = _text(data, "task_code", required=True)
        data["title"] = _text(data, "title", required=True)
        data["phase"] = _text(data, "phase", required=True)
        data["assignee"] = _text(data, "assignee", "Unassigned", required=True)
        data["start_week"] = _number(data, "start_week", 1, 1, 16, True)
        data["duration_days"] = _number(data, "duration_days", 1, 0.1, 180)
        data["effort_days"] = _number(data, "effort_days", 1, 0, 365)
        data["status"] = _choice(data, kind, "status")
        data["priority"] = _choice(data, kind, "priority")
        data["dependencies"] = _text(data, "dependencies")
    elif kind == "risks":
        data["risk_code"] = _text(data, "risk_code", required=True)
        data["title"] = _text(data, "title", required=True)
        data["category"] = _text(data, "category", "Technical", required=True)
        data["likelihood"] = _number(data, "likelihood", 2, 1, 3, True)
        data["impact"] = _number(data, "impact", 2, 1, 3, True)
        data["mitigation"] = _text(data, "mitigation")
        data["contingency"] = _text(data, "contingency")
        data["owner"] = _text(data, "owner", "Project Manager", required=True)
        data["status"] = _choice(data, kind, "status")
    elif kind == "team":
        data["name"] = _text(data, "name", required=True)
        data["role"] = _text(data, "role", required=True)
        data["capacity_days"] = _number(data, "capacity_days", None, 0.1, 365)
        data["hourly_rate"] = _number(data, "hourly_rate", 0, 0, 1000000)
        data["skills"] = _text(data, "skills")
    else:
        data["change_type"] = _choice(data, kind, "change_type")
        data["branch_name"] = _text(data, "branch_name", "main", required=True)
        data["summary"] = _text(data, "summary", required=True)
        data["author"] = _text(data, "author", "Project Team", required=True)
        data["status"] = _choice(data, kind, "status")
    return {field: data[field] for field in FIELDS[kind]}


def _choice(data, kind, field):
    value = str(data.get(field, "")).strip()
    if value not in VALID[kind][field]:
        raise ValueError(f"Invalid {field.replace('_', ' ')} value.")
    return value


def _enhance(kind, row):
    data = dict(row)
    if kind == "risks":
        score = int(data["likelihood"]) * int(data["impact"])
        data["score"] = score
        data["severity"] = "High" if score >= 6 else ("Medium" if score >= 3 else "Low")
    return data


def list_items(kind):
    table = TABLES[kind]
    with get_connection() as con:
        rows = [dict(row) for row in con.execute(f"SELECT * FROM {table} ORDER BY id DESC")]
        if kind == "team":
            for row in rows:
                allocated = con.execute("SELECT COALESCE(SUM(effort_days),0) FROM spm_tasks WHERE lower(assignee)=lower(?)", (row["name"],)).fetchone()[0]
                row["allocated_days"] = round(float(allocated), 2)
                row["utilization_pct"] = round(float(allocated) / float(row["capacity_days"]) * 100, 1) if row["capacity_days"] else 0
        return [_enhance(kind, row) for row in rows]


def create_item(kind, payload):
    data = _validate(kind, payload)
    table = TABLES[kind]
    columns = list(data.keys())
    qcols = ",".join(columns)
    marks = ",".join("?" for _ in columns)
    with get_connection() as con:
        try:
            cur = con.execute(f"INSERT INTO {table} ({qcols}) VALUES ({marks})", [data[c] for c in columns])
            con.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Could not save {kind[:-1] if kind.endswith('s') else kind}; check that its code/name is unique and values are valid.") from exc
        row = con.execute(f"SELECT * FROM {table} WHERE id=?", (cur.lastrowid,)).fetchone()
        return _enhance(kind, row)


def update_item(kind, item_id, payload):
    table = TABLES[kind]
    with get_connection() as con:
        row = con.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise LookupError("SPM record was not found.")
        current = dict(row)
        # Ignore generated columns; only take known editable fields.
        data = _validate(kind, {k:v for k,v in payload.items() if k in FIELDS[kind]}, current)
        columns = list(data.keys())
        assignments = ",".join(f"{col}=?" for col in columns)
        try:
            con.execute(f"UPDATE {table} SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=?", [data[c] for c in columns] + [item_id])
            con.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Could not update record; check unique codes/names and values.") from exc
        updated = con.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
        return _enhance(kind, updated)


def delete_item(kind, item_id):
    table = TABLES[kind]
    with get_connection() as con:
        cur = con.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
        con.commit()
        return cur.rowcount > 0


def workspace_data():
    requirements = list_items("requirements")
    tasks = list_items("tasks")
    risks = list_items("risks")
    team = list_items("team")
    changes = list_items("changes")
    status_counts = {status: sum(1 for t in tasks if t["status"] == status) for status in ("To Do", "In Progress", "Testing / Review", "Done")}
    score_bands = {"High": sum(1 for r in risks if r["severity"] == "High" and r["status"] != "Closed"), "Medium": sum(1 for r in risks if r["severity"] == "Medium" and r["status"] != "Closed"), "Low": sum(1 for r in risks if r["severity"] == "Low" and r["status"] != "Closed")}
    effort_total = round(sum(float(t["effort_days"]) for t in tasks), 2)
    effort_done = round(sum(float(t["effort_days"]) for t in tasks if t["status"] == "Done"), 2)
    return {
        "requirements": requirements, "tasks": tasks, "risks": risks, "team": team, "changes": changes,
        "metrics": {
            "requirements": len(requirements), "tasks": len(tasks), "tasks_done": status_counts["Done"],
            "open_risks": sum(1 for r in risks if r["status"] != "Closed"), "team_members": len(team),
            "total_capacity_days": round(sum(float(m["capacity_days"]) for m in team), 2),
            "allocated_effort_days": round(sum(float(m["allocated_days"]) for m in team), 2),
            "planned_effort_days": effort_total, "completed_effort_days": effort_done,
            "task_status_counts": status_counts, "risk_severity_counts": score_bands,
        },
    }


def seed_spm_data():
    """Insert illustrative starting records once; all are editable from the UI."""
    sample_requirements = [
        ("FR-03", "Create and save project estimates", "Functional", "High", "Implemented", "Capture project details, duration, team rates and cost items.", "A saved project appears in project history."),
        ("FR-09", "Calculate estimated project cost", "Functional", "High", "Tested", "Calculate personnel, direct, contingency and total costs on the server.", "Calculated total equals direct cost plus contingency."),
        ("FR-12", "Show dashboard and cost breakdown", "Functional", "High", "Implemented", "Display portfolio totals and category-wise cost contribution.", "Dashboard loads saved estimates and breakdown values."),
        ("FR-15", "Generate PDF and Excel reports", "Functional", "High", "Planned", "Provide downloadable report files for each saved estimate.", "PDF and XLSX export contain project details and itemized costs."),
        ("NFR-04", "Provide a usable responsive interface", "Non-functional", "Medium", "Implemented", "Provide clear navigation and responsive forms for desktop and mobile widths.", "Core forms remain usable at common screen sizes."),
        ("NFR-02", "Secure login and role-based permissions", "Non-functional", "High", "Planned", "Authenticate users and enforce permissions by role before production use.", "Unauthenticated users cannot access protected endpoints."),
    ]
    sample_tasks = [
        ("T-01", "Requirement gathering and SRS", "Planning & Analysis", "System Analyst", 1, 5, 5, "Done", "High", ""),
        ("T-02", "System and database design", "Design", "Database Developer", 3, 4, 5, "Done", "High", "T-01"),
        ("T-03", "Authentication and role management", "Development", "Backend Developer (Core)", 5, 5, 4, "To Do", "High", "T-02"),
        ("T-04", "Project creation and parameter input", "Development", "Backend Developer (Core)", 5, 8, 6, "Done", "High", "T-03"),
        ("T-05", "Cost calculation engine", "Development", "Backend Developer (Core)", 6, 10, 8, "Done", "High", "T-04"),
        ("T-06", "Dashboard and data visualization", "Development", "Frontend Developer", 8, 7, 7, "Done", "High", "T-05"),
        ("T-07", "PDF and Excel report generation", "Development", "Backend Developer (Reports)", 9, 6, 5, "To Do", "High", "T-05"),
        ("T-08", "Budget comparison and tracking", "Development", "Frontend Developer", 9, 5, 5, "Done", "Medium", "T-05"),
        ("T-09", "Notifications and project search", "Development", "Backend Developer (Reports)", 10, 4, 3, "To Do", "Medium", "T-04"),
        ("T-10", "Unit, integration and acceptance testing", "Testing & Deployment", "QA Tester", 12, 7, 7, "In Progress", "High", "T-06, T-07, T-08, T-09"),
        ("T-11", "Deployment and documentation", "Testing & Deployment", "Project Manager", 15, 3, 3, "In Progress", "Medium", "T-10"),
    ]
    sample_risks = [
        ("R1", "Incorrect cost calculation", "Technical", 2, 3, "Maintain unit tests for the cost formula; review changes and check edge cases.", "Roll back the calculation change and use a manually verified estimate for critical decisions.", "Backend Developer (Core)", "Monitoring"),
        ("R2", "Requirement changes late in the project", "Scope", 2, 3, "Record and review each change request; assess schedule and effort impact.", "Re-baseline the work plan after project manager approval.", "Project Manager", "Monitoring"),
        ("R3", "Data loss or database corruption", "Operational", 2, 3, "Keep source-controlled schema scripts and schedule database backups before deployment.", "Restore a verified backup and replay confirmed changes.", "Database Developer", "Identified"),
        ("R4", "Authentication and access control incomplete", "Security", 2, 3, "Keep authentication marked as a release blocker and review access requirements before production.", "Restrict the prototype to local demo use until access control is implemented.", "Project Manager", "Mitigating"),
        ("R5", "Schedule slippage due to uneven workload", "Schedule", 2, 2, "Review task effort and role workload weekly; reassign work when capacity is exceeded.", "Move lower-priority work to a later milestone and update the plan.", "Project Manager", "Monitoring"),
        ("R6", "PDF/Excel reporting implementation delay", "Technical", 2, 2, "Prototype report format early and test output against saved estimates.", "Deliver CSV export as an interim option and defer PDF/XLSX to a later increment.", "Backend Developer (Reports)", "Identified"),
    ]
    sample_team = [
        ("Project Manager", "Planning & Coordination", 8, 600, "Scheduling, reviews, stakeholder coordination, release readiness"),
        ("System Analyst", "Requirements & Documentation", 5, 500, "SRS, acceptance criteria, requirement traceability"),
        ("Database Developer", "Database Design", 5, 550, "SQLite schema, data integrity, backup planning"),
        ("Backend Developer (Core)", "Backend Development", 18, 550, "Python API, project CRUD, cost calculation"),
        ("Frontend Developer", "Frontend Development", 12, 500, "HTML, CSS, JavaScript, dashboard, task UI"),
        ("Backend Developer (Reports)", "Reports & Integrations", 8, 550, "PDF/Excel, notifications, search endpoints"),
        ("QA Tester", "Testing & Quality", 8, 350, "Unit, integration and acceptance testing"),
    ]
    sample_changes = [
        ("Commit", "main", "Initial project cost estimation prototype and normalized SQL setup", "Project Team", "Completed"),
        ("Branch", "assignment-7-scm", "Created Assignment 7 SCM branch for versioned documentation", "Saiesh Wala", "Completed"),
        ("Commit", "assignment-7-scm", "Added SCM_README.md and pushed to the shared GitHub repository", "Saiesh Wala", "Completed"),
        ("Review", "assignment-7-scm", "Review and merge the SCM documentation through a pull request if required by the team workflow", "Project Manager", "Planned"),
    ]
    with get_connection() as con:
        if con.execute("SELECT COUNT(*) FROM spm_requirements").fetchone()[0] == 0:
            con.executemany("INSERT INTO spm_requirements(req_code,title,kind,priority,status,description,acceptance_criteria) VALUES(?,?,?,?,?,?,?)", sample_requirements)
        if con.execute("SELECT COUNT(*) FROM spm_tasks").fetchone()[0] == 0:
            con.executemany("INSERT INTO spm_tasks(task_code,title,phase,assignee,start_week,duration_days,effort_days,status,priority,dependencies) VALUES(?,?,?,?,?,?,?,?,?,?)", sample_tasks)
        if con.execute("SELECT COUNT(*) FROM spm_risks").fetchone()[0] == 0:
            con.executemany("INSERT INTO spm_risks(risk_code,title,category,likelihood,impact,mitigation,contingency,owner,status) VALUES(?,?,?,?,?,?,?,?,?)", sample_risks)
        if con.execute("SELECT COUNT(*) FROM spm_team_members").fetchone()[0] == 0:
            con.executemany("INSERT INTO spm_team_members(name,role,capacity_days,hourly_rate,skills) VALUES(?,?,?,?,?)", sample_team)
        if con.execute("SELECT COUNT(*) FROM spm_changes").fetchone()[0] == 0:
            con.executemany("INSERT INTO spm_changes(change_type,branch_name,summary,author,status) VALUES(?,?,?,?,?)", sample_changes)
        con.commit()
