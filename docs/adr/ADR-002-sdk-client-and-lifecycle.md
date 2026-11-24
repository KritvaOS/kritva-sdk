# ADR-002 — Client Model and Lifecycle

Status: PROPOSED. To be finalized in KOS-SDK-001.

## Proposal
- Async-first public API, with synchronous convenience wrappers over it.
- A client is created from explicit configuration, used as an async context manager, and closed deterministically.
- Timeout, cancellation and cleanup behavior is documented per call; errors are typed and deterministic.
- Authentication is injected through a boundary the SDK does not own. Client-side validation never replaces server authorization or safety checks.

## Open questions
- Retry and idempotency policy per operation class.
- Configuration sources and precedence.
- Thread and event-loop rules for the synchronous wrappers.
