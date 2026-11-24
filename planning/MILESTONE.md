# Kritva SDK Milestone Plan

**Status:** PROPOSED / PLANNING_ONLY. Local mapping only; not centrally registered.

| Program milestone | Local SDK milestone | Outcome |
|---|---|---|
| V2-M0 | Governance baseline | Adopt repository governance and acceptance structure; not a claim of central M0 closure |
| V2-M1 | V2-M1-SDK-001 | Local planning label only: Python-first architecture and developer API reviewed. No M1 progress is claimed until the program decides SDK ownership (a V2-M2 exit condition) |
| V2-M2 | V2-M2-SDK-001 | Python package, reproducible build, core client and compatibility |
| V2-M3 | V2-M3-SDK-001 | Control Plane and capability API adapters |
| V2-M5 | V2-M5-SDK-001 | Simulation adapter and reproducible examples |
| V2-M7 | V2-M7-SDK-001 | Telemetry, events and execution results |
| V2-M8 | V2-M8-SDK-001 | Security, compatibility and release readiness |

V2-M4 has no direct SDK deliverable. V2-M6 remains HOLD; no physical SDK integration is planned. M7 software evidence cannot imply physical readiness.

> Governance note: kritva-program's V2-M2 exit includes "Sim and SDK ownership location decided", and the SDK workstream has no repository assigned. Local M1 work is pre-registration planning and earns no program credit.

## V2-M1-SDK-001 — Architecture and API
Task KOS-SDK-001. Exit: Python-first scope, ownership boundaries, candidate public API, lifecycle semantics, contract dependencies and open decisions reviewed. No runtime implementation is implied.

## V2-M2-SDK-001 — Package foundation
Tasks KOS-SDK-002/003. Exit: clean install, reproducible package artifacts, version policy, client/configuration/lifecycle tests and contract compatibility checks.

## V2-M3-SDK-001 — Service and capability integration
Tasks KOS-SDK-004/005/009. Exit: approved Control Plane API/security boundary; exact upstream contract pins; typed adapters; timeout, cancellation, idempotency, retry and error tests.

## V2-M5-SDK-001 — Simulation and examples
Task KOS-SDK-006. Exit: approved simulation interface, replayable examples and smoke tests; all evidence labelled simulation.

## V2-M7-SDK-001 — Telemetry and results
Task KOS-SDK-007. Exit: approved telemetry/event/result contracts, tested lifecycle/stale-data/error paths and reproducible software evidence.

## V2-M8-SDK-001 — Production readiness
Task KOS-SDK-008. Exit: security dispositions, compatibility matrix, release integrity, install/upgrade/recovery procedures, accepted residual risks and completion record.

## Schedule references
Inherit central planning targets only as references: M1 2026-11-30; M2 2027-01-15; M3 2027-03-15; M5 2027-06-15; M7 2027-08-15; M8 2027-09-13. They are not SDK commitments or capacity estimates. M6 remains HOLD without a date.
