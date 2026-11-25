# ADR-003 — Transport: Deferred Until an Approved API Exists

Status: PROPOSED. Revised 2026-11-24 (replaces "HTTP transport first").

## Decision
No transport abstraction or HTTP implementation is built in the first release. Core R1.0 is an in-process C++ API with no network surface, and the Control Plane and Sim are NOT_AVAILABLE, so a transport would have no consumer and any wire format would be invented.

## Revisit when
An approved Control Plane API or a Community runtime interface exists with a versioned contract. Then SDK-004 defines the transport boundary, HTTP library choice (license, security and maintenance review) and wire format from that contract.

## Constraints that remain
- Adapters stay isolated behind extras; ROS 2, simulator and hardware are never required by the base import.
- Dependency direction is preserved: Mind and Motion -> Skill. The SDK exposes contracts without reversing ownership.
- No SDK-only substitute is invented for a missing upstream contract.
