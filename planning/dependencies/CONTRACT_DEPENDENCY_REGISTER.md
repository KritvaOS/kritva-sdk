# Contract Dependency Register

Status: PROPOSED / PLANNING_ONLY. Verified against upstream repository contents on 2026-11-24 (read-only clones; heads listed below). A DRAFT, PROPOSED or NOT_AVAILABLE contract is never pinned as APPROVED. Statuses come from each upstream's own files and can change; re-verify before any pin is used.

| Repository | Contract source | Version | Immutable commit SHA | Status | SDK consumer API | Compatibility constraint | Outstanding upstream dependency |
|---|---|---|---|---|---|---|---|
| kritva-core | `API.md`, `ARCHITECTURE.md` | R1.0 | `4acce3b60833abfe33168c4766405ab86ea73edc` (tag `kritva-core-r1.0`) | APPROVED (released); C++ in-process API only, see Finding 1 | none identified | none until a Python or service surface exists | a service or binding surface, if the SDK is to consume Core |
| kritva-sense | `contract/SENSE_CONTRACT.md`, `contract/sense-sample.schema.json` | 0.1.0 | `543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77` (tag `v0.2.0`; tag `v0.1.0` is `07c48d5398bea19e58f7bd4c7a5af55041b28df5`) | APPROVED (owner approval; interim D-047 review, not independent) | Sense adapter (SDK-005) | pin contract 0.1.0; other versions are `UNSUPPORTED_CONTRACT_VERSION` | none known; Mind pins the same tag |
| kritva-motion | `contract/MOTION_CONTRACT.md` and schemas | 0.1.0-draft rev 5 | none (not tagged) | DRAFT (task KOS-MOTION-001 ACCEPTED, but the contract itself stays draft and untagged) | Motion adapter (SDK-009) | do not pin | contract approval and tag |
| kritva-mind | `contract/` schemas, `contract/README.md` | 0.1.0-draft | tag `v0.1.0` = `8cc33291919ce5599d60351d0cf181ea19cdf0ff` | UNCLEAR, treated as DRAFT: task KOS-MIND-001 is ACCEPTED (2026-11-10) and tag `v0.1.0` exists, but `contract/README.md` still says "PROPOSED, 0.1.0-draft ... not accepted" | Mind adapter (SDK-009) | do not pin until Mind confirms contract status | clarification from the Mind repository |
| kritva-skill | `docs/design/MIND_SKILL_INTERFACE.md` | proposed | none | PROPOSED (KOS-SKILL-001 IN_PROGRESS; no Skill interface schema exists) | Skill adapter (SDK-009) | do not pin | approved interface and schema |
| Sim | none | n/a | n/a | NOT_AVAILABLE (placement open per D-144) | simulation adapter (SDK-006) | n/a | placement decision and artifact interface |
| Control Plane | none | n/a | n/a | NOT_AVAILABLE (planned separate repository, D-148) | Control Plane client (SDK-004) | n/a | approved API and security boundary |

Upstream heads when verified: kritva-core `42253f9`, kritva-sense `f33b67b`, kritva-mind `cbb96c8`, kritva-motion `c68d6bb`, kritva-skill `e0d9cc2`.

## Findings from the verification

1. **Core has no Python or network surface.** Core R1.0 documents a C++ public API under `include/kritva/core/` with no HTTP, RPC, socket or Python binding. The SDK has no service to be a client of, so SDK-003 ("core client") and the "HTTP transport first" choice in ADR-003 rest on an assumption with no upstream contract. SDK-001 must decide what the first real consumable surface is: a Control Plane service, a Community runtime interface, or contract-schema validation only.
2. **Mind status is inconsistent upstream.** The task is accepted and a tag exists, yet the contract README still says draft. Ask the Mind repository; do not resolve it here.
3. **Community still lists `sdk/` as planned in-tree.** `kritvaos-community` README predates D-149, which moved SDK placement to kritva-sdk. That is a Community documentation update, outside this repository.
4. **Program documents** `v2/architecture/SDK_CONTRACTS.md` and per-component contract documents do not exist in kritva-program and must not be cited. `v2/PRS.md` and `v2/REQUIREMENT_TRACEABILITY.md` are skeletons.
