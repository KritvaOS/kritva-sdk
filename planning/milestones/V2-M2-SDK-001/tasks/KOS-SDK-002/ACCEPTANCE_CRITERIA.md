# Acceptance Criteria — KOS-SDK-002

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | Package installs in a clean supported Python environment. | clean install |
| AC-002 | Metadata declares name, version, license, Python range and dependencies. | metadata inspection |
| AC-003 | Base install does not require ROS 2, simulator or hardware libraries. | dependency/import test |
| AC-004 | Optional integrations are extras and do not leak into base imports. | extras tests |
| AC-005 | Two clean builds are equivalent under declared reproducibility policy. | build test |
| AC-006 | Artifact hashes and provenance are recorded. | build report |
| AC-007 | Package version follows approved SemVer policy. | version review |
