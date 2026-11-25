# ADR-002 — Library Lifecycle, Configuration and Errors

Status: PROPOSED. Revised 2026-11-24 for the contract-first first release.

## Proposal
- The first release is a pure library: no connections, sessions or background tasks, so no client lifecycle exists yet.
- Configuration is explicit, validated and immutable. There is no implicit global state and no environment-variable magic in the base import.
- Errors are typed and deterministic and preserve upstream error codes (for example `UNSUPPORTED_CONTRACT_VERSION`). Error text never includes secrets.
- Validation is synchronous and pure. Timeout and cancellation semantics are specified when a network surface is approved.

## Deferred
When a client is introduced: async-first with synchronous convenience wrappers, async context manager with deterministic close, authentication injected through a boundary the SDK does not own, retry and idempotency per operation class.
