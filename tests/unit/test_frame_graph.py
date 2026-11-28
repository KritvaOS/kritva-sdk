"""Unit tests for the frame graph 0.1.0 models, validation and resolution (KOS-SDK-005). Standard library only.

Cases are authored here from the prose contract (FRAME_GRAPH_CONTRACT.md), with hand-derived answers, and checked
against the upstream-authored fixtures (with their own expectations) vendored under tests/data/frame_graph. Parity
with the pinned reference implementation is tests/conformance/test_frame_graph_oracle.py.
"""
import copy
import dataclasses
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import kritva_sdk.frame_graph as fg  # noqa: E402
from kritva_sdk.compat import supported_contracts  # noqa: E402
from kritva_sdk.errors import ContractError, SdkError  # noqa: E402
from kritva_sdk.frame_graph import (FrameGraph, FrameGraphContractError, FrameGraphUsageError, FrameTransform,  # noqa: E402
                                    Quaternion, Resolution, ResolvedTransform, Translation, UnsupportedFrameGraphVersion,
                                    parse_frame_graph, resolve, transform_point, validate_graph, validate_transform)

DATA = ROOT / "tests" / "data" / "frame_graph"
TOL = 1e-9
H = math.sqrt(0.5)


def load(group):
    return [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((DATA / group).glob("*.json"))]


def edge(parent, child, t=(0.0, 0.0, 0.0), q=(1.0, 0.0, 0.0, 0.0)):
    return {"parent": parent, "child": child, "translation": dict(zip("xyz", t)), "translation_unit": "m",
            "rotation": dict(zip("wxyz", q))}


def graph(*edges):
    return {"contract_version": "0.1.0", "transforms": list(edges)}


def codes(violations):
    return sorted({v.code for v in violations})


def near(got, want):
    return (all(abs(got["translation"][k] - want["translation"][k]) <= TOL for k in "xyz")
            and all(abs(got["rotation"][k] - want["rotation"][k]) <= TOL for k in "wxyz"))


class DeclarationTest(unittest.TestCase):
    def test_contract_declared_and_codes_listed(self):
        self.assertEqual(supported_contracts()["frame_graph"], ("0.1.0",))
        self.assertEqual(fg.FRAME_GRAPH_CONTRACT_VERSION, "0.1.0")
        self.assertEqual(len(fg.FG_ERROR_CODES), 14)
        self.assertTrue(all(c.startswith("FG_") for c in fg.FG_ERROR_CODES))
        self.assertEqual((fg.QUAT_TOLERANCE, fg.SIGN_EPSILON, fg.TRANSLATION_UNIT), (1e-9, 1e-12, "m"))

    def test_vendored_contract_states_the_convention(self):
        doc = (ROOT / "src" / "kritva_sdk" / "_schemas" / "sense" / "FRAME_GRAPH_CONTRACT.md").read_text(encoding="utf-8")
        for code in fg.FG_ERROR_CODES:
            self.assertIn("`%s`" % code, doc)
        for needle in ("p_parent = R(q) * p_child + t", "Hamilton", "unit quaternion", "one parent"):
            self.assertIn(needle, doc)


class VendoredFixtureTest(unittest.TestCase):
    def test_valid_fixtures_validate_and_resolve_as_expected(self):
        items = load("valid")
        self.assertGreaterEqual(len(items), 8)
        for name, doc in items:
            with self.subTest(name=name):
                self.assertEqual(validate_graph(doc["graph"]), ())
                parse_frame_graph(doc["graph"])
                for case in doc["resolve"]:
                    r = resolve(doc["graph"], case["from"], case["to"])
                    self.assertTrue(r.ok, (name, case))
                    self.assertTrue(near(r.transform.to_dict(), case["expected"]), (name, case, r))

    def test_invalid_fixtures_report_exactly_the_expected_codes(self):
        items = load("invalid")
        self.assertGreaterEqual(len(items), 34)
        for name, doc in items:
            with self.subTest(name=name):
                got = validate_graph(doc["graph"])
                self.assertEqual(codes(got), sorted(doc["expected_codes"]))
                self.assertFalse(resolve(doc["graph"], "world", "base").ok)
                with self.assertRaises(FrameGraphContractError):
                    parse_frame_graph(doc["graph"])

    def test_every_error_code_is_exercised_by_a_fixture_or_a_resolution_case(self):
        seen = {c for _, doc in load("invalid") for c in doc["expected_codes"]}
        self.assertEqual(set(fg.FG_ERROR_CODES) - seen, {"FG_FRAME_NOT_IN_GRAPH", "FG_NO_PATH"})


