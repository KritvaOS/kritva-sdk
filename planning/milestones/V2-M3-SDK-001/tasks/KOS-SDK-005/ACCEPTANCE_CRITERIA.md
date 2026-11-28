# Acceptance Criteria — KOS-SDK-005

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | The Sense adapter names owning repo and exact contract version/commit. | dependency inventory |
| AC-002 | Models preserve upstream units, timestamps, frames, lifecycle and errors. | contract tests |
| AC-003 | No API is invented where upstream contract is absent/unapproved. | design review |
| AC-004 | Adapters do not depend on other capability implementation internals. | dependency check |
| AC-005 | Tests cover valid, invalid, missing and unsupported-version cases. | contract tests |
| AC-006 | Support matrix identifies implemented/deferred/unsupported contracts. | docs review |
| AC-007 | The vendored stream and frame-graph contract files and their test fixtures are byte-exact copies of the pinned upstream files (tag `v0.2.0`, commit SHA) with provenance, and a drift check detects divergence. | drift check |
| AC-008 | The stream checker gives identical (position, code, path, message) results to the pinned kritva-sense reference checker on the upstream fixtures, the harness stream cases and seeded mutations. | cross-validation tests |
| AC-009 | The frame-graph validation and resolution give identical diagnostics and numerically identical transforms and points to the pinned reference implementation on the upstream fixtures, every frame pair, generated graphs and seeded mutations. | cross-validation tests |
| AC-010 | The stream checker gives the same result for every split of the same ordered records into batches, including empty batches. | unit and cross-validation tests |
| AC-011 | A non-conformant graph never resolves, and an unknown frame or an unconnected pair never yields an invented or identity transform. | unit tests |
| AC-012 | Upstream codes are preserved verbatim, the STREAM_, FG_ and Sense code namespaces stay separate, and SDK misuse raises typed SDK errors that are not contract diagnostics. | unit tests |
| AC-013 | An unsupported stream or frame-graph version is rejected with the upstream code and never accepted silently; `supported_contracts()` declares exactly the implemented contracts. | compatibility and negative tests |
| AC-014 | No result is described as sensor freshness, calibration, physical, time-synchronisation or safety validation; the transform convention and the support matrix are documented. | docs review |
