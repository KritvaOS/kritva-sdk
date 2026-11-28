"""Unit tests for the stream 0.1.0 models and checker (KOS-SDK-005). Standard library only.

Cases are authored here from the prose contract (STREAM_CONTRACT.md) and checked against the upstream-authored
fixtures and expected diagnostics vendored under tests/data/stream. Parity with the pinned reference checker is
tests/conformance/test_stream_oracle.py.
"""
import copy
import dataclasses
import itertools
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import kritva_sdk.stream as stream  # noqa: E402
from kritva_sdk.compat import supported_contracts  # noqa: E402
from kritva_sdk.errors import ContractError, SdkError  # noqa: E402
from kritva_sdk.stream import (Stream, StreamChecker, StreamClose, StreamContractError, StreamOpen,  # noqa: E402
                               StreamResult, StreamSample, StreamUsageError, UnsupportedStreamVersion, check_stream,
                               parse_stream)

DATA = ROOT / "tests" / "data" / "stream"
EXPECTED = json.loads((DATA / "expected.json").read_text(encoding="utf-8"))


def fixtures(group):
    return [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((DATA / group).glob("*.json"))
            if p.name not in ("expected.json", "PROVENANCE.json")]


def sample(seq, ts=None, clock="monotonic", sensor="imu.main", kind="imu"):
    meas = {n: {"value": 0.5, "unit": u} for n, u in (("accel_x", "m/s^2"), ("accel_y", "m/s^2"), ("accel_z", "m/s^2"),
                                                      ("gyro_x", "rad/s"), ("gyro_y", "rad/s"), ("gyro_z", "rad/s"))}
    return {"contract_version": "0.1.0", "sensor_id": sensor, "kind": kind, "sequence": seq,
            "timestamp": {"clock": clock, "unit": "ns", "value": 1000 * seq if ts is None else ts},
            "frame_id": "sensor", "validity": "VALID", "measurements": meas}


def build(seqs, first="same", last="same", clock="monotonic"):
    """A conformant stream over the sequences ``seqs`` (increasing by one)."""
    recs = [{"record": "open", "index": 0, "stream_id": "stream_one", "sensor_id": "imu.main", "kind": "imu",
             "clock": clock}]
    if first is not None:
        recs[0]["first_sequence"] = seqs[0] if first == "same" else first
    for i, s in enumerate(seqs):
        recs.append({"record": "sample", "index": i + 1, "sample": sample(s, clock=clock)})
    close = {"record": "close", "index": len(seqs) + 1}
    if last is not None:
        close["last_sequence"] = seqs[-1] if last == "same" else last
    recs.append(close)
    return {"stream_version": "0.1.0", "records": recs}


def codes(doc):
    r = check_stream(doc)
    return [d.code for d in r.stream], [v.code for v in r.samples]


def reindex(doc):
    for i, r in enumerate(doc["records"]):
        if isinstance(r, dict):
            r["index"] = i
    return doc


class ConformantTest(unittest.TestCase):
    def test_worked_example_is_conformant(self):
        r = check_stream(build([100, 101, 102]))
        self.assertTrue(r.conformant)
        self.assertEqual((r.stream, r.samples), ((), ()))

    def test_minimal_stream_without_samples_and_bounds(self):
        doc = {"stream_version": "0.1.0", "records": [
            {"record": "open", "index": 0, "stream_id": "s", "sensor_id": "imu.main", "kind": "imu", "clock": "utc"},
            {"record": "close", "index": 1}]}
        self.assertTrue(check_stream(doc).conformant)

    def test_equal_timestamps_and_other_clock_start_are_fine(self):
        doc = build([5, 6, 7])
        for r in doc["records"][2:4]:
            r["sample"]["timestamp"]["value"] = 5000
        self.assertTrue(check_stream(doc).conformant)

    def test_contract_declared_and_codes_listed(self):
        self.assertEqual(supported_contracts()["stream"], ("0.1.0",))
        self.assertEqual(stream.STREAM_CONTRACT_VERSION, "0.1.0")
        self.assertEqual(len(stream.STREAM_ERROR_CODES), 23)
        self.assertEqual(len(set(stream.STREAM_ERROR_CODES)), 23)
        self.assertTrue(all(c.startswith("STREAM_") for c in stream.STREAM_ERROR_CODES))


