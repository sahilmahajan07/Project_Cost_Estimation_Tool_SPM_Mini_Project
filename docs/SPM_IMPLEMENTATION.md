# SPM implementation notes — Project Cost Estimation Tool

This file explains how the running mini-project represents the SPM activities planned across Assignments 1–8.

## Mapping of SPM concepts to the application

| SPM concept | Where demonstrated | Implementation evidence |
|---|---|---|
| Problem statement, feasibility and assumptions | `README.md` and project page | Description, constraints, prototype scope and calculation assumptions |
| Software Requirements Specification | SPM Control Center → Requirements | Functional/non-functional register with ID, priority, status, description and acceptance criteria |
| Project planning / WBS | SPM Control Center → Planning & Kanban | Work packages, phase, week, duration, effort, owner and dependencies |
| Cost estimation | Cost Estimator page | Formula-based personnel/direct/contingency/total computation; saved estimate history |
| Risk management | SPM Control Center → Risk register | Likelihood × impact score, severity band, mitigation, contingency action, owner and status |
| Implementation | Cost Estimator and SPM Control Center | HTML/CSS/JS interface, Python HTTP API, SQLite persistence, model/service layers |
| Software Configuration Management | SCM activity panel, `GIT_WORKFLOW.md`, `SCM_README.md` in the developer workflow | Branch/commit log, local Git history, feature branch and documented collaboration process |
| Team/staff coordination | SPM Control Center → Team & workload | Role capacities, assigned effort, utilization percentage and over-capacity warning |
| Kanban coordination | SPM Control Center → Planning & Kanban | Task cards grouped by To Do, In Progress, Testing / Review and Done; status changes persist to database |

## Main calculation algorithm

1. Validate duration, working hours, workdays and contingency percentage.
2. For each team role, calculate count × hourly rate × hours/day × days/week × 4.33 × duration.
3. Sum resource, testing/QA and overhead line items.
4. Add those direct costs to personnel cost.
5. Multiply the direct cost by the contingency percentage and add it to direct cost.
6. Save project inputs and the latest estimate as a history snapshot; calculate variance when actual spend is entered.

## Risk scoring convention

Likelihood and impact are both rated from 1 (low) to 3 (high). Score = likelihood × impact. Scores 1–2 are Low, 3–4 are Medium and 6–9 are High. Each register entry has a mitigation action and a contingency response.

## Resource allocation convention

Capacity and effort are measured in person-days. Allocation for a staff role is calculated by summing the effort of tasks assigned to that role. Utilization = allocated effort / capacity × 100. A value above 100% is displayed as a warning to encourage reassignment or re-planning. Team names are role placeholders for an academic planning model.

## Notes

- Seed records are illustrative. Update the statuses/owners in the app to match the team's actual progress before taking evidence screenshots.
- SCM log entries are a project management log, not automatic parsing of Git commits. Use the real GitHub commit history to confirm version history.
- Authentication/RBAC, PDF/XLSX exports, external notifications, scheduled backups and load testing are explicitly marked as not yet implemented.
