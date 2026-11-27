#!/usr/bin/env python3
"""make test: runs the unit tests, the integration gate and the regression gate once each. Standard library only.

Prints the three results separately and fails if any one fails, is incomplete or did not run. The integration gate runs
with --full (the pinned kritva-sense oracle, PyPI or a wheelhouse, and jsonschema are needed; see TESTING.md).
Exit 0 all three passed; otherwise the highest exit code among them.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = (
    ("test-unit", [sys.executable, "-m", "unittest", "discover", "-s", "tests/unit"]),
    ("test-integration", [sys.executable, "scripts/integration_gate.py", "--full"]),
    ("test-regression", [sys.executable, "scripts/regression_gate.py"]),
)


def main():
    results = []
    for name, cmd in STEPS:
        print(f"\n[test] >>> {name}", flush=True)
        results.append((name, subprocess.run(cmd, cwd=ROOT, check=False).returncode))
    print("\n[test] results")
    for name, code in results:
        print(f"  {name:18s} {'PASS' if code == 0 else 'INCOMPLETE' if code == 4 else 'FAIL'} (exit {code})")
    worst = max(code for _, code in results)
    return worst


if __name__ == "__main__":
    sys.exit(main())