class TransformRecordTest(unittest.TestCase):
    def test_conformant_record_and_integers(self):
        self.assertEqual(validate_transform(edge("world", "base", (1, 2, 3))), ())
        rec = edge("world", "base", (1, 2, 3), (1, 0, 0, 0))
        self.assertEqual(validate_transform(rec), ())

    def test_record_defects(self):
        cases = {
            "FG_MALFORMED": [5, None, "x", [], edge("world", None)],
            "FG_SELF_LINK": [edge("base", "base")],
            "FG_INVALID_FRAME_ID": [edge("World", "base"), edge("world", "0base"), edge("world", "a" * 33),
                                    edge("", "base"), edge("world", "base-link")],
            "FG_NON_FINITE": [edge("world", "base", (float("nan"), 0, 0)), edge("world", "base", (0, float("inf"), 0))],
            "FG_NOT_UNIT_QUATERNION": [edge("world", "base", q=(2, 0, 0, 0)), edge("world", "base", q=(0, 0, 0, 0)),
                                       edge("world", "base", q=(1.0 + 1.1e-9, 0, 0, 0))],
        }
        for code, recs in cases.items():
            for rec in recs:
                with self.subTest(code=code, rec=rec):
                    self.assertIn(code, codes(validate_transform(rec)))
        rec = edge("world", "base")
        rec["translation_unit"] = "mm"
        self.assertEqual(codes(validate_transform(rec)), ["FG_INVALID_UNIT"])
        rec = edge("world", "base")
        del rec["rotation"]
        self.assertEqual(codes(validate_transform(rec)), ["FG_MISSING_FIELD"])
        rec = edge("world", "base")
        rec["extra"] = 1
        rec["rotation"]["extra"] = 1
        self.assertEqual(codes(validate_transform(rec)), ["FG_UNKNOWN_FIELD"])
        rec = edge("world", "base")
        rec["translation"] = [1, 2, 3]
        rec["rotation"] = {"roll": 0, "pitch": 0, "yaw": 0}
        self.assertIn("FG_MALFORMED", codes(validate_transform(rec)))
        for bad in (True, "1", None):
            rec = edge("world", "base")
            rec["translation"]["x"] = bad
            self.assertEqual(codes(validate_transform(rec)), ["FG_MALFORMED"], bad)

    def test_quaternion_tolerance_and_negated_quaternion(self):
        self.assertEqual(validate_transform(edge("world", "base", q=(1.0 + 9e-10, 0, 0, 0))), ())
        self.assertEqual(validate_transform(edge("world", "base", q=(-1, 0, 0, 0))), ())
        self.assertEqual(validate_transform(edge("world", "base", q=(-H, 0, 0, -H))), ())

    def test_results_are_sorted_and_input_is_never_mutated(self):
        rec = edge("base", "base", q=(2, 0, 0, 0))
        rec["extra"] = 1
        before = copy.deepcopy(rec)
        a = validate_transform(rec)
        self.assertEqual(a, tuple(sorted(a)))
        self.assertEqual(rec, before)
        self.assertEqual(validate_transform(copy.deepcopy(rec)), a)