class VendoredFixtureTest(unittest.TestCase):
    """Exact (position, code) expectations authored upstream; the SDK checker must reproduce them."""

    def test_every_fixture_has_an_expectation_and_vice_versa(self):
        names = {n for n, _ in fixtures("valid")} | {n for n, _ in fixtures("invalid")}
        self.assertEqual(names, set(EXPECTED) | {n for n, _ in fixtures("valid")})
        self.assertTrue(set(EXPECTED) <= names)

    def test_valid_fixtures_are_conformant(self):
        items = fixtures("valid")
        self.assertGreaterEqual(len(items), 10)
        for name, doc in items:
            with self.subTest(name=name):
                self.assertTrue(check_stream(doc).conformant, check_stream(doc))

    def test_invalid_fixtures_match_the_expected_diagnostics(self):
        items = fixtures("invalid")
        self.assertGreaterEqual(len(items), 48)
        for name, doc in items:
            with self.subTest(name=name):
                r = check_stream(doc)
                self.assertFalse(r.conformant)
                self.assertEqual(sorted([d.position, d.code] for d in r.stream), EXPECTED[name]["stream"])
                self.assertEqual(sorted([v.position, v.code] for v in r.samples), EXPECTED[name]["samples"])


class DocumentTest(unittest.TestCase):
    def test_document_level_defects(self):
        self.assertEqual(codes([]), (["STREAM_MALFORMED"], []))
        self.assertEqual(codes({"records": []}), (["STREAM_MISSING_FIELD", "STREAM_OPEN_MISSING"], []))
        self.assertEqual(codes({"stream_version": "0.1.0"}), (["STREAM_MISSING_FIELD"], []))
        self.assertEqual(codes({"stream_version": 1, "records": []})[0],
                         ["STREAM_MALFORMED", "STREAM_OPEN_MISSING"])
        self.assertEqual(codes({"stream_version": "0.2.0", "records": []})[0],
                         ["STREAM_OPEN_MISSING", "STREAM_UNSUPPORTED_VERSION"])
        doc = build([1])
        doc["extra"] = 1
        self.assertEqual(codes(doc)[0], ["STREAM_UNKNOWN_FIELD"])
        self.assertEqual(codes({"stream_version": "0.1.0", "records": {}}), (["STREAM_MALFORMED"], []))

    def test_empty_stream_is_not_conformant(self):
        r = check_stream({"stream_version": "0.1.0", "records": []})
        self.assertEqual([(d.position, d.code, d.path) for d in r.stream], [(-1, "STREAM_OPEN_MISSING", "records")])

    def test_check_stream_never_raises_and_leaves_input_untouched(self):
        doc = build([1, 2, 3])
        doc["records"][2]["sample"]["sequence"] = 9
        before = copy.deepcopy(doc)
        for bad in (None, 3, "x", [], {}, {"records": None}, {"stream_version": None, "records": [1, None, "x", []]}):
            check_stream(bad)
        check_stream(doc)
        self.assertEqual(doc, before)


class LifecycleTest(unittest.TestCase):
    def test_unterminated(self):
        doc = build([1, 2], last=None)
        doc["records"].pop()
        self.assertEqual(codes(doc)[0], ["STREAM_UNTERMINATED"])

    def test_close_before_open_and_open_not_first(self):
        doc = build([1])
        doc["records"].insert(0, {"record": "close", "index": 0})
        reindex(doc)
        self.assertEqual(sorted(codes(doc)[0]), ["STREAM_CLOSE_BEFORE_OPEN", "STREAM_OPEN_NOT_FIRST"])

    def test_repeats_and_after_close(self):
        doc = build([1])
        doc["records"] += [dict(doc["records"][0]), {"record": "close", "index": 0},
                           {"record": "sample", "index": 0, "sample": sample(2)}]
        reindex(doc)
        self.assertEqual(sorted(codes(doc)[0]),
                         ["STREAM_CLOSE_REPEATED", "STREAM_OPEN_REPEATED", "STREAM_SAMPLE_AFTER_CLOSE"])

    def test_sample_before_open_is_still_checked(self):
        doc = build([1])
        doc["records"].insert(0, {"record": "sample", "index": 0, "sample": sample(0)})
        reindex(doc)
        d, s = codes(doc)
        self.assertIn("STREAM_SAMPLE_BEFORE_OPEN", d)
        self.assertIn("STREAM_OPEN_NOT_FIRST", d)

    def test_open_only_has_two_defects_at_the_document(self):
        doc = {"stream_version": "0.1.0", "records": [
            {"record": "open", "index": 0, "stream_id": "s", "sensor_id": "imu.main", "kind": "imu",
             "clock": "monotonic", "first_sequence": 4}]}
        r = check_stream(doc)
        self.assertEqual([(d.position, d.code) for d in r.stream],
                         [(-1, "STREAM_FIRST_SEQUENCE_UNMET"), (-1, "STREAM_UNTERMINATED")])


