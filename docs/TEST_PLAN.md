# Test Plan — Project Cost Estimation Tool / SPM Mini-Project

## Objective
Verify the core cost-estimation formula, validation behavior, and CRUD workflows for requirements, planning tasks, risks, team roles, and SCM records.

## Manual test cases

| ID | Test condition | Input / action | Expected result |
|---|---|---|---|
| TC-01 | Load main application | Open `http://127.0.0.1:8000` | Cost estimator loads; projects are listed from SQLite |
| TC-02 | Load SPM workspace | Open `/frontend/spm.html` | Counts and tables load from `/api/spm/data` |
| TC-03 | Calculate estimate | Enter duration, team rates, costs and 10% contingency; save | Server returns estimate; total is direct costs + contingency |
| TC-04 | Reject invalid estimate | Set duration to 0 or contingency above 100% | Validation message is displayed; invalid data is not saved |
| TC-05 | Add requirement | Enter a unique ID, title, priority and acceptance criteria | Requirement appears in the register and persists after reload |
| TC-06 | Update requirement status | Change Planned to Tested and select Save | New status is stored and displayed after refresh |
| TC-07 | Update Kanban task | Change a task status and click Update status | Task moves to the selected column and database value updates |
| TC-08 | Risk evaluation | Create risk with likelihood 3 and impact 3 | Risk score is 9 and severity is High |
| TC-09 | Workload distribution | Assign planned effort to a role | Allocated days and utilization percentage are recalculated |
| TC-10 | Add SCM log item | Add a branch or commit log entry | Entry appears in SCM activity with branch/reference and status |
| TC-11 | Export estimates | Click Export CSV in main page | CSV file is downloaded with estimate summary columns |
| TC-12 | Run unit tests | `python -m unittest discover -s tests -v` | All tests pass |

## Automated tests

`tests/test_calculator.py` covers expected formula outputs, actual-versus-estimate variance, and validation of duration and contingency. `tests/test_spm_validation.py` tests requirements, task schedule/effort values, risk bounds, and staff capacity validation.

## Results from build verification

- Automated unit and validation tests: **10 passed**.
- Local API smoke check: main page, SPM page, health endpoint, SPM summary, and create/update/delete operations for requirement records returned expected HTTP responses; task creation/status update also succeeded.
- The application uses a local SQLite file for demonstration. Database backups, authentication, production security, PDF/XLSX generation and load testing are not included in this build and should be listed as future work.
