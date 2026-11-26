"""Vendored upstream Sense fixtures against the SDK (KOS-SDK-003 AC-005). Offline, standard library only.

The fixtures are byte-exact copies authored upstream (tests/data/sense/PROVENANCE.json); they were not produced by
the SDK validator, so this test does not validate the SDK against its own assumptions.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kritva_sdk.errors import ContractError, UnsupportedContractVersion  # noqa: E402
from kritva_sdk.sense import ERROR_CODES, KINDS, parse_sample, validate_sample  # noqa: E402

DATA = ROOT / "tests" / "data" / "sense"


def load(group):
    return [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((DATA / group).glob("*.json"))]


class VendoredFixtures(unittest.TestCase):
    def test_fixture_sets_are_complete(self):
        valid, invalid = load("valid"), load("invalid")
        self.assertGreaterEqual(len(valid), 7)
        self.assertGreaterEqual(len(invalid), 20)
        self.assertEqual({d["sample"]["kind"] for _, d in valid}, set(KINDS))
        prov = json.loads((DATA / "PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(prov["files"]), len(valid) + len(invalid))

    def test_valid_fixtures_pass_and_round_trip(self):
        for name, doc in load("valid"):
            with self.subTest(name):
                self.assertEqual(validate_sample(doc["sample"]), ())
                self.assertEqual(parse_sample(doc["sample"]).to_dict(), doc["sample"])

    def test_invalid_fixtures_report_exactly_the_documented_codes(self):
        for name, doc in load("invalid"):
            with self.subTest(name):
                got = sorted({v.code for v in validate_sample(doc["sample"])})
                self.assertEqual(got, sorted(doc["expected_codes"]))
                self.assertTrue(set(got) <= set(ERROR_CODES))

    def test_parse_rejects_every_invalid_fixture(self):
        for name, doc in load("invalid"):
            with self.subTest(name):
                with self.assertRaises(ContractError) as cm:
                    parse_sample(doc["sample"])
                if "UNSUPPORTED_CONTRACT_VERSION" in doc["expected_codes"]:
                    self.assertIsInstance(cm.exception, UnsupportedContractVersion)
                else:
                    self.assertEqual(sorted({v.code for v in cm.exception.violations}), sorted(doc["expected_codes"]))

    def test_validity_states_are_conformant_not_readings(self):
        by = dict(load("valid"))
        for name, state in (("stale_declared", "STALE"), ("missing_declared", "MISSING"), ("invalid_declared", "INVALID")):
            s = parse_sample(by[name]["sample"])
            self.assertEqual(s.validity, state)
            self.assertIsNotNone(s.error_code)
        self.assertEqual(len(parse_sample(by["missing_declared"]["sample"]).measurements), 0)

    def test_results_are_deterministic(self):
        for _, doc in load("invalid"):
            self.assertEqual(validate_sample(doc["sample"]), validate_sample(json.loads(json.dumps(doc["sample"]))))


if __name__ == "__main__":
    unittest.main()
