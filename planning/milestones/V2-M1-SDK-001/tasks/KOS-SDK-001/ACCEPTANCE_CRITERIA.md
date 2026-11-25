# Acceptance Criteria — KOS-SDK-001

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | SDK purpose, ownership and exclusions are documented. | architecture review |
| AC-002 | Python-first strategy and deferred languages are explicit. | owner review |
| AC-003 | Candidate public API is documented and marked proposed. | API review |
| AC-004 | Lifecycle, sync/async, timeout and cancellation are specified or recorded as open decisions. | design review |
| AC-005 | Core, Sense, Motion, Mind, Skill, Sim, ROS 2, Studio and Control Plane boundaries are mapped. | boundary review |
| AC-006 | Approved contract versions are identified; unknown/draft versions remain unpinned. | dependency review |
| AC-007 | No runtime, hardware or release readiness is claimed. | documentation review |
| AC-008 | Owner dispositions and immutable review evidence are recorded. | PR record |
| AC-009 | The first-release scope is contract-first and every dependency is traceable to a pinned APPROVED contract (Sense 0.1.0, commit 543f574); Mind, Motion, Skill, Sim and Control Plane are recorded as excluded. | dependency review |
| AC-010 | Explicit exclusions are documented: no Core client, no network or HTTP implementation, no ROS 2 or simulator adapter in the first release. | API review |
| AC-011 | Scope or acceptance changes to KOS-SDK-001..009 are mirrored by a reviewed kritva-program change. | program PR record |
| AC-012 | The project owner approves the public API and architecture. | owner approval |
