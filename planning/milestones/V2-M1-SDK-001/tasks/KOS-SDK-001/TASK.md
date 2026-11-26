# KOS-SDK-001 — Define Python-First SDK Architecture and Developer API

Status: COMPLETE in this repository; owner decision to accept 2026-11-26 (interim D-047, not independent); program acceptance, baseline and approval record pending; no credit. Milestone: V2-M1-SDK-001.

Objective: define SDK purpose, ownership boundaries, Python-first package strategy, candidate public API, lifecycle and integration boundaries before implementation.

In scope: architecture, API namespace/client proposal, sync/async principles, error/timeout/cancellation/idempotency design, contract dependency map and open decisions.

Out of scope: runtime implementation, Control Plane service, upstream contract changes, mandatory ROS 2 and C++ SDK.

Revised 2026-11-24: first-release scope is a contract-first library (Sense 0.1.0); network clients and transport are deferred (ADR-003).

Deliverables: reviewed ARCHITECTURE.md, REQUIREMENTS.md and API.md; owner decision/open-question register; upstream contract dependency map.

DoD: task criteria reviewed, PR merged, immutable evidence and review record retained.
