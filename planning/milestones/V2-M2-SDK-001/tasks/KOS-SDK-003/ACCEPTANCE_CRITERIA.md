# Acceptance Criteria — KOS-SDK-003

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | Client configuration is explicit, validated and documented. | unit tests |
| AC-002 | Client lifecycle supports deterministic close/cleanup. | lifecycle tests |
| AC-003 | Errors preserve upstream codes and do not expose secrets. | error/security tests |
| AC-004 | Compatibility declarations identify supported contract versions. | compatibility tests |
| AC-005 | Unsupported versions fail clearly before operation. | negative tests |
| AC-006 | Async timeout and cancellation semantics are tested. | async tests |
| AC-007 | Base import is independent of optional integrations. | clean import |
