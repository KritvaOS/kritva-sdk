# Acceptance Criteria — KOS-SDK-004

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | Adapter consumes a versioned approved Control Plane API. | contract review |
| AC-002 | Credentials are injected securely and never logged. | security tests |
| AC-003 | Client checks do not claim to replace server authorization. | security review |
| AC-004 | Timeout, cancellation, retry and idempotency follow contract. | integration tests |
| AC-005 | Errors preserve service identity without sensitive leakage. | error tests |
| AC-006 | Evidence distinguishes mock from real endpoint. | test report |