class SequenceAndTimestampTest(unittest.TestCase):
    def test_gap_message_states_the_missing_range(self):
        doc = build([100, 102], first=None, last=None)
        r = check_stream(doc)
        self.assertEqual([d.code for d in r.stream], ["STREAM_SEQUENCE_GAP"])
        self.assertIn("sequence 101 to 101 missing", r.stream[0].message)
        self.assertEqual(r.stream[0].position, 2)
        self.assertEqual(r.stream[0].path, "records[2].sample.sequence")
        self.assertEqual(r.samples, ())

    def test_duplicate_regression_and_exclusivity(self):
        for seqs, code in (([1, 1], "STREAM_SEQUENCE_DUPLICATE"), ([5, 3], "STREAM_SEQUENCE_REGRESSION"),
                           ([1, 4], "STREAM_SEQUENCE_GAP")):
            with self.subTest(seqs=seqs):
                doc = build(seqs, first=None, last=None)
                for i, s in enumerate(seqs):
                    doc["records"][i + 1]["sample"]["sequence"] = s
                    doc["records"][i + 1]["sample"]["timestamp"]["value"] = 1000 * (i + 1)
                self.assertEqual(codes(doc)[0], [code])

    def test_bounds(self):
        self.assertEqual(codes(build([5, 6], first=4))[0], ["STREAM_FIRST_SEQUENCE_UNMET"])
        self.assertEqual(codes(build([5, 6], last=9))[0], ["STREAM_LAST_SEQUENCE_UNMET"])
        self.assertEqual(codes(build([5, 6], first=None, last=None))[0], [])

    def test_timestamp_regression_and_equal_is_fine(self):
        doc = build([1, 2, 3], first=None, last=None)
        doc["records"][3]["sample"]["timestamp"]["value"] = 10
        self.assertEqual(codes(doc)[0], ["STREAM_TIMESTAMP_REGRESSION"])

    def test_clock_mismatch_only_reports_once_and_skips_comparison(self):
        doc = build([1, 2, 3], first=None, last=None)
        doc["records"][2]["sample"]["timestamp"]["clock"] = "utc"
        doc["records"][2]["sample"]["timestamp"]["value"] = 1
        self.assertEqual(codes(doc)[0], ["STREAM_CLOCK_MISMATCH"])

    def test_identity_changes(self):
        doc = build([1, 2], first=None, last=None)
        doc["records"][2]["sample"]["sensor_id"] = "imu.other"
        self.assertEqual(codes(doc)[0], ["STREAM_SENSOR_CHANGE"])
        doc = build([1, 2], first=None, last=None)
        doc["records"][2]["sample"].update(kind="range", measurements={"distance": {"value": 1, "unit": "m"}})
        self.assertEqual(codes(doc)[0], ["STREAM_KIND_CHANGE"])

    def test_sample_violations_keep_the_unchanged_upstream_codes(self):
        doc = build([1, 2], first=None, last=None)
        doc["records"][2]["sample"]["measurements"]["accel_x"]["unit"] = "g"
        r = check_stream(doc)
        self.assertEqual(r.stream, ())
        self.assertEqual([(v.position, v.code) for v in r.samples], [(2, "INVALID_UNIT")])
        self.assertFalse(r.conformant)

    def test_non_object_sample_is_reported_in_both_lists(self):
        doc = build([1], first=None, last=None)
        doc["records"][1]["sample"] = 7
        d, s = codes(doc)
        self.assertEqual(d, ["STREAM_MALFORMED"])
        self.assertEqual(s, ["MALFORMED_FIELD"])


