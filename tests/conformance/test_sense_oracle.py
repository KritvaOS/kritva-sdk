"""Cross-validation of kritva_sdk.sense against the pinned kritva-sense reference implementation (AC-008).

kritva-sense is a TEST-ONLY ORACLE here. The SDK never imports it at runtime and never depends on it. The oracle is a
checkout of kritva-sense at the exact commit recorded in the vendored provenance, named by KRITVA_SENSE_ORACLE:

    git clone https://github.com/KritvaOS/kritva-sense oracle && git -C oracle checkout <commit>
    KRITVA_SENSE_ORACLE=$PWD/oracle python3 -m unittest discover -s tests/conformance -v

With KRITVA_REQUIRE_ORACLE=1 (CI) an unavailable oracle is a FAILURE, never a skip. Without it, tests skip with an
explicit reason. A checkout whose HEAD is not the recorded commit always fails. Standard library only.
"""
import copy
import importlib
import json
import os
import random
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kritva_sdk import sense  # noqa: E402

DATA = ROOT / "tests" / "data" / "sense"
PIN = json.loads((ROOT / "src" / "kritva_sdk" / "_schemas" / "sense" / "PROVENANCE.json").read_text())["files"][0]["commit"]
REQUIRED = os.environ.get("KRITVA_REQUIRE_ORACLE") == "1"
ORACLE_DIR = os.environ.get("KRITVA_SENSE_ORACLE", "")


