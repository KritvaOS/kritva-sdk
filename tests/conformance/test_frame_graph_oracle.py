"""Cross-validation of kritva_sdk.frame_graph against the pinned kritva-sense reference implementation (KOS-SDK-005).

kritva-sense is a TEST-ONLY ORACLE here, exactly as in test_sense_oracle.py: a checkout at the commit recorded in the
vendored provenance, named by KRITVA_SENSE_ORACLE, with KRITVA_REQUIRE_ORACLE=1 turning an unavailable oracle into a
failure. Three kinds of check, kept apart:

* diagnostic parity: identical (code, path, message) for every document, fixture, harness case and seeded mutation;
* numerical parity: resolved transforms and transformed points identical to the oracle's (the arithmetic is the same
  sequence of IEEE 754 operations, so equality is exact; the check also states the 1e-9 absolute tolerance);
* the harness decisions of the upstream conformance module.

Random cases use a fixed seed, and a failure prints the case. Standard library only.
"""
import copy
import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kritva_sdk.frame_graph as sdk  # noqa: E402
from test_sense_oracle import ORACLE  # noqa: E402

DATA = ROOT / "tests" / "data" / "frame_graph"
TOL = 1e-9


def fixtures():
    return [(p.relative_to(DATA).as_posix(), json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(DATA.glob("*/*.json"))]


def mine(violations):
    return [v.as_tuple() for v in violations]


def theirs(violations):
    return [tuple(v) for v in violations]


@unittest.skipIf(ORACLE is None, "oracle not available (see test_sense_oracle.OracleAvailability)")
class FrameGraphOracleParity(unittest.TestCase):
    def assert_graph_same(self, doc, tag=""):
        self.assertEqual(mine(sdk.validate_graph(doc)), theirs(ORACLE["frame_graph"].validate_graph(doc)),
                         f"{tag}: {json.dumps(doc, default=str)[:600]}")

    def assert_resolve_same(self, doc, source, target, tag=""):
        o_t, o_v = ORACLE["frame_graph"].resolve(doc, source, target)
        r = sdk.resolve(doc, source, target)
        where = f"{tag}: {source}->{target} {json.dumps(doc, default=str)[:400]}"
        self.assertEqual(mine(r.violations), theirs(o_v), where)
        if o_t is None:
            self.assertIsNone(r.transform, where)
            return None
        self.assertEqual(r.transform.to_dict(), o_t, where)
        return o_t

    def test_contract_constants_agree(self):
        F = ORACLE["frame_graph"]
        self.assertEqual(sdk.FRAME_GRAPH_CONTRACT_VERSION, F.FRAME_GRAPH_VERSION)
        self.assertEqual(sdk.FG_ERROR_CODES, tuple(F.ERROR_CODES))
        self.assertEqual(sdk._TRANSFORM_FIELDS, tuple(F.TRANSFORM_FIELDS))
        self.assertEqual(sdk._TRANSLATION_FIELDS, tuple(F.TRANSLATION_FIELDS))
        self.assertEqual(sdk._ROTATION_FIELDS, tuple(F.ROTATION_FIELDS))
        self.assertEqual((sdk.QUAT_TOLERANCE, sdk.SIGN_EPSILON, sdk.TRANSLATION_UNIT),
                         (F.QUAT_TOLERANCE, F.SIGN_EPSILON, F.TRANSLATION_UNIT))
        self.assertEqual(sdk.FRAME_ID_PATTERN, F.FRAME_ID_RE.pattern)

    def test_fixture_parity_diagnostics_and_numerics(self):
        items = fixtures()
        self.assertGreaterEqual(len(items), 42)
        resolved = 0
        for name, doc in items:
            self.assert_graph_same(doc["graph"], name)
            for case in doc.get("resolve", []):
                got = self.assert_resolve_same(doc["graph"], case["from"], case["to"], name)
                self.assertIsNotNone(got, name)
                want = case["expected"]
                for k in "xyz":
                    self.assertLessEqual(abs(got["translation"][k] - want["translation"][k]), TOL, name)
                for k in "wxyz":
                    self.assertLessEqual(abs(got["rotation"][k] - want["rotation"][k]), TOL, name)
                resolved += 1
        self.assertGreaterEqual(resolved, 15)

    def test_every_pair_of_frames_in_every_fixture(self):
        pairs = 0
        for name, doc in fixtures():
            g = doc["graph"]
            transforms = g.get("transforms") if isinstance(g, dict) and isinstance(g.get("transforms"), list) else []
            frames = sorted({f for t in transforms if isinstance(t, dict) for f in (t.get("parent"), t.get("child"))
                             if isinstance(f, str)} | {"ghost"})
            for a in frames:
                for b in frames:
                    self.assert_resolve_same(g, a, b, name)
                    pairs += 1
        self.assertGreater(pairs, 100)

    def test_conformance_harness_frame_cases(self):
        C = ORACLE["conformance"]
        n = 0
        for case in C.build_cases():
            if case["operation"] != "frame":
                continue
            inp = case["input"]
            self.assert_graph_same(inp["graph"], case["id"])
            got = self.assert_resolve_same(inp["graph"], inp["source"], inp["target"], case["id"])
            exp = case["expected"]
            self.assertEqual(got is not None, exp["ok"], case["id"])
            if not exp["ok"]:
                self.assertEqual(sorted({v.code for v in sdk.resolve(inp["graph"], inp["source"], inp["target"]).violations}),
                                 exp["codes"], case["id"])
            if got is not None and exp.get("transform"):
                for k in "xyz":
                    self.assertLessEqual(abs(got["translation"][k] - exp["transform"]["translation"][k]), TOL, case["id"])
                for k in "wxyz":
                    self.assertLessEqual(abs(got["rotation"][k] - exp["transform"]["rotation"][k]), TOL, case["id"])
            n += 1
        self.assertGreaterEqual(n, 20)

    def test_generated_graphs_and_defects(self):
        G, F = ORACLE["generator"], ORACLE["frame_graph"]
        n = 0
        for seed in (0, 1, 2, 7, 99, 12345):
            for extra in (0, 1, 3, 6):
                doc = G.generate_graph(seed, extra_frames=extra)["graph"]
                self.assert_graph_same(doc, f"generated {seed}/{extra}")
                self.assertEqual(sdk.validate_graph(doc), ())
                self.assertEqual(sdk.parse_frame_graph(doc).to_dict(), doc)
                frames = sorted({f for t in doc["transforms"] for f in (t["parent"], t["child"])})
                for a in frames:
                    for b in frames:
                        got = self.assert_resolve_same(doc, a, b, f"generated {seed}/{extra}")
                        # numerical parity of points through the resolved transform
                        for pt in ((0, 0, 0), (1, 2, 3), (-4.5, 0.25, 7.0)):
                            want = F.transform_point(got, pt)
                            self.assertEqual(sdk.transform_point(got, pt), want)
                            self.assertEqual(sdk.resolve(doc, a, b).transform.apply(pt), want)
                        n += 1
            for defect in G.GRAPH_DEFECTS:
                doc = G.generate_graph(seed, extra_frames=2, defect=defect)["graph"]
                self.assert_graph_same(doc, f"defect {defect}")
                self.assertNotEqual(sdk.validate_graph(doc), (), defect)
        self.assertGreater(n, 200)

    def test_round_trip_through_the_inverse(self):
        G = ORACLE["generator"]
        doc = G.generate_graph(5, extra_frames=4)["graph"]
        frames = sorted({f for t in doc["transforms"] for f in (t["parent"], t["child"])})
        for a in frames:
            for b in frames:
                fwd, back = sdk.resolve(doc, a, b).transform, sdk.resolve(doc, b, a).transform
                for pt in ((0, 0, 0), (1, -2, 3.5)):
                    again = back.apply(fwd.apply(pt))
                    for g, w in zip(again, pt):
                        self.assertLessEqual(abs(g - w), TOL)

    def test_seeded_mutations(self):
        bases = [doc["graph"] for name, doc in fixtures() if name.startswith("valid/") and doc["graph"]["transforms"]]
        junk = [None, True, False, 0, -1, 1, 2, 0.5, 1.5, float("nan"), float("inf"), "", "x", "world", "base", "m",
                "mm", "0.1.0", "A", [], {}, [1], {"a": 1}, 10 ** 30, 0.7071067811865476]
        rng = random.Random(20261128)
        F = ORACLE["frame_graph"]

        def paths(o, p=()):
            yield p
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    yield from paths(v, p + (k,))
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    yield from paths(v, p + (i,))

        for i in range(3000):
            d = copy.deepcopy(rng.choice(bases))
            for _ in range(rng.randint(1, 3)):
                p = rng.choice(list(paths(d)))
                if not p:
                    d = copy.deepcopy(rng.choice(junk))
                    break
                cur = d
                for k in p[:-1]:
                    cur = cur[k]
                r = rng.random()
                if r < .2 and isinstance(cur, dict):
                    cur.pop(p[-1], None)
                elif r < .3 and isinstance(cur, list) and cur:
                    cur.pop(p[-1])
                elif r < .4 and isinstance(cur, list):
                    cur.insert(p[-1], copy.deepcopy(rng.choice(cur)))
                elif r < .5 and isinstance(cur, dict):
                    cur[rng.choice(["extra", "parent", "child", "translation_unit"])] = copy.deepcopy(rng.choice(junk))
                else:
                    cur[p[-1]] = copy.deepcopy(rng.choice(junk))
            self.assert_graph_same(d, f"mutation {i}")
            frames = ["world", "base", "sensor", "ghost", None, "A"]
            a, b = rng.choice(frames), rng.choice(frames)
            self.assert_resolve_same(d, a, b, f"mutation {i}")
            if isinstance(d, dict) and not F.validate_graph(d):
                self.assertEqual(sdk.parse_frame_graph(d).to_dict(), d)


if __name__ == "__main__":
    unittest.main()
