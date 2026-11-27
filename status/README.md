# Status report: kritva-sdk

`status.json` is this repository's task-level report for the program (schema 2.0, `status.schema.json`). It reports facts only; acceptance and credit live in KritvaOS/kritva-program.

`tasks` lists KOS-SDK-001, KOS-SDK-002 and KOS-SDK-003, the SDK tasks in the approved program baseline (kritva-program baseline v16, D-155). Each is reported COMPLETE with the CI runs on the closing commit (the merge of pull request 14, which implemented the required local gates). COMPLETE is this repository's execution report only: acceptance and credit need the owner's approval record in kritva-program, and the 15 manual acceptance criteria are listed by `make acceptance`, never reported as passed by a script. KOS-SDK-004 to KOS-SDK-009 are approved plans (D-153), NOT_STARTED, not baselined, and are not reported here.

The program treats a report older than 14 days as stale. Update `updated_at` and `source.commit` when this file changes.

`program_snapshot.json` and `STATUS.md` are a derived snapshot of the program status, written by kritva-program (`tools/publish_repo_progress.py`, decision D-120) and checked here by `scripts/progress_report.py --check`. Do not edit them by hand.

`status.schema.json` is copied from kritva-skill; `status.schema.json.sha256` pins it.