class RecordShapeTest(unittest.TestCase):
    def test_record_level_defects(self):
        doc = build([1], first=None, last=None)
        doc["records"][1] = 5
        self.assertEqual(codes(doc)[0], ["STREAM_MALFORMED"])
        doc = build([1], first=None, last=None)
        doc["records"][1]["record"] = "reading"
        self.assertEqual(codes(doc)[0], ["STREAM_UNKNOWN_RECORD"])
        doc = build([1], first=None, last=None)
        del doc["records"][1]["record"]
        self.assertEqual(codes(doc)[0], ["STREAM_MISSING_FIELD"])
        doc = build([1], first=None, last=None)
        doc["records"][1]["index"] = 4
        self.assertEqual(codes(doc)[0], ["STREAM_INDEX_MISMATCH"])
        for bad in (-1, "1", 1.0, True):
            doc = build([1], first=None, last=None)
            doc["records"][1]["index"] = bad
            self.assertEqual(codes(doc)[0], ["STREAM_MALFORMED"], bad)
        doc = build([1], first=None, last=None)
        doc["records"][0]["extra"] = 1
        self.assertEqual(codes(doc)[0], ["STREAM_UNKNOWN_FIELD"])

    def test_malformed_open_fields_are_reported_and_not_used(self):
        doc = build([1], first=None, last=None)
        doc["records"][0].update(stream_id="BAD", sensor_id="Bad", kind="lidar", clock="gps")
        self.assertEqual(codes(doc)[0], ["STREAM_MALFORMED"] * 4)
        self.assertEqual(codes(doc)[1], [])

    def test_bounds_must_be_non_negative_integers(self):
        for bad in (-1, 1.5, "1", True):
            doc = build([1])
            doc["records"][0]["first_sequence"] = bad
            doc["records"][2]["last_sequence"] = bad
            self.assertEqual(codes(doc)[0], ["STREAM_MALFORMED", "STREAM_MALFORMED"], bad)


class IncrementalTest(unittest.TestCase):
    def split_results(self, doc, cuts):
        c = StreamChecker()
        recs = doc["records"]
        bounds = [0, *cuts, len(recs)]
        for a, b in zip(bounds, bounds[1:]):
            c.feed(recs[a:b])
        c.finish()
        return c.result()

    def test_every_split_gives_the_same_result_as_the_whole(self):
        docs = [build([1, 2, 3]), build([1, 3, 3, 2]), reindex({"stream_version": "0.1.0", "records": [
            {"record": "sample", "index": 0, "sample": sample(4)}, {"record": "close", "index": 0},
            {"record": "open", "index": 0, "stream_id": "s", "sensor_id": "imu.main", "kind": "imu",
             "clock": "utc", "first_sequence": 9}]})]
        for doc in docs:
            whole = check_stream(doc)
            n = len(doc["records"])
            for k in range(0, n):
                for cuts in itertools.combinations(range(0, n + 1), k):
                    got = self.split_results(doc, list(cuts))
                    self.assertEqual(got.as_tuples(), whole.as_tuples(), cuts)

    def test_feed_and_finish_return_only_their_own_additions(self):
        c = StreamChecker()
        doc = build([1, 3], first=None, last=None)
        doc["records"].pop()
        first = c.feed(doc["records"][:2])
        second = c.feed(doc["records"][2:])
        end = c.finish()
        self.assertTrue(first.conformant)
        self.assertEqual([d.code for d in second.stream], ["STREAM_SEQUENCE_GAP"])
        self.assertEqual([d.code for d in end.stream], ["STREAM_UNTERMINATED"])
        self.assertEqual(len(c.result().stream), 2)

    def test_empty_batches_are_harmless(self):
        c = StreamChecker()
        self.assertTrue(c.feed([]).conformant)
        c.feed(build([1])["records"])
        c.feed(())
        self.assertTrue(c.finish().conformant)

    def test_misuse_is_a_typed_sdk_error_not_a_diagnostic(self):
        c = StreamChecker()
        for bad in ("abc", {"a": 1}, None, 5, iter([])):
            with self.assertRaises(StreamUsageError):
                c.feed(bad)
        self.assertEqual(c.result().stream, ())      # nothing was consumed
        c.finish()
        with self.assertRaises(StreamUsageError):
            c.feed([])
        with self.assertRaises(StreamUsageError):
            c.finish()
        self.assertTrue(c.finished)
        self.assertTrue(issubclass(StreamUsageError, SdkError))
        self.assertTrue(issubclass(StreamUsageError, ValueError))

    def test_results_are_sorted_and_deterministic_across_runs(self):
        doc = build([5, 3, 3, 9], first=1, last=2)
        doc["records"][2]["sample"]["sensor_id"] = "imu.other"
        a, b = check_stream(doc), check_stream(copy.deepcopy(doc))
        self.assertEqual(a, b)
        keys = [(d.position, d.code, d.path, d.message) for d in a.stream]
        self.assertEqual(keys, sorted(keys))

    def test_ten_thousand_record_stream_is_a_scale_test_only(self):
        doc = build(list(range(1, 10001)))
        self.assertTrue(check_stream(doc).conformant)