def _load_oracle():
    """Return (modules, problem). modules is None when the oracle cannot be used."""
    if not ORACLE_DIR:
        return None, "KRITVA_SENSE_ORACLE is not set"
    head = subprocess.run(["git", "-C", ORACLE_DIR, "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    if head.returncode != 0:
        return None, f"{ORACLE_DIR} is not a git checkout (cannot verify the pinned commit)"
    if head.stdout.strip() != PIN:
        return None, f"oracle HEAD {head.stdout.strip()} is not the pinned commit {PIN}"
    sys.path.insert(0, str(Path(ORACLE_DIR) / "src"))
    return {n: importlib.import_module(f"kritva_sense.{n}") for n in ("validator", "generator", "conformance", "stream", "frame_graph")}, None


ORACLE, PROBLEM = _load_oracle()
# A wrong-commit checkout is never a skip, even outside CI.
HARD_FAIL = bool(ORACLE_DIR) and PROBLEM is not None and "pinned commit" in PROBLEM


class OracleAvailability(unittest.TestCase):
    def test_oracle_is_available_at_the_pinned_commit(self):
        if ORACLE is not None:
            return
        if REQUIRED or HARD_FAIL:
            self.fail(f"oracle unavailable: {PROBLEM}")
        self.skipTest(f"oracle not used: {PROBLEM} (set KRITVA_SENSE_ORACLE; CI sets KRITVA_REQUIRE_ORACLE=1)")


@unittest.skipIf(ORACLE is None, "oracle not available (see OracleAvailability)")
class OracleParity(unittest.TestCase):
    def assert_same(self, payload, tag=""):
        want = [tuple(v) for v in ORACLE["validator"].validate_sample(payload)]
        got = [v.as_tuple() for v in sense.validate_sample(payload)]
        self.assertEqual(got, want, f"{tag}: {payload!r}")

    def test_contract_constants_agree(self):
        v = ORACLE["validator"]
        self.assertEqual(sense.SENSE_CONTRACT_VERSION, v.CONTRACT_VERSION)
        self.assertEqual(sense.ERROR_CODES, tuple(v.ERROR_CODES))
        self.assertEqual(sense.FRAMES, tuple(v.FRAMES))
        self.assertEqual(sense.CLOCKS, tuple(v.CLOCKS))
        self.assertEqual(sense.VALIDITY_STATES, tuple(v.VALIDITY_STATES))
        self.assertEqual(sense.TIMESTAMP_UNIT, v.TIMESTAMP_UNIT)
        self.assertEqual({k: dict(m) for k, m in sense.KINDS.items()}, v.KINDS)

    def test_upstream_fixtures(self):
        n = 0
        for p in sorted(DATA.glob("*/*.json")):
            self.assert_same(json.loads(p.read_text(encoding="utf-8"))["sample"], p.name)
            n += 1
        self.assertGreaterEqual(n, 30)

    def test_generator_samples_and_faults(self):
        G = ORACLE["generator"]
        structural = {"bad_unit", "unknown_frame", "missing_measurement", "bad_timestamp", "bad_version"}
        checked = 0
        for kind in sense.KINDS:
            for seed in (0, 1, 7, 12345):
                for clock in sense.CLOCKS:
                    for frame in sense.FRAMES:
                        doc = G.generate_samples(kind, "gen.sensor", 3, seed, clock=clock, frame=frame)
                        for s in doc["samples"]:
                            self.assert_same(s, "generated")
                            self.assertEqual(sense.validate_sample(s), ())
                            self.assertEqual(sense.parse_sample(s).to_dict(), s)
                            checked += 1
            for fault, expected in G.SAMPLE_FAULTS.items():
                for seed in (1, 2):
                    doc = G.generate_samples(kind, "gen.sensor", 3, seed, faults={2: fault})
                    for i, s in enumerate(doc["samples"]):
                        self.assert_same(s, f"fault {fault}")
                        if i == 2 and fault in structural:
                            self.assertIn(expected, {v.code for v in sense.validate_sample(s)}, fault)
                        elif i == 2:
                            # validity-state, sequence, gap and boundary samples are conformant context-free
                            self.assertEqual(sense.validate_sample(s), (), fault)
                        checked += 1
        self.assertGreater(checked, 300)

    def test_conformance_harness_samples(self):
        C = ORACLE["conformance"]
        n = 0
        for case in C.build_cases():
            if case["operation"] != "sample":
                continue
            inp = case["input"]
            for key in ("sample", "previous"):
                if isinstance(inp.get(key), dict) or key in inp and inp[key] is not None:
                    self.assert_same(inp[key], case["id"] + ":" + key)
                    n += 1
            if case["expected"]["usable"]:
                self.assertEqual(sense.validate_sample(inp["sample"]), (), case["id"])
        self.assertGreater(n, 20)

    def test_seeded_mutations(self):
        base = json.loads((DATA / "valid" / "imu_valid.json").read_text())["sample"]
        junk = [None, True, False, 0, -1, 1, 1.5, float("nan"), float("inf"), "", "x", "VALID", "imu", "0.1.0", "base",
                "m/s^2", [], {}, [1], {"a": 1}, "ns", "utc", 10 ** 30]
        rng = random.Random(20261126)

        def paths(o, p=()):
            yield p
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    yield from paths(v, p + (k,))

        for i in range(4000):
            d = copy.deepcopy(base)
            for _ in range(rng.randint(1, 3)):
                p = rng.choice(list(paths(d)))
                if not p:
                    d = copy.deepcopy(rng.choice(junk))
                    break
                cur = d
                for k in p[:-1]:
                    cur = cur[k]
                r = rng.random()
                if r < .3:
                    cur.pop(p[-1], None)
                elif r < .4:
                    cur[rng.choice(["extra", "error_code", "timestamp"])] = copy.deepcopy(rng.choice(junk))
                elif r < .5 and isinstance(cur.get(p[-1]), dict):
                    cur[p[-1]]["zz"] = copy.deepcopy(rng.choice(junk))
                else:
                    cur[p[-1]] = copy.deepcopy(rng.choice(junk))
            if isinstance(d, dict):
                if rng.random() < .3:
                    d["validity"] = rng.choice(["VALID", "STALE", "MISSING", "INVALID", None, []])
                if rng.random() < .2:
                    d["kind"] = rng.choice(["range", "encoder", "temperature", "imu", "bogus"])
                if rng.random() < .2:
                    d["error_code"] = rng.choice(["STALE_DATA", "bogus", None])
            self.assert_same(d, f"mutation {i}")


if __name__ == "__main__":
    unittest.main()