class GraphRulesTest(unittest.TestCase):
    def test_document_defects(self):
        self.assertEqual(codes(validate_graph([])), ["FG_MALFORMED"])
        self.assertEqual(codes(validate_graph({"transforms": []})), ["FG_MISSING_FIELD"])
        self.assertEqual(codes(validate_graph({"contract_version": "0.1.0"})), ["FG_MISSING_FIELD"])
        self.assertEqual(codes(validate_graph({"contract_version": 1, "transforms": []})), ["FG_MALFORMED"])
        self.assertEqual(codes(validate_graph({"contract_version": "0.2.0", "transforms": []})),
                         ["FG_UNSUPPORTED_VERSION"])
        self.assertEqual(codes(validate_graph({"contract_version": "0.1.0", "transforms": {}})), ["FG_MALFORMED"])
        self.assertEqual(codes(validate_graph({**graph(), "extra": 1})), ["FG_UNKNOWN_FIELD"])
        self.assertEqual(validate_graph(graph()), ())

    def test_duplicate_edge_multiple_parents_and_cycles(self):
        a = edge("world", "base")
        self.assertEqual(codes(validate_graph(graph(a, copy.deepcopy(a)))), ["FG_DUPLICATE_EDGE"])
        self.assertEqual(codes(validate_graph(graph(a, edge("arm", "base")))), ["FG_MULTIPLE_PARENTS"])
        self.assertEqual(codes(validate_graph(graph(edge("a", "b"), edge("b", "a")))), ["FG_CYCLE"])
        ring = validate_graph(graph(edge("a", "b"), edge("b", "c"), edge("c", "a")))
        self.assertEqual([v.code for v in ring], ["FG_CYCLE"])
        self.assertIn("a, b, c", ring[0].message)
        two = validate_graph(graph(edge("a", "b"), edge("b", "a"), edge("c", "d"), edge("d", "c")))
        self.assertEqual([v.code for v in two], ["FG_CYCLE", "FG_CYCLE"])

    def test_siblings_and_deep_chains_are_fine(self):
        self.assertEqual(validate_graph(graph(edge("world", "a"), edge("world", "b"), edge("world", "c"))), ())
        chain = [edge("n%d" % i, "n%d" % (i + 1)) for i in range(200)]
        self.assertEqual(validate_graph(graph(*chain)), ())

    def test_a_defect_anywhere_makes_the_whole_graph_non_conformant(self):
        g = graph(edge("world", "base"), edge("base", "base"))
        self.assertFalse(resolve(g, "world", "base").ok)
        self.assertEqual(codes(resolve(g, "world", "base").violations), ["FG_SELF_LINK"])


class ResolveTest(unittest.TestCase):
    def test_hand_derived_worked_example(self):
        g = graph(edge("world", "base", (1, 2, 0), (H, 0, 0, H)), edge("base", "sensor", (0.1, 0, 0.2)))
        r = resolve(g, "sensor", "world")
        self.assertTrue(r.ok)
        self.assertEqual(r.violations, ())
        self.assertTrue(near(r.transform.to_dict(), {"translation": {"x": 1.0, "y": 2.1, "z": 0.2},
                                                     "rotation": {"w": H, "x": 0, "y": 0, "z": H}}))
        p = r.transform.apply((1, 0, 0))                       # sensor x-axis, in world
        self.assertAlmostEqual(p[0], 1.0, delta=TOL)
        self.assertAlmostEqual(p[1], 3.1, delta=TOL)
        self.assertAlmostEqual(p[2], 0.2, delta=TOL)

    def test_reverse_is_the_inverse_and_siblings_go_through_the_ancestor(self):
        g = graph(edge("world", "a", (1, 0, 0), (H, 0, 0, H)), edge("world", "b", (0, 5, 0)))
        fwd = resolve(g, "a", "b").transform
        back = resolve(g, "b", "a").transform
        for pt in ((0, 0, 0), (1, 2, 3), (-4.5, 0.25, 7)):
            there = fwd.apply(pt)
            again = back.apply(there)
            for got, want in zip(again, pt):
                self.assertAlmostEqual(got, want, delta=TOL)

    def test_same_frame_is_the_identity_and_only_for_a_frame_of_the_graph(self):
        g = graph(edge("world", "base", (3, 0, 0)))
        r = resolve(g, "base", "base")
        self.assertEqual(r.transform.to_dict(), {"translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                                                 "translation_unit": "m",
                                                 "rotation": {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}})
        self.assertEqual(codes(resolve(g, "nowhere", "nowhere").violations), ["FG_FRAME_NOT_IN_GRAPH"])

    def test_unknown_frames_and_no_path_never_invent_a_transform(self):
        g = graph(edge("world", "base"), edge("arm", "hand"))
        r = resolve(g, "world", "ghost")
        self.assertIsNone(r.transform)
        self.assertEqual([(v.code, v.path) for v in r.violations], [("FG_FRAME_NOT_IN_GRAPH", "target")])
        both = resolve(g, "ghost", "phantom")
        self.assertEqual([(v.code, v.path) for v in both.violations],
                         [("FG_FRAME_NOT_IN_GRAPH", "source"), ("FG_FRAME_NOT_IN_GRAPH", "target")])
        np = resolve(g, "world", "hand")
        self.assertIsNone(np.transform)
        self.assertEqual([v.code for v in np.violations], ["FG_NO_PATH"])
        self.assertEqual(resolve(graph(), "world", "base").violations[0].code, "FG_FRAME_NOT_IN_GRAPH")

    def test_bad_frame_arguments_are_contract_diagnostics(self):
        g = graph(edge("world", "base"))
        for bad, code in ((None, "FG_MALFORMED"), (3, "FG_MALFORMED"), ("World", "FG_INVALID_FRAME_ID"),
                          ("", "FG_INVALID_FRAME_ID")):
            self.assertEqual([v.code for v in resolve(g, bad, "base").violations], [code], bad)

    def test_canonical_form(self):
        g = graph(edge("world", "base", (0, 0, 0), (-1, 0, 0, 0)), edge("world", "other", (0, 0, 0), (0, -1, 0, 0)))
        a = resolve(g, "base", "world").transform
        self.assertEqual(a.rotation, (1.0, 0.0, 0.0, 0.0))
        b = resolve(g, "other", "world").transform
        self.assertEqual(b.rotation, (0.0, 1.0, 0.0, 0.0))
        for r in (a, b):
            for c in (*r.translation, *r.rotation):
                self.assertFalse(c == 0 and math.copysign(1.0, c) < 0, "negative zero")
        self.assertAlmostEqual(math.hypot(*b.rotation), 1.0, delta=1e-15)

    def test_resolution_is_deterministic_and_does_not_mutate_the_graph(self):
        g = graph(edge("world", "a", (1, 2, 3), (H, 0, H, 0)), edge("a", "b", (0.5, 0, 0), (H, H, 0, 0)))
        before = copy.deepcopy(g)
        first = resolve(g, "b", "world")
        self.assertEqual(first, resolve(copy.deepcopy(g), "b", "world"))
        self.assertEqual(g, before)

    def test_long_chain_resolves(self):
        chain = [edge("n%d" % i, "n%d" % (i + 1), (1, 0, 0)) for i in range(200)]
        r = resolve(graph(*chain), "n200", "n0")
        self.assertAlmostEqual(r.transform.translation[0], 200.0, delta=TOL)


