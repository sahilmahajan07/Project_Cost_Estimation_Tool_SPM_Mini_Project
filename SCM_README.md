# Software Configuration Management (SCM)

## Purpose
SCM is used to identify, version, review and track changes to source code, database scripts, requirements, plans, test cases and project documentation.

## Key SCM components used in this project

1. **Configuration identification:** tracked items include `app.py`, `backend/`, `frontend/`, `database/schema.sql`, tests and documentation.
2. **Version control:** Git stores snapshots in commits; GitHub hosts the shared repository.
3. **Change control:** use a feature branch and review a pull request before merging changes into `main`.
4. **Status accounting:** commit messages and history record the reason, author and time of changes.
5. **Configuration auditing:** run the automated test suite and review the schema/UI/API changes before accepting a change.
6. **Build and release management:** run the local app and tests, then label or document a stable demonstration version.

## Typical commands

```bash
git status
git switch -c feature/risk-register-update
git add frontend/spm.js backend/models/spm_model.py
git commit -m "feat: improve SPM risk register"
git push -u origin feature/risk-register-update
python -m unittest discover -s tests -v
```

Create a pull request on GitHub for review. Do not commit `.env`, passwords, tokens or `database/pcet.db`. The `.gitignore` excludes local database and Python cache files.

## Team task management

The SPM workspace includes a Kanban task board with **To Do**, **In Progress**, **Testing / Review**, and **Done** statuses. The same task records appear in the project plan, including owner, start week, duration, effort and dependencies. Use the task status field to keep the board aligned with actual progress.

The in-app SCM log is a manual traceability aid; use Git's commit history as the source of truth for actual source changes.
