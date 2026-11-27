"""Tests of the gate scripts themselves: lint, regression, acceptance, integration (make lint and friends).

A gate that cannot fail is not a gate. These tests prove each gate rejects the defects it exists to catch.
"""
import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lint = load("lint")
regression_gate = load("regression_gate")
acceptance_gate = load("acceptance_gate")
integration_gate = load("integration_gate")


def quiet(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*a)
    return code, buf.getvalue()


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()

    def codes(self, rel, text):
        path = self.root / rel
        path.write_text(text, encoding="utf-8")
        return sorted(c for _, c, _ in lint.check_file(path, self.root))

    def test_clean_file_has_no_findings(self):
        self.assertEqual(self.codes("src/a.py", "import os\n\nprint_ = os.sep\n"), [])

    def test_each_rule_fires(self):
        self.assertEqual(self.codes("tests/a.py", "def f(:\n"), ["L001"])
        self.assertEqual(self.codes("tests/a.py", "import os\n"), ["L002"])
        self.assertEqual(self.codes("tests/a.py", "from os import *\n"), ["L003"])
        self.assertIn("L004", self.codes("tests/a.py", "try:\n    pass\nexcept:\n    pass\n"))
        self.assertEqual(self.codes("tests/a.py", "def f(x=[]):\n    return x\n"), ["L005"])
        self.assertEqual(self.codes("tests/a.py", "x = 1 \n"), ["L006"])
        self.assertEqual(self.codes("tests/a.py", "x = 1"), ["L007"])
        self.assertEqual(self.codes("src/a.py", "print('x')\n"), ["L008"])
        self.assertEqual(self.codes("tests/a.py", "print('x')\n"), [])

    def test_library_may_not_import_forbidden_modules(self):
        for mod in ("requests", "socket", "jsonschema", "kritva_sense", "rclpy", "urllib.request"):
            self.assertIn("L009", self.codes("src/a.py", f"import {mod}\nx = {mod.split('.')[0]}\n"), mod)
        self.assertNotIn("L009", self.codes("tests/a.py", "import socket\nx = socket\n"))

    def test_noqa_and_exports_and_future_are_respected(self):
        self.assertEqual(self.codes("tests/a.py", "import os  # noqa\n"), [])
        self.assertEqual(self.codes("src/a.py", "from __future__ import annotations\nimport os\n__all__ = ['os']\n"), [])

    def test_repository_is_clean(self):
        code, out = quiet(lint.main, [])
        self.assertEqual(code, 0, out)

    def test_missing_path_is_a_usage_error(self):
        self.assertEqual(quiet(lint.main, ["no/such/path"])[0], 2)


class RegressionGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.golden = Path(self.tmp.name) / "golden"
        shutil.copytree(regression_gate.GOLDEN, self.golden)
        self.orig = regression_gate.GOLDEN
        regression_gate.GOLDEN = self.golden
        self.addCleanup(setattr, regression_gate, "GOLDEN", self.orig)

    def test_passes_on_current_behaviour(self):
        code, out = quiet(regression_gate.main, [])
        self.assertEqual(code, 0, out)
        self.assertIn("7 cases, 0 failure", out)

    def test_a_changed_golden_file_fails(self):
        p = self.golden / "supported_contracts.json"
        p.write_text(json.dumps({"sense": ["0.1.0", "0.2.0"]}, indent=2, sort_keys=True) + "\n")
        code, out = quiet(regression_gate.main, [])
        self.assertEqual(code, 1)
        self.assertIn("REG-02 FAIL", out)

    def test_a_missing_golden_file_fails(self):
        (self.golden / "config.json").unlink()
        code, out = quiet(regression_gate.main, [])
        self.assertEqual(code, 1)
        self.assertIn("no golden data", out)

    def test_zero_cases_is_not_a_pass(self):
        saved = dict(regression_gate.CASES)
        regression_gate.CASES.clear()
        try:
            code, _ = quiet(regression_gate.main, [])
        finally:
            regression_gate.CASES.update(saved)
        self.assertEqual(code, 1)

    def test_every_case_is_in_the_inventory(self):
        text = (ROOT / "tests" / "regression" / "REGRESSION_INVENTORY.md").read_text(encoding="utf-8")
        for cid in regression_gate.CASES:
            self.assertIn(cid, text)

    def test_usage_error(self):
        self.assertEqual(quiet(regression_gate.main, ["--bogus"])[0], 2)