class ResolutionTypeTest(unittest.TestCase):
    def test_a_resolution_has_a_transform_or_violations_never_both_or_neither(self):
        good = resolve(graph(edge("world", "base")), "base", "world")
        with self.assertRaises(ValueError):
            Resolution(None, ())
        with self.assertRaises(ValueError):
            Resolution(good.transform, good.violations + (fg.Violation("$", "FG_NO_PATH", "x"),))
        self.assertTrue(good.ok)
        self.assertIs(good.unwrap(), good.transform)
        bad = resolve(graph(edge("world", "base")), "base", "ghost")
        self.assertFalse(bad.ok)
        with self.assertRaises(FrameGraphContractError) as cm:
            bad.unwrap()
        self.assertEqual(cm.exception.code, "FG_FRAME_NOT_IN_GRAPH")


class TransformPointTest(unittest.TestCase):
    def test_apply_matches_the_convention(self):
        r = resolve(graph(edge("world", "base", (1, 2, 0), (H, 0, 0, H))), "base", "world").transform
        p = transform_point(r, (1, 0, 0))                      # +x of base is +y of world after a 90 degree turn
        for got, want in zip(p, (1.0, 3.0, 0.0)):
            self.assertAlmostEqual(got, want, delta=TOL)
        self.assertEqual(transform_point(r.to_dict(), (1, 0, 0)), p)

    def test_misuse_is_a_typed_sdk_error(self):
        r = resolve(graph(edge("world", "base")), "base", "world").transform
        for bad in ((1, 2), (1, 2, 3, 4), "abc", None, 5, (1, 2, "3"), (1, 2, True), (1, float("nan"), 0),
                    (float("inf"), 0, 0), {"x": 1, "y": 2, "z": 3}):
            with self.assertRaises(FrameGraphUsageError, msg=repr(bad)):
                transform_point(r, bad)
        for bad in (None, 3, "t", {"translation": {}}, [1, 2, 3]):
            with self.assertRaises(FrameGraphUsageError, msg=repr(bad)):
                transform_point(bad, (0, 0, 0))
        self.assertTrue(issubclass(FrameGraphUsageError, SdkError))
        self.assertTrue(issubclass(FrameGraphUsageError, ValueError))
        self.assertNotIsInstance(FrameGraphUsageError("x"), ContractError)


