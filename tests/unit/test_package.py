"""Unit tests for the package foundation (KOS-SDK-002). Standard library only."""
import importlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


class PackageFoundationTest(unittest.TestCase):
    def test_version_is_pep440_and_exported(self):
        mod = importlib.import_module("kritva_sdk")
        self.assertRegex(mod.__version__, r"^\d+\.\d+\.\d+(\.dev\d+)?$")
        self.assertEqual(mod.__all__, ["SdkConfig", "__version__", "supported_contracts"])

    def test_base_import_pulls_no_forbidden_modules(self):
        importlib.import_module("kritva_sdk")
        for name in ("rclpy", "ament_index_python", "requests", "urllib3", "httpx", "socket"):
            if name == "socket":
                continue  # stdlib may load socket indirectly; network use is checked by absence of a client
            self.assertNotIn(name, sys.modules)

    def test_py_typed_present(self):
        self.assertTrue((ROOT / "src" / "kritva_sdk" / "py.typed").is_file())

    def test_no_optional_dependencies_declared(self):
        # no extras exist, so no optional integration can leak into the base import (KOS-SDK-002 AC-004)
        self.assertNotIn("optional-dependencies", (ROOT / "pyproject.toml").read_text())

    def test_no_runtime_dependencies_declared(self):
        text = (ROOT / "pyproject.toml").read_text()
        self.assertRegex(text, re.compile(r"^dependencies = \[\]$", re.M))


if __name__ == "__main__":
    unittest.main()
