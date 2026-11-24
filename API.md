# Kritva SDK Public API Design

**Status:** SKELETON / PROPOSED. No API below is approved or implemented.

## Candidate namespace
```python
from kritva import KritvaClient, KritvaConfig

client = KritvaClient(config=KritvaConfig(...))
await client.connect()
robot = await client.robots.get(robot_id="...")
await client.aclose()
```

This is illustrative only. No class, method or import path is stable.

## Candidate domains
| Domain | Responsibility | Authority |
|---|---|---|
| Client / Config | Client construction, config and lifecycle | SDK |
| Robot | Identity, capability discovery and status views | approved Core/runtime contracts |
| Sense | Sensor metadata and streams | kritva-sense |
| Motion | Command submission and lifecycle | kritva-motion |
| Mind | Request/context/result | kritva-mind |
| Skill | Manifest and execution interface | kritva-skill |
| Control Plane | Remote job/service operations | approved Control Plane API |
| Simulation | Optional simulation integration | approved simulation contract |

Before implementation, each API specifies input/output, units, timestamps, lifecycle, errors, timeout, cancellation, idempotency, security and compatibility. All interfaces here remain proposals until reviewed and released.