class AcceptanceGateTest(unittest.TestCase):
    def test_every_criterion_is_classified(self):
        ids = acceptance_gate.criteria_ids()
        self.assertEqual(len(ids), 27)
        mapping = json.loads(acceptance_gate.MAP.read_text(encoding="utf-8"))
        mapping.pop("_note")
        self.assertEqual(sorted(ids), sorted(mapping))

    def test_unmapped_and_stale_entries_fail(self):
        mapping = json.loads(acceptance_gate.MAP.read_text(encoding="utf-8"))
        del mapping["KOS-SDK-003/AC-001"]
        mapping["KOS-SDK-009/AC-001"] = {"mode": "MANUAL", "evidence": "x"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.json"
            path.write_text(json.dumps(mapping))
            orig = acceptance_gate.MAP
            acceptance_gate.MAP = path
            try:
                code, out = quiet(acceptance_gate.main, [])
            finally:
                acceptance_gate.MAP = orig
        self.assertEqual(code, 1)
        self.assertIn("not in ACCEPTANCE_MAP.json", out)
        self.assertIn("stale", out)

    def test_automated_entry_without_tests_fails(self):
        mapping = json.loads(acceptance_gate.MAP.read_text(encoding="utf-8"))
        mapping["KOS-SDK-003/AC-001"] = {"mode": "AUTOMATED", "tests": ["tests/unit::test_config_errors_compat.NoSuchClass"]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.json"
            path.write_text(json.dumps(mapping))
            orig = acceptance_gate.MAP
            acceptance_gate.MAP = path
            try:
                code, out = quiet(acceptance_gate.main, [])
            finally:
                acceptance_gate.MAP = orig
        self.assertEqual(code, 1)
        self.assertIn("KOS-SDK-003/AC-001 FAIL", out)

    def test_manual_criteria_are_never_reported_as_passed(self):
        code, out = quiet(acceptance_gate.main, [])
        self.assertIn("KOS-SDK-001/AC-012 MANUAL", out)
        self.assertNotIn("KOS-SDK-001/AC-012 PASS", out)

    def test_usage_error(self):
        self.assertEqual(quiet(acceptance_gate.main, ["--bogus"])[0], 2)


class IntegrationGateTest(unittest.TestCase):
    def test_partial_run_is_incomplete_not_a_pass(self):
        code, out = quiet(integration_gate.main, [])
        self.assertEqual(code, 4, out)
        for sid in ("INT-01", "INT-02", "INT-03", "INT-04"):
            self.assertIn(f"{sid} PASS", out)
        for sid in ("INT-05", "INT-06", "INT-07"):
            self.assertIn(f"{sid} SKIP", out)

    def test_a_failing_scenario_fails_the_gate(self):
        saved = integration_gate.SCENARIOS
        def boom():
            raise AssertionError("boom")
        integration_gate.SCENARIOS = (("INT-99", boom, False),)
        try:
            code, out = quiet(integration_gate.main, [])
        finally:
            integration_gate.SCENARIOS = saved
        self.assertEqual(code, 1)
        self.assertIn("INT-99 FAIL boom", out)

    def test_a_crashing_scenario_is_a_failure_not_a_skip(self):
        saved = integration_gate.SCENARIOS
        def crash():
            raise KeyError("x")
        integration_gate.SCENARIOS = (("INT-98", crash, False),)
        try:
            code, out = quiet(integration_gate.main, [])
        finally:
            integration_gate.SCENARIOS = saved
        self.assertEqual(code, 1)
        self.assertIn("INT-98 FAIL KeyError", out)

    def test_usage_error(self):
        self.assertEqual(quiet(integration_gate.main, ["--bogus"])[0], 2)


if __name__ == "__main__":
    unittest.main()
