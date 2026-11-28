# Status report: kritva-sdk

`status.json` is this repository's task-level report for the program (schema 2.0, `status.schema.json`). It reports facts only; acceptance and credit live in KritvaOS/kritva-program.

`tasks` lists KOS-SDK-001, KOS-SDK-002 and KOS-SDK-003 (kritva-program baseline v16, D-155) and KOS-SDK-005 (baseline v17, D-161), the SDK tasks in the approved program baseline. Each is reported COMPLETE with the CI runs on its closing commit (pull request 14 for SDK-001 to 003, pull request 20 for SDK-005, main 3505859). COMPLETE is this repository's execution report only: acceptance and credit need the owner's approval record in kritva-program, and the manual acceptance criteria are listed by `make acceptance`, never reported as passed by a script. KOS-SDK-004 and KOS-SDK-006 to KOS-SDK-009 are approved plans (D-153), NOT_STARTED, not baselined, and are not reported here.

The program treats a report older than 14 days as stale. Update `updated_at` and `source.commit` when this file changes.

`program_snapshot.json` and `STATUS.md` are a derived snapshot of the program status, written by kritva-program (`tools/publish_repo_progress.py`, decision D-120) and checked here by `scripts/progress_report.py --check`. Do not edit them by hand.

`status.schema.json` is copied from kritva-skill; `status.schema.json.sha256` pins it.
