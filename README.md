# Project Cost Estimation Tool — SPM Mini-Project

A local, database-backed academic mini-project combining a practical software cost estimator with a Software Project Management (SPM) control workspace. It consolidates the themes from Assignments 1–8: project context and feasibility, SRS requirements, 16-week planning, cost estimation, risk management, implementation, software configuration management (SCM), and team/staff coordination.

## What the application does

### Cost estimation (main page)
- Create, edit, search, and delete project estimates.
- Enter project duration, working calendar, team roles/counts/hourly rates, resource expenses, QA/testing expenses, overhead, contingency, and actual spending.
- Calculate personnel cost, direct cost, contingency, total estimate, and estimated-versus-actual variance.
- View portfolio summary and estimate history; export saved estimates to CSV.

### SPM Control Center (`/frontend/spm.html`)
- **Requirements register:** tracks functional and non-functional requirements, IDs, priorities, status, descriptions, and acceptance criteria.
- **Project planning:** task/WBS records include phase, start week, duration, person-day effort, owner, dependencies, status, and priority. Uses a 16-week academic planning window and the 58-person-day baseline from earlier assignments.
- **Kanban board:** To Do, In Progress, Testing / Review, and Done columns; task status can be updated on the board and is saved in SQLite.
- **Risk register:** captures risk category, likelihood (1–3), impact (1–3), score, severity, mitigation, contingency plan, owner, and current response status.
- **Team and workload:** captures role, capacity in person-days, planning hourly rate, skills/responsibilities, task allocation and utilization. Utilization above 100% is flagged as overload.
- **SCM change log:** records branch, commit, review, requirement and release references. This log complements, but does not replace, the actual Git history.

## Technology
- Frontend: HTML5, CSS3, vanilla JavaScript
- Backend: Python 3 standard-library HTTP server; controller/model/service organization
- Database: SQLite for local setup; a PostgreSQL schema reference is provided
- Testing: Python `unittest`
- Configuration management: Git and GitHub

No third-party Python packages are required. Python 3.10+ is recommended.

## Run on Windows
1. Extract `Project_Cost_Estimation_Tool_SPM_Mini_Project.zip`.
2. Open the extracted `pcet_project` folder.
3. Double-click `run_project.bat` (or open Command Prompt in this folder and run `python app.py`). The batch file launches the same command without requiring external packages.
4. Open the cost estimator at <http://127.0.0.1:8000>.
5. Open the SPM workspace at <http://127.0.0.1:8000/frontend/spm.html>.
6. Stop the server with `Ctrl+C` in the terminal.

Manual start command:

```bat
python app.py
```

On first startup, SQLite creates `database/pcet.db` and inserts illustrative sample project/SPM records. Existing data is preserved; samples are inserted only where the relevant table is empty. Back up the local database before testing destructive actions.

## Run automated tests

```bat
python -m unittest discover -s tests -v
```

Alternatively, double-click `run_tests.bat`.

The tests verify core cost formulae and validation rules for requirements, planning tasks, and risks.

## API overview

- `GET /api/health` — local service health
- `/api/projects` — project estimate list/create and related project endpoints
- `GET /api/spm/data` — SPM workspace data and summary metrics
- `/api/spm/requirements` — list/create/update/delete requirements
- `/api/spm/tasks` — list/create/update/delete planning and Kanban tasks
- `/api/spm/risks` — list/create/update/delete risks
- `/api/spm/team` — list/create/update/delete staff roles and capacity
- `/api/spm/changes` — list/create/update/delete SCM log entries

## Cost model

- Personnel cost = sum of people × hourly rate × hours/day × working days/week × 4.33 weeks/month × duration in months.
- Direct cost = personnel + resources + testing/QA + overhead.
- Contingency = direct cost × contingency percentage / 100.
- Estimated total = direct cost + contingency.
- Variance = actual spending − estimated total (positive means actual spending is above estimate).

The 4.33-weeks-per-month convention is a prototype assumption and should be confirmed before real financial use.

## Sample planning baseline

The seeded WBS/task effort values total **58 person-days**. Staffing capacity totals 64 person-days in the illustrative role plan. The people listed are role placeholders for an academic allocation model; they are not claims about named, separately employed staff. Task owners, statuses, risks and requirements can be modified in the UI to reflect actual team progress.

## Current scope and limitations

This is an academic local prototype, not a production financial system. Core estimation, CRUD/history, CSV export, requirements/task/risk/team management, workload summary, and SCM log are implemented. Login/password hashing and server-side role authorization, PDF/Excel report generation, email notifications, automated backup scheduling, HTTPS deployment, and 200-user load testing remain future work. The health and database-summary APIs are for local demonstration only. Do not expose the application publicly or store confidential client data without implementing security controls.
