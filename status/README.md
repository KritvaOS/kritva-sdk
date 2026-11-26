# Status report: kritva-sdk

`status.json` is this repository's task-level report for the program (schema 2.0, `status.schema.json`). It reports facts only; acceptance and credit live in KritvaOS/kritva-program.

`tasks` is empty on purpose: no SDK task is in the approved program baseline. KOS-SDK-001 to KOS-SDK-009 are planning inventory in `planning/TASKS.md` and are not reported here with execution states (kritva-program D-150, D-153). An empty list means "no baselined task to report", not "no implementation": KOS-SDK-002 (package foundation) is implemented and merged in this repository (pull request 5), and it is planning-only, not baselined and not accepted, so it earns no program credit. When a task is baselined, add it here with its execution state and evidence, and reference the CI run and commit.

The program treats a report older than 14 days as stale. Update `updated_at` and `source.commit` when this file changes.

`program_snapshot.json` and `STATUS.md` are a derived snapshot of the program status, written by kritva-program (`tools/publish_repo_progress.py`, decision D-120) and checked here by `scripts/progress_report.py --check`. Do not edit them by hand.

`status.schema.json` is copied from kritva-skill; `status.schema.json.sha256` pins it.
