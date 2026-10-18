# Git / SCM workflow for the SPM mini-project

Repository currently used for collaboration:

`https://github.com/sahilmahajan07/Project-Cost-Estimation-Tool`

Assignment branch used for SCM documentation:

`assignment-7-scm`

## Recommended workflow

```bash
git status
git switch -c feature/<short-task-name>
# make and test the change
git add <changed-files>
git commit -m "feat: describe the change"
git push -u origin feature/<short-task-name>
```

Open a pull request to review a change before merging it into `main`. Run tests before merging:

```bash
python -m unittest discover -s tests -v
```

Never commit passwords, tokens, `.env` files or the local `database/pcet.db`. The local database is ignored by `.gitignore`; the SQL schema is source-controlled.

## SCM evidence

- `.git/` in a developer clone stores real Git history; the source distribution ZIP intentionally excludes `.git` so it can be extracted separately without carrying stale remotes.
- `SCM_README.md` from the Assignment 7 workflow documents the main SCM components.
- The SPM workspace's SCM activity log is a manual traceability record and should be checked against actual commits/branches.
