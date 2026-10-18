PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('Admin','Project Manager','Team Lead','Finance')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    project_type TEXT NOT NULL DEFAULT 'Web Application',
    duration_months REAL NOT NULL CHECK(duration_months > 0),
    hours_per_day REAL NOT NULL CHECK(hours_per_day > 0 AND hours_per_day <= 24),
    working_days_per_week REAL NOT NULL CHECK(working_days_per_week > 0 AND working_days_per_week <= 7),
    contingency_percent REAL NOT NULL CHECK(contingency_percent >= 0 AND contingency_percent <= 100),
    actual_cost REAL NOT NULL DEFAULT 0 CHECK(actual_cost >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role_name TEXT NOT NULL,
    member_count INTEGER NOT NULL CHECK(member_count >= 0),
    hourly_rate REAL NOT NULL CHECK(hourly_rate >= 0)
);

CREATE TABLE IF NOT EXISTS cost_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK(category IN ('resource','testing','overhead')),
    item_name TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0)
);

CREATE TABLE IF NOT EXISTS estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    personnel_cost REAL NOT NULL,
    resource_cost REAL NOT NULL,
    testing_cost REAL NOT NULL,
    overhead_cost REAL NOT NULL,
    direct_cost REAL NOT NULL,
    contingency_percent REAL NOT NULL,
    contingency_amount REAL NOT NULL,
    total_cost REAL NOT NULL,
    variance REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_estimates_project_created ON estimates(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cost_items_project ON cost_items(project_id);

-- Software Project Management workspace (Assignments 1–8 integration)
CREATE TABLE IF NOT EXISTS spm_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('Functional','Non-functional')),
    priority TEXT NOT NULL CHECK(priority IN ('High','Medium','Low')),
    status TEXT NOT NULL CHECK(status IN ('Planned','In Progress','Implemented','Tested')),
    description TEXT NOT NULL DEFAULT '',
    acceptance_criteria TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spm_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'Development',
    assignee TEXT NOT NULL DEFAULT 'Unassigned',
    start_week INTEGER NOT NULL DEFAULT 1 CHECK(start_week >= 1 AND start_week <= 16),
    duration_days REAL NOT NULL DEFAULT 1 CHECK(duration_days > 0),
    effort_days REAL NOT NULL DEFAULT 1 CHECK(effort_days >= 0),
    status TEXT NOT NULL CHECK(status IN ('To Do','In Progress','Testing / Review','Done')),
    priority TEXT NOT NULL CHECK(priority IN ('High','Medium','Low')),
    dependencies TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spm_risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Technical',
    likelihood INTEGER NOT NULL CHECK(likelihood BETWEEN 1 AND 3),
    impact INTEGER NOT NULL CHECK(impact BETWEEN 1 AND 3),
    mitigation TEXT NOT NULL DEFAULT '',
    contingency TEXT NOT NULL DEFAULT '',
    owner TEXT NOT NULL DEFAULT 'Project Manager',
    status TEXT NOT NULL CHECK(status IN ('Identified','Monitoring','Mitigating','Closed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spm_team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    capacity_days REAL NOT NULL CHECK(capacity_days > 0),
    hourly_rate REAL NOT NULL DEFAULT 0 CHECK(hourly_rate >= 0),
    skills TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spm_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_type TEXT NOT NULL CHECK(change_type IN ('Commit','Branch','Requirement','Release','Review')),
    branch_name TEXT NOT NULL DEFAULT 'main',
    summary TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Project Team',
    status TEXT NOT NULL CHECK(status IN ('Planned','In Review','Accepted','Completed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spm_tasks_status ON spm_tasks(status);
CREATE INDEX IF NOT EXISTS idx_spm_risks_status ON spm_risks(status);
CREATE INDEX IF NOT EXISTS idx_spm_requirements_status ON spm_requirements(status);
