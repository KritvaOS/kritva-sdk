# ADR-003 — Transport Abstraction

Status: PROPOSED. To be finalized in KOS-SDK-001.

## Proposal
- HTTP-based service adapter first, behind a transport interface so other transports can be added without changing the public API.
- Adapters are isolated behind extras; ROS 2, simulator and hardware are never required by the base import.
- Dependency direction is preserved: Mind and Motion → Skill. Skill consumes capability interfaces; Mind must not depend on Skill. The SDK exposes these interfaces without reversing ownership.

## Open questions
- HTTP client library choice, with license, security and maintenance review.
- Wire format and versioning, taken from the approved upstream contracts; none is invented here.
