# Kritva SDK Planning

Local planning and execution control for Kritva SDK.

- `MILESTONE.md`: local mapping to Kritva V2 phases.
- `TASKS.md`: stable local task register.
- `MILESTONE_STATUS.md`: local planning snapshot, not central acceptance.
- `MASTER_TRACKER.md`: consolidated task map.
- `milestones/<ID>/MILESTONE.md`: milestone scope and exit criteria.
- Each task directory contains `TASK.md` and `ACCEPTANCE_CRITERIA.md`.

Execution: Milestone → Task → Acceptance Criteria → contract/API review → implementation → tests → immutable evidence → PR → review → task acceptance → completion record.

kritva-program registers this repository as the `SDK` workstream (D-149) and carries SDK planning rows and weights in its approved plan register (D-153), with six V2 repository milestones proposed. KOS-SDK-001 to 003 are complete here and the owner decided to accept them (2026-11-26, interim D-047, not independent), but no SDK task is in the approved baseline yet and weights in the plan register are planning anchors that earn no credit; KOS-SDK-004 to 009 are approved plan scope, not started. Do not edit central baseline, approvals, gates, workstreams or generated views here.