class ModelTest(unittest.TestCase):
    def test_parse_roundtrip_and_resolution_on_the_model(self):
        doc = graph(edge("world", "base", (1, 2, 3), (H, 0, 0, H)), edge("base", "sensor", (0.1, 0, 0.2)))
        g = parse_frame_graph(doc)
        self.assertIsInstance(g, FrameGraph)
        self.assertEqual(g.to_dict(), doc)
        self.assertEqual(parse_frame_graph(g.to_dict()), g)
        self.assertEqual(g.frames(), ("base", "sensor", "world"))
        self.assertEqual(g.resolve("sensor", "world"), resolve(doc, "sensor", "world"))
        self.assertEqual(resolve(g, "sensor", "world"), resolve(doc, "sensor", "world"))
        self.assertIsInstance(g.transforms[0], FrameTransform)
        self.assertIsInstance(g.transforms[0].translation, Translation)
        self.assertIsInstance(g.transforms[0].rotation, Quaternion)

    def test_wire_values_are_kept(self):
        doc = graph(edge("world", "base", (1, 2, 3), (1, 0, 0, 0)))
        g = parse_frame_graph(doc)
        self.assertEqual(g.to_dict()["transforms"][0]["translation"], {"x": 1, "y": 2, "z": 3})
        self.assertIsInstance(g.transforms[0].translation.x, int)

    def test_models_are_immutable_and_validate_on_construction(self):
        g = parse_frame_graph(graph(edge("world", "base")))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            g.contract_version = "9"             # type: ignore[misc]
        with self.assertRaises(ContractError) as cm:
            Quaternion(2, 0, 0, 0)
        self.assertEqual(cm.exception.code, "FG_NOT_UNIT_QUATERNION")
        with self.assertRaises(ContractError):
            Translation(float("nan"), 0, 0)
        with self.assertRaises(ContractError):
            Translation(True, 0, 0)
        with self.assertRaises(ContractError):
            FrameTransform("base", "base", Translation(0, 0, 0), Quaternion(1, 0, 0, 0))
        t = FrameTransform("world", "base", Translation(0, 0, 0), Quaternion(1, 0, 0, 0))
        with self.assertRaises(ContractError) as cm:
            FrameGraph((t, FrameTransform("world", "base", Translation(1, 0, 0), Quaternion(1, 0, 0, 0))))
        self.assertEqual(cm.exception.code, "FG_DUPLICATE_EDGE")
        self.assertEqual(FrameGraph([t]).transforms, (t,))

    def test_non_conformant_is_never_represented_and_version_fails_early(self):
        with self.assertRaises(FrameGraphContractError) as cm:
            parse_frame_graph(graph(edge("a", "b"), edge("b", "a")))
        self.assertEqual(cm.exception.code, "FG_CYCLE")
        for bad in ("0.2.0", "", "0.1", "1.0.0", "0.1.0 "):
            with self.subTest(bad=bad):
                doc = graph(edge("world", "base"))
                doc["contract_version"] = bad
                with self.assertRaises(UnsupportedFrameGraphVersion) as cm:
                    parse_frame_graph(doc)
                self.assertEqual(cm.exception.code, "FG_UNSUPPORTED_VERSION")
                self.assertEqual(len(cm.exception.violations), 1)
        doc = graph(edge("world", "base"))
        doc["contract_version"] = 1
        with self.assertRaises(FrameGraphContractError) as cm:
            parse_frame_graph(doc)
        self.assertNotIsInstance(cm.exception, UnsupportedFrameGraphVersion)

    def test_resolved_transform_roundtrip(self):
        r = resolve(graph(edge("world", "base", (1, 0, 0))), "base", "world").transform
        self.assertIsInstance(r, ResolvedTransform)
        d = r.to_dict()
        self.assertEqual(sorted(d), ["rotation", "translation", "translation_unit"])
        self.assertEqual(transform_point(d, (0, 0, 0)), (1.0, 0.0, 0.0))


class HygieneTest(unittest.TestCase):
    def test_no_oracle_or_third_party_import(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import kritva_sdk, kritva_sdk.frame_graph; "
                "names = ('kritva_sense', 'jsonschema', 'numpy', 'rclpy', 'requests', 'httpx', 'urllib3', 'socket', "
                "'ssl'); bad = [n for n in names if n in sys.modules]; print(','.join(bad)); "
                "sys.exit(1 if bad else 0)")
        done = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT / "src")], capture_output=True, text=True,
                              check=False)
        self.assertEqual(done.returncode, 0, f"library imported a forbidden module: {done.stdout.strip()} {done.stderr[-300:]}")

    def test_exports_exist(self):
        for name in fg.__all__:
            self.assertTrue(hasattr(fg, name), name)


if __name__ == "__main__":
    unittest.main()
