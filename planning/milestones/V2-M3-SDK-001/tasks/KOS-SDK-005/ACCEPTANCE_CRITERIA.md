# Acceptance Criteria — KOS-SDK-005

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | Each adapter names owning repo and exact contract version/commit. | dependency inventory |
| AC-002 | Models preserve upstream units, timestamps, frames, lifecycle and errors. | contract tests |
| AC-003 | No API is invented where upstream contract is absent/unapproved. | design review |
| AC-004 | Adapters do not depend on other capability implementation internals. | dependency check |
| AC-005 | Tests cover valid, invalid, missing and unsupported-version cases. | contract tests |
| AC-006 | Support matrix identifies implemented/deferred/unsupported contracts. | docs review |
