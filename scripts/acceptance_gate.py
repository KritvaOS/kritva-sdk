#!/usr/bin/env python3
"""Acceptance gate (make acceptance): runs the automatable acceptance criteria of KOS-SDK-001..003. Stdlib only.

    python3 scripts/acceptance_gate.py [--full]

tests/acceptance/ACCEPTANCE_MAP.json maps every criterion AC-nnn found in the task ACCEPTANCE_CRITERIA.md files to
automated tests or to a recorded manual review. An unmapped criterion, a stale map entry, an automated criterion with
no tests, or a failing test fails the gate. Criteria whose tests need the network or the pinned kritva-sense oracle run
with --full (CI); without it they are SKIPPED and the run is INCOMPLETE. MANUAL criteria are listed and never reported
as passed: their evidence is a recorded review. Exit 0 all automated criteria passed and every criterion is classified,
1 failure, 2 usage error, 4 incomplete (a skip).
"""
import json
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "tests" / "acceptance" / "ACCEPTANCE_MAP.json"
TASKS = ("KOS-SDK-001", "KOS-SDK-002", "KOS-SDK-003")


def criteria_ids():
    found = []
    for task in TASKS:
        files = sorted(ROOT.glob(f"planning/milestones/*/tasks/{task}/ACCEPTANCE_CRITERIA.md"))
        if len(files) != 1:
            raise SystemExit(f"acceptance: expected one criteria file for {task}, found {len(files)}")
        found += [f"{task}/{m}" for m in re.findall(r"^\| (AC-\d+) \|", files[0].read_text(encoding="utf-8"), re.M)]
    return found


def oracle_dir():
    for cand in (os.environ.get("KRITVA_SENSE_ORACLE", ""), str(ROOT / ".cache" / "kritva-sense")):
        if cand and Path(cand).is_dir():
            return cand
    return None


def run_tests(specs):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for spec in specs:
        directory, name = spec.split("::", 1)
        path = str(ROOT / directory)
        if path not in sys.path:
            sys.path.insert(0, path)
        suite.addTests(loader.loadTestsFromName(name))
    if suite.countTestCases() == 0:
        return None
    result = unittest.TestResult()
    suite.run(result)
    return result


def main(argv):
    if argv not in ([], ["--full"]):
        print(__doc__)
        return 2
    full = bool(argv)
    if full:
        os.environ["KRITVA_PACKAGING_TESTS"] = "1"
        os.environ["KRITVA_REQUIRE_ORACLE"] = "1"
        d = oracle_dir()
        if d:
            os.environ["KRITVA_SENSE_ORACLE"] = d
    sys.path.insert(0, str(ROOT / "src"))
    mapping = json.loads(MAP.read_text(encoding="utf-8"))
    mapping.pop("_note", None)
    ids = criteria_ids()
    problems = []
    for cid in ids:
        if cid not in mapping:
            problems.append(f"{cid}: not in ACCEPTANCE_MAP.json")
    for cid in mapping:
        if cid not in ids:
            problems.append(f"{cid}: map entry has no criterion (stale)")
    rows = []
    for cid in ids:
        entry = mapping.get(cid)
        if entry is None:
            continue
        if entry["mode"] == "MANUAL":
            rows.append((cid, "MANUAL", entry["evidence"]))
            continue
        res = run_tests(entry["tests"])
        if res is None:
            rows.append((cid, "FAIL", "no tests found for the mapped names"))
        elif res.failures or res.errors:
            first = (res.failures + res.errors)[0]
            rows.append((cid, "FAIL", f"{first[0]}: {first[1].strip().splitlines()[-1]}"))
        elif res.skipped:
            rows.append((cid, "SKIP", f"{len(res.skipped)} of {res.testsRun} tests skipped: {res.skipped[0][1]}"))
        else:
            rows.append((cid, "PASS", f"{res.testsRun} tests"))
    for cid, status, detail in rows:
        print(f"{cid} {status} {detail}")
    for p in problems:
        print(f"PROBLEM {p}")
    count = {s: sum(1 for r in rows if r[1] == s) for s in ("PASS", "FAIL", "SKIP", "MANUAL")}
    print(f"acceptance gate: {len(ids)} criteria; automated PASS {count['PASS']}, FAIL {count['FAIL']}, SKIP {count['SKIP']}; "
          f"MANUAL {count['MANUAL']} (listed, not passed: evidence is a recorded review)")
    if problems or count["FAIL"] or not ids:
        return 1
    if count["SKIP"]:
        print("INCOMPLETE: a skipped criterion is not a pass (exit 4)")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
