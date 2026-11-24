# Kritva SDK Testing Strategy

**Status:** PROPOSED. Gates are not implemented unless explicitly reported otherwise.

| Level | Purpose |
|---|---|
| Unit | Config, models, errors and client lifecycle |
| Contract | Upstream schemas, versions and error mapping |
| Integration | Actual service boundaries and transport behavior |
| Regression | Preserve accepted API and behavior guarantees |
| Example smoke | Run examples against mocks or simulation |
| Security | Dependency, secret and logging boundaries |

Base unit/contract suites run without hardware, ROS 2, live Control Plane or simulator. Integration reports identify mocks versus real endpoints. Simulation evidence is labelled simulation.

Kritva V2 requires `make check`, `make lint`, `make test-unit`, `make test-integration`, `make test-regression`, `make test`, `make docs-check` and `make acceptance`. Until implemented, a gate must report NOT_IMPLEMENTED and exit non-zero; it must never silently pass.

Evidence records exact commit SHA, CI run ID, command, result, environment and skipped dependencies.
