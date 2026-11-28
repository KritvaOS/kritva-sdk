"""Cross-validation of kritva_sdk.stream against the pinned kritva-sense reference checker (KOS-SDK-005).

kritva-sense is a TEST-ONLY ORACLE here, exactly as in test_sense_oracle.py: a checkout at the commit recorded in the
vendored provenance, named by KRITVA_SENSE_ORACLE, with KRITVA_REQUIRE_ORACLE=1 turning an unavailable oracle into a
failure. Parity is exact: position, code, path and message of every stream diagnostic and sample violation. The
random cases use a fixed seed, and a failure prints the case. Standard library only.
"""
import copy
import itertools
import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kritva_sdk.stream as sdk  # noqa: E402
from test_sense_oracle import ORACLE  # noqa: E402

DATA = ROOT / "tests" / "data" / "stream"


def fixtures():
    return [(p.relative_to(DATA).as_posix(), json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(DATA.glob("*/*.json"))]


def want(result):
    return ([tuple(d) for d in result.stream], [tuple(v) for v in result.samples])


@unittest.skipIf(ORACLE is None, "oracle not available (see test_sense_oracle.OracleAvailability)")
class StreamOracleParity(unittest.TestCase):
    def assert_same(self, doc, tag=""):
        expected = want(ORACLE["stream"].check_stream(doc))
        self.assertEqual(sdk.check_stream(doc).as_tuples(), (tuple(expected[0]), tuple(expected[1])),
                         f"{tag}: {json.dumps(doc, default=str)[:600]}")

    def test_contract_constants_agree(self):
        S = ORACLE["stream"]
        self.assertEqual(sdk.STREAM_CONTRACT_VERSION, S.STREAM_VERSION)
        self.assertEqual(sdk.STREAM_ERROR_CODES, tuple(S.STREAM_ERROR_CODES))
        self.assertEqual(sdk.RECORD_KINDS, tuple(S.RECORD_KINDS))
        self.assertEqual({k: (tuple(a), tuple(b)) for k, (a, b) in sdk._RECORD_FIELDS.items()},
                         {k: (tuple(a), tuple(b)) for k, (a, b) in S.RECORD_FIELDS.items()})
        self.assertEqual(sdk._DOCUMENT_FIELDS, tuple(S.DOCUMENT_FIELDS))
        self.assertEqual(sdk._SENSOR_ID_RE.pattern, S.STREAM_ID_RE.pattern)

    def test_fixture_parity(self):
        items = fixtures()
        self.assertGreaterEqual(len(items), 58)
        for name, doc in items:
            self.assert_same(doc, name)

    def test_conformance_harness_stream_cases(self):
        n = 0
        for case in ORACLE["conformance"].build_cases():
            if case["operation"] != "stream":
                continue
            self.assert_same(case["input"], case["id"])
            r = sdk.check_stream(case["input"])
            self.assertEqual(r.conformant, case["expected"]["conformant"], case["id"])
            self.assertEqual([[d.position, d.code] for d in r.stream], case["expected"]["stream"], case["id"])
            self.assertEqual([[v.position, v.code] for v in r.samples], case["expected"]["samples"], case["id"])
            n += 1
        self.assertGreaterEqual(n, 25)

    def test_batch_split_invariance_against_the_oracle(self):
        S = ORACLE["stream"]
        tested = 0
        for name, doc in fixtures():
            recs = doc.get("records") if isinstance(doc, dict) else None
            if not isinstance(recs, list) or len(recs) > 8:
                continue
            if doc.get("stream_version") != "0.1.0" or set(doc) != {"stream_version", "records"}:
                continue            # document-level diagnostics are not part of the incremental record checker
            whole = sdk.check_stream(doc).as_tuples()
            n = len(recs)
            for k in range(0, n):
                for cuts in itertools.combinations(range(0, n + 1), k):
                    bounds = [0, *cuts, n]
                    mine, theirs = sdk.StreamChecker(), S.StreamChecker()
                    for a, b in zip(bounds, bounds[1:]):
                        mine.feed(recs[a:b])
                        theirs.feed(recs[a:b])
                    mine.finish()
                    theirs.finish()
                    self.assertEqual(mine.result().as_tuples(), whole, f"{name} {cuts}")
                    got = want(theirs.result())
                    self.assertEqual(mine.result().as_tuples(), (tuple(got[0]), tuple(got[1])), f"{name} {cuts}")
                    tested += 1
        self.assertGreater(tested, 200)

    def test_seeded_mutations(self):
        bases = [doc for name, doc in fixtures() if name.startswith("valid/")]
        junk = [None, True, False, 0, -1, 1, 2, 1.5, float("nan"), "", "x", "open", "sample", "close", "imu",
                "range", "monotonic", "utc", "0.1.0", "imu.main", [], {}, [1], {"a": 1}, 10 ** 30]
        rng = random.Random(20261127)

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
                elif r < .5 and isinstance(cur, list) and len(cur) > 1:
                    j = rng.randrange(len(cur))
                    cur[p[-1]], cur[j] = cur[j], cur[p[-1]]
                elif r < .6 and isinstance(cur, dict):
                    cur[rng.choice(["extra", "index", "record", "first_sequence", "last_sequence"])] = \
                        copy.deepcopy(rng.choice(junk))
                else:
                    cur[p[-1]] = copy.deepcopy(rng.choice(junk))
            self.assert_same(d, f"mutation {i}")


if __name__ == "__main__":
    unittest.main()