class ModelTest(unittest.TestCase):
    def test_parse_roundtrip_and_equality(self):
        doc = build([100, 101, 102])
        st = parse_stream(doc)
        self.assertIsInstance(st, Stream)
        self.assertEqual(st.to_dict(), doc)
        self.assertEqual(parse_stream(st.to_dict()), st)
        self.assertIsInstance(st.records[0], StreamOpen)
        self.assertIsInstance(st.records[1], StreamSample)
        self.assertIsInstance(st.records[-1], StreamClose)
        self.assertEqual(st.records[1].sample.sequence, 100)
        self.assertEqual(st.records[0].first_sequence, 100)
        self.assertEqual(st.records[-1].last_sequence, 102)

    def test_optional_fields_absent_stay_absent(self):
        doc = build([1], first=None, last=None)
        st = parse_stream(doc)
        self.assertIsNone(st.records[0].first_sequence)
        self.assertNotIn("first_sequence", st.records[0].to_dict())
        self.assertEqual(st.to_dict(), doc)

    def test_models_are_immutable(self):
        st = parse_stream(build([1]))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            st.stream_version = "9"          # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            st.records[0].index = 3          # type: ignore[misc]

    def test_non_conformant_is_never_represented(self):
        doc = build([1, 3])
        with self.assertRaises(StreamContractError) as cm:
            parse_stream(doc)
        self.assertIsInstance(cm.exception, ContractError)
        self.assertEqual(cm.exception.code, "STREAM_SEQUENCE_GAP")
        self.assertEqual(cm.exception.result, check_stream(doc))
        self.assertIn("STREAM_SEQUENCE_GAP", str(cm.exception))

    def test_sample_violations_are_mapped_under_the_record(self):
        doc = build([1])
        doc["records"][1]["sample"]["measurements"]["accel_x"]["unit"] = "g"
        with self.assertRaises(StreamContractError) as cm:
            parse_stream(doc)
        self.assertEqual(cm.exception.code, "INVALID_UNIT")
        self.assertTrue(cm.exception.path.startswith("records[1].sample"))

    def test_unsupported_version_fails_early_with_the_upstream_code(self):
        for bad in ("0.2.0", "", "0.1", "1.0.0", "0.1.0 "):
            with self.subTest(bad=bad):
                doc = build([1])
                doc["stream_version"] = bad
                with self.assertRaises(UnsupportedStreamVersion) as cm:
                    parse_stream(doc)
                self.assertEqual(cm.exception.code, "STREAM_UNSUPPORTED_VERSION")
                self.assertEqual(len(cm.exception.violations), 1)
        doc = build([1])
        doc["stream_version"] = 1
        with self.assertRaises(StreamContractError) as cm:
            parse_stream(doc)
        self.assertNotIsInstance(cm.exception, UnsupportedStreamVersion)
        self.assertEqual(cm.exception.code, "STREAM_MALFORMED")

    def test_models_can_be_fed_to_the_checker(self):
        st = parse_stream(build([1, 2, 3]))
        c = StreamChecker()
        self.assertTrue(c.feed(list(st.records)).conformant)
        self.assertTrue(c.finish().conformant)


class HygieneTest(unittest.TestCase):
    def test_no_oracle_or_third_party_import(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import kritva_sdk, kritva_sdk.stream; "
                "names = ('kritva_sense', 'jsonschema', 'rclpy', 'requests', 'httpx', 'urllib3', 'socket', 'ssl'); "
                "bad = [n for n in names if n in sys.modules]; print(','.join(bad)); sys.exit(1 if bad else 0)")
        done = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT / "src")], capture_output=True, text=True,
                              check=False)
        self.assertEqual(done.returncode, 0, f"library imported a forbidden module: {done.stdout.strip()} {done.stderr[-300:]}")

    def test_result_type_is_exported(self):
        self.assertIs(StreamResult, stream.StreamResult)
        for name in stream.__all__:
            self.assertTrue(hasattr(stream, name), name)


if __name__ == "__main__":
    unittest.main()
