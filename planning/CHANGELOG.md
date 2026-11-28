# Planning Changelog

## 2026-11-28 (KOS-SDK-005 status report)
- kritva-program baselined KOS-SDK-005 in baseline v17 (D-161, weight 5, V2-M3-SDK-001). `status/status.json` now reports it COMPLETE with the seven CI runs on main commit 3505859 (pull request 20, the last of pull requests 17 to 20). This is an execution report only: the 18 manual acceptance criteria need the owner's recorded review, and acceptance and credit need the owner's approval record in kritva-program.

## 2026-11-28 (KOS-SDK-005 PR4, conformance and acceptance)
- Extended the regression gate: REG-03 covers the stream and frame graph constants, REG-04 their fixture results (including resolved transforms), REG-05 the early unsupported-version cases. The golden data change is additive only.
- Extended the integration gate: INT-01..05 and INT-07 cover the stream and frame graph modules (wire round trip, documented rejection codes, no secrets in errors, tamper checks for every vendored kind, schema subset checks); `--full` runs 7 scenarios.
- Added acceptance criteria AC-007 to AC-014 for KOS-SDK-005 with 14 acceptance-map entries (AC-003, AC-006 and AC-014 are manual) and added KOS-SDK-005 to the acceptance gate. Added a test that keeps the API.md support matrix equal to `supported_contracts()`.
- KOS-SDK-005 remains outside the frozen baseline: no credit and no acceptance are claimed.

## 2026-11-28 (KOS-SDK-005 PR3, frame-graph adapter)
- Added `kritva_sdk.frame_graph`: typed transform and graph models, `validate_transform`, `validate_graph` with the upstream `FG_` codes, deterministic `resolve` returning a `Resolution` (a canonical transform or the violations, never both), `transform_point`, `parse_frame_graph`. `frame_graph` 0.1.0 is now declared in `supported_contracts()`.
- Vendored the 42 upstream frame graph fixtures under `tests/data/frame_graph` with provenance; the drift check covers them. Added unit tests and oracle parity tests (diagnostics, every frame pair, generated graphs, 3,000 seeded mutations, exact numerical parity). Regenerated the REG-01 and REG-02 golden data on purpose.

## 2026-11-28 (KOS-SDK-005 PR2, stream adapter)
- Added `kritva_sdk.stream`: typed stream 0.1.0 models, an incremental `StreamChecker` (same result for every batch split), `check_stream`, `parse_stream`, upstream `STREAM_` codes preserved verbatim and sample violations kept apart with their Sense 0.1.0 codes. `stream` 0.1.0 is now declared in `supported_contracts()`.
- Vendored the 58 upstream stream fixtures and `expected.json` under `tests/data/stream` with provenance; the drift check covers them. Added unit tests and oracle parity tests (fixtures, harness cases, every split of short streams, 3,000 seeded mutations). Regenerated the REG-01 and REG-02 golden data on purpose.
- Frame-graph support is declared in PR3.

## 2026-11-27 (KOS-SDK-005 start)
- Owner authorized starting KOS-SDK-005. Plan aligned with the advisory review: four PRs (vendoring, stream adapter, frame-graph adapter, conformance and acceptance).
- PR1 vendors the stream 0.1.0 and frame graph 0.1.0 contracts and schemas byte-exact from kritva-sense tag v0.2.0 (commit 543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77) with provenance (D-088, D-085). Support is declared in `supported_contracts()` only when each adapter lands, so no version is declared before it is implemented.
- Corrected the `TASKS.md` header: KOS-SDK-001 to 003 are in baseline v16; KOS-SDK-005 is not in the frozen baseline and earns no credit.

## 2026-11-27 (status report)
- kritva-program baselined KOS-SDK-001 to 003 in baseline v16 (D-155; KOS-SDK-002 is one task at weight 8). `status/status.json` now reports them COMPLETE with the CI runs on main commit 645f984. Program acceptance and credit still need the owner's approval record; KOS-SDK-004 to 009 stay approved plans and are not reported.

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
- 2026-11-26: task dispositions recorded: SDK-001 to 003 complete, acceptance pending; SDK-004 to 009 approved plan, not started (D-153).
