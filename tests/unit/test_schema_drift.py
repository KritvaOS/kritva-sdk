"""Unit tests for the vendored Sense contract files and the drift checker (KOS-SDK-003 AC-004). Stdlib only."""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
_spec = importlib.util.spec_from_file_location("check_schema_drift", ROOT / "scripts" / "check_schema_drift.py")
drift = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(drift)

VENDOR = ROOT / "src" / "kritva_sdk" / "_schemas" / "sense"
PINNED_COMMIT = "543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77"


def copy_vendor(dst):
    shutil.copytree(VENDOR, dst)
    return Path(dst)


ALL_VENDORED = ("sense-sample.schema.json", "SENSE_CONTRACT.md", "stream.schema.json", "STREAM_CONTRACT.md",
                "frame-transform.schema.json", "FRAME_GRAPH_CONTRACT.md")


class VendoredFilesTest(unittest.TestCase):
    def test_offline_check_is_clean_on_the_repository(self):
        problems, prov = drift.check_offline(VENDOR)
        self.assertEqual(problems, [])
        self.assertIsNotNone(prov)

    def test_provenance_records_the_approved_pin(self):
        prov = json.loads((VENDOR / "PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual({e["file"] for e in prov["files"]}, set(ALL_VENDORED))
        for e in prov["files"]:
            self.assertEqual(e["upstream_repo"], "KritvaOS/kritva-sense")
            self.assertEqual(e["contract_version"], "0.1.0")
            self.assertEqual(e["tag"], "v0.2.0")
            self.assertEqual(e["commit"], PINNED_COMMIT)
            self.assertIn("APPROVED", e["approval_status"])
            self.assertTrue(e["decision_ref"].startswith("D-"))

    def test_stream_and_frame_graph_contracts_are_pinned_at_the_same_commit(self):
        prov = json.loads((VENDOR / "PROVENANCE.json").read_text(encoding="utf-8"))
        by_contract = {}
        for e in prov["files"]:
            by_contract.setdefault(e["contract"], []).append(e)
        self.assertEqual(set(by_contract), {"sense", "stream", "frame_graph"})
        for name, decision in (("stream", "D-088"), ("frame_graph", "D-085")):
            self.assertEqual(len(by_contract[name]), 2)
            for e in by_contract[name]:
                self.assertEqual(e["decision_ref"], decision)
                self.assertIn("0.x contract", e["approval_status"])
        schema = json.loads((VENDOR / "stream.schema.json").read_text(encoding="utf-8"))
        self.assertIn("0.1.0", json.dumps(schema))
        schema = json.loads((VENDOR / "frame-transform.schema.json").read_text(encoding="utf-8"))
        self.assertIn("translation_unit", json.dumps(schema))

    def test_package_resources_are_readable_and_match_provenance(self):
        d = files("kritva_sdk") / "_schemas" / "sense"
        prov = json.loads((d / "PROVENANCE.json").read_text(encoding="utf-8"))
        for e in prov["files"]:
            self.assertEqual(hashlib.sha256((d / e["file"]).read_bytes()).hexdigest(), e["sha256"])

    def test_vendored_schema_declares_contract_0_1_0(self):
        schema = json.loads((VENDOR / "sense-sample.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["contract_version"]["enum"], ["0.1.0"])


class OfflineDriftTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.v = copy_vendor(Path(self.tmp.name) / "v")

    def test_hand_edit_fails(self):
        p = self.v / "sense-sample.schema.json"
        p.write_bytes(p.read_bytes() + b" ")
        problems, _ = drift.check_offline(self.v)
        self.assertTrue(any("DRIFT" in x for x in problems), problems)

    def test_missing_file_fails(self):
        (self.v / "SENSE_CONTRACT.md").unlink()
        problems, _ = drift.check_offline(self.v)
        self.assertTrue(any("missing" in x for x in problems), problems)

    def test_unlisted_file_fails(self):
        (self.v / "extra.json").write_text("{}")
        problems, _ = drift.check_offline(self.v)
        self.assertTrue(any("no provenance entry" in x for x in problems), problems)

    def test_incomplete_provenance_fails(self):
        prov = json.loads((self.v / "PROVENANCE.json").read_text())
        del prov["files"][0]["approval_status"]
        prov["files"][1]["commit"] = "main"
        (self.v / "PROVENANCE.json").write_text(json.dumps(prov))
        problems, _ = drift.check_offline(self.v)
        self.assertTrue(any("approval_status" in x for x in problems), problems)
        self.assertTrue(any("40-hex" in x for x in problems), problems)

    def test_missing_provenance_fails(self):
        (self.v / "PROVENANCE.json").unlink()
        problems, prov = drift.check_offline(self.v)
        self.assertTrue(problems)
        self.assertIsNone(prov)

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_schema_drift.py")], capture_output=True)
        self.assertEqual(ok.returncode, 0)
        (self.v / "SENSE_CONTRACT.md").write_bytes(b"changed")
        bad = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_schema_drift.py"), "--vendor-dir", str(self.v)],
                             capture_output=True)
        self.assertEqual(bad.returncode, 1)
        usage = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_schema_drift.py"), "--nope"], capture_output=True)
        self.assertEqual(usage.returncode, 2)


@unittest.skipUnless(shutil.which("git"), "git not available")
class UpstreamDriftTest(unittest.TestCase):
    """Builds a throwaway upstream repository so the check needs no network."""

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.up), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                               "-c", "commit.gpgsign=false", *a], check=True, capture_output=True, text=True).stdout.strip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = Path(self.tmp.name)
        self.up = t / "up"
        (self.up / "contract").mkdir(parents=True)
        self.git("init", "-q")
        for n in ALL_VENDORED:
            shutil.copy(VENDOR / n, self.up / "contract" / n)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "pin")
        self.commit = self.git("rev-parse", "HEAD")
        self.v = copy_vendor(t / "v")
        prov = json.loads((self.v / "PROVENANCE.json").read_text())
        for e in prov["files"]:
            e["commit"] = self.commit
        (self.v / "PROVENANCE.json").write_text(json.dumps(prov))

    def run_check(self):
        problems, prov = drift.check_offline(self.v)
        self.assertEqual(problems, [])
        return drift.check_upstream(self.v, prov, self.up)

    def test_clean_when_head_is_the_recorded_commit(self):
        self.assertEqual(self.run_check(), [])

    def test_wrong_head_fails_even_if_content_matches(self):
        (self.up / "other.txt").write_text("x")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "later")
        self.assertTrue(any("not the recorded commit" in x for x in self.run_check()))

    def test_upstream_content_change_at_recorded_commit_is_reported(self):
        prov = json.loads((self.v / "PROVENANCE.json").read_text())
        prov["files"][0]["sha256"] = "0" * 64
        (self.v / "PROVENANCE.json").write_text(json.dumps(prov))
        _, p = drift.check_offline(self.v)
        self.assertTrue(any("DRIFT" in x for x in drift.check_upstream(self.v, p, self.up)))

    def test_not_a_checkout(self):
        _, prov = drift.check_offline(self.v)
        out = drift.check_upstream(self.v, prov, Path(self.tmp.name) / "nowhere")
        self.assertTrue(out)


if __name__ == "__main__":
    unittest.main()
