# Planning Changelog

## 2026-11-24
- Initial proposed V2 milestone mapping and eight-task SDK register.
- Central SDK repository/workstream registration remains pending.

## 2026-11-24 (review update)
- Owner decisions recorded: CODEOWNER `@dineshannayya`; repository visibility PUBLIC.
- Added ADR-001..003 and the contract dependency register.
- Narrowed KOS-SDK-005 to the Sense adapter; added KOS-SDK-009 for Motion, Mind and Skill (blocked on contract approval).
- Marked local M1 as a planning label with no program credit pending the SDK ownership decision.
- Ported hooks, CI workflows, gate config and preflight from kritva-skill; rewrote README to pass the README standard.

## 2026-11-24 (contract register verification)
- Verified the contract dependency register against upstream contents; recorded exact commits and statuses.
- Recorded that Core R1.0 has no Python or network surface, and that Mind's contract status is inconsistent upstream.

## 2026-11-24 (SDK-001 design alignment)
- First release re-scoped to a contract-first library (Sense 0.1.0); no Core client or network transport until an approved API exists.
- Distribution `kritva-sdk`, import `kritva_sdk`; vendored pinned schemas with drift check; hand-written typed models.
- Rewrote API.md and ARCHITECTURE.md; revised ADR-001..003, KOS-SDK-001 criteria and KOS-SDK-003 scope.
- Central change required: KOS-SDK-003 title and the TASKS.md pin in kritva-program planning_inventory.json.
