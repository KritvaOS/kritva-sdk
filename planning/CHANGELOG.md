# Planning Changelog

## 2026-11-24
- Initial proposed V2 milestone mapping and eight-task SDK register.
- Central SDK repository/workstream registration remains pending.

## 2026-11-24 (review update)
- Owner decisions recorded: CODEOWNER `@dineshannayya`; repository visibility PUBLIC.
- Added ADR-001..003 and the contract dependency register.
- Narrowed KOS-SDK-005 to the Sense adapter; added KOS-SDK-009 for Motion, Mind and Skill (blocked on contract approval).
- Marked local M1 as a planning label with no program credit pending the SDK ownership decision.
- Ported hooks, CI workflows, gate config and preflight from kritva-skill; rewrote README to pass the README standard.

## 2026-11-24 (contract register verification)
- Verified the contract dependency register against upstream contents; recorded exact commits and statuses.
- Recorded that Core R1.0 has no Python or network surface, and that Mind's contract status is inconsistent upstream.

## 2026-11-24 (SDK-001 design alignment)
- First release re-scoped to a contract-first library (Sense 0.1.0); no Core client or network transport until an approved API exists.
- Distribution `kritva-sdk`, import `kritva_sdk`; vendored pinned schemas with drift check; hand-written typed models.
- Rewrote API.md and ARCHITECTURE.md; revised ADR-001..003, KOS-SDK-001 criteria and KOS-SDK-003 scope.
- Central change required: KOS-SDK-003 title and the TASKS.md pin in kritva-program planning_inventory.json.

## 2026-11-25 (open-item alignment)
- Python support changed to 3.12+; zero runtime dependencies; kritva-sense validator is a test/CI oracle only.
- Sense stream and frame-graph contracts recorded as APPROVED and eligible (staged under KOS-SDK-005); Mind recorded as DRAFT.
- KOS-SDK-002 narrowed to package foundation; schema vendoring, drift check and Sense validation stay in KOS-SDK-003.
- PyPI availability check recorded as an open check; PD-021 and the SDK-002 start remain owner decisions.

## 2026-11-25 (SDK-002 start)
- Owner approved the KOS-SDK-002 start (package foundation only; scope per the task file).
- Layout is root-level `src/kritva_sdk/`, matching kritva-sense; docs updated from `sdk/python/`.
- Implemented: `pyproject.toml` (setuptools==80.9.0), `kritva_sdk` with `__version__ = 0.1.0.dev0`, `py.typed`, hash-pinned build requirements, sdist normaliser, unit and packaging tests.
- Task status in `planning/TASKS.md` is unchanged here to avoid a kritva-program re-pin before merge; status moves with the program record.

## 2026-11-26 (status reporting)
- Added `status/` (status.json schema 2.0 with no baselined tasks, schema and checksum, README), the generated progress view from kritva-program's published snapshot, `scripts/progress_report.py`, the `progress-check` workflow and `make progress-check` (in preflight).
- README now links the status report and states that implementation maturity (SDK-002 merged) is separate from program acceptance; stale "pending central registration" text corrected (D-149, D-153).

## 2026-11-26 (PyPI name check)
- Recorded the owner's PyPI check of 2026-11-25: `kritva-sdk` is not currently listed (404 on the Simple and JSON endpoints). It is not reserved and is re-checked before the first release (ADR-001, API.md, ARCHITECTURE.md).
