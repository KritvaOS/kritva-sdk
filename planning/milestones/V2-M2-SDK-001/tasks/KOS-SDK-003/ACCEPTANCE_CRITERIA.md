# Acceptance Criteria — KOS-SDK-003

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | Configuration is explicit, immutable, validated and documented. | unit tests |
| AC-002 | Errors preserve upstream codes and do not expose secrets. | error/security tests |
| AC-003 | Compatibility declarations identify supported contract versions; unsupported versions fail clearly before any operation. | compatibility and negative tests |
| AC-004 | Vendored schemas carry provenance (repo, path, version, tag, commit SHA, checksum, approval status) and a CI drift check detects divergence from the pinned upstream. | drift check |
| AC-005 | Sense models round-trip and validate identically to the normative JSON Schema, including units, timestamps, frames, `validity` and `error_code` rules, and unknown-field rejection. | conformance tests |
| AC-006 | Base import is independent of ROS 2, simulator, hardware and network libraries. | clean import |
| AC-007 | No Core client, transport or unapproved contract is included. | design review |
| AC-008 | Cross-validation tests run the pinned kritva-sense validator, generator and conformance harness as oracles and show the SDK does not diverge semantically; the SDK has no runtime dependency on kritva-sense. | cross-validation tests |
