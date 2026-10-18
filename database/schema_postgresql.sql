-- PostgreSQL reference schema for deployments that use the database option named in the SRS.
-- The local demonstration currently runs database/schema.sql with SQLite for zero-install setup.
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL CHECK (role IN ('Admin','Project Manager','Team Lead','Finance')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS projects (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    project_type VARCHAR(80) NOT NULL DEFAULT 'Web Application',
    duration_months NUMERIC(7,2) NOT NULL CHECK (duration_months > 0),
    hours_per_day NUMERIC(4,2) NOT NULL CHECK (hours_per_day > 0 AND hours_per_day <= 24),
    working_days_per_week NUMERIC(3,1) NOT NULL CHECK (working_days_per_week > 0 AND working_days_per_week <= 7),
    contingency_percent NUMERIC(5,2) NOT NULL CHECK (contingency_percent BETWEEN 0 AND 100),
    actual_cost NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (actual_cost >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS team_members (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role_name VARCHAR(80) NOT NULL,
    member_count INTEGER NOT NULL CHECK (member_count >= 0),
    hourly_rate NUMERIC(12,2) NOT NULL CHECK (hourly_rate >= 0)
);
CREATE TABLE IF NOT EXISTS cost_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category VARCHAR(20) NOT NULL CHECK (category IN ('resource','testing','overhead')),
    item_name VARCHAR(100) NOT NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0)
);
CREATE TABLE IF NOT EXISTS estimates (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    personnel_cost NUMERIC(14,2) NOT NULL,
    resource_cost NUMERIC(14,2) NOT NULL,
    testing_cost NUMERIC(14,2) NOT NULL,
    overhead_cost NUMERIC(14,2) NOT NULL,
    direct_cost NUMERIC(14,2) NOT NULL,
    contingency_percent NUMERIC(5,2) NOT NULL,
    contingency_amount NUMERIC(14,2) NOT NULL,
    total_cost NUMERIC(14,2) NOT NULL,
    variance NUMERIC(14,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_estimates_project_created ON estimates(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_items_project ON cost_items(project_id);

-- SPM workspace tables: requirements, WBS/Kanban tasks, risks, team and SCM log.
CREATE TABLE IF NOT EXISTS spm_requirements (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    req_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(180) NOT NULL,
    kind VARCHAR(30) NOT NULL CHECK (kind IN ('Functional','Non-functional')),
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('High','Medium','Low')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Planned','In Progress','Implemented','Tested')),
    description TEXT NOT NULL DEFAULT '',
    acceptance_criteria TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS spm_tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(180) NOT NULL,
    phase VARCHAR(100) NOT NULL DEFAULT 'Development',
    assignee VARCHAR(120) NOT NULL DEFAULT 'Unassigned',
    start_week INTEGER NOT NULL DEFAULT 1 CHECK (start_week BETWEEN 1 AND 16),
    duration_days NUMERIC(7,2) NOT NULL DEFAULT 1 CHECK (duration_days > 0),
    effort_days NUMERIC(7,2) NOT NULL DEFAULT 1 CHECK (effort_days >= 0),
    status VARCHAR(30) NOT NULL CHECK (status IN ('To Do','In Progress','Testing / Review','Done')),
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('High','Medium','Low')),
    dependencies TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS spm_risks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    risk_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(180) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'Technical',
    likelihood SMALLINT NOT NULL CHECK (likelihood BETWEEN 1 AND 3),
    impact SMALLINT NOT NULL CHECK (impact BETWEEN 1 AND 3),
    mitigation TEXT NOT NULL DEFAULT '',
    contingency TEXT NOT NULL DEFAULT '',
    owner VARCHAR(120) NOT NULL DEFAULT 'Project Manager',
    status VARCHAR(20) NOT NULL CHECK (status IN ('Identified','Monitoring','Mitigating','Closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS spm_team_members (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    role VARCHAR(100) NOT NULL,
    capacity_days NUMERIC(7,2) NOT NULL CHECK (capacity_days > 0),
    hourly_rate NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (hourly_rate >= 0),
    skills TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS spm_changes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('Commit','Branch','Requirement','Release','Review')),
    branch_name VARCHAR(200) NOT NULL DEFAULT 'main',
    summary TEXT NOT NULL,
    author VARCHAR(120) NOT NULL DEFAULT 'Project Team',
    status VARCHAR(20) NOT NULL CHECK (status IN ('Planned','In Review','Accepted','Completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_spm_tasks_status ON spm_tasks(status);
CREATE INDEX IF NOT EXISTS idx_spm_risks_status ON spm_risks(status);
CREATE INDEX IF NOT EXISTS idx_spm_requirements_status ON spm_requirements(status);
