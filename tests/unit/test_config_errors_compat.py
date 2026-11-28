"""Unit tests for errors, compat and config (KOS-SDK-003 AC-001..003, AC-006). Standard library only."""
import dataclasses
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kritva_sdk import SdkConfig, supported_contracts  # noqa: E402
from kritva_sdk.compat import require_supported  # noqa: E402
from kritva_sdk.errors import ContractError, SdkError, UnsupportedContractVersion, Violation  # noqa: E402


class CompatTest(unittest.TestCase):
    def test_supported_contracts_declaration(self):
        self.assertEqual(supported_contracts(), {"sense": ("0.1.0",), "stream": ("0.1.0",)})

    def test_declaration_is_not_mutable_through_result(self):
        supported_contracts()["sense"] = ("9.9.9",)
        supported_contracts().pop("sense")
        self.assertEqual(supported_contracts(), {"sense": ("0.1.0",), "stream": ("0.1.0",)})

    def test_supported_version_returned(self):
        self.assertEqual(require_supported("sense", "0.1.0"), "0.1.0")
        self.assertEqual(require_supported("stream", "0.1.0"), "0.1.0")

    def test_unsupported_version_fails_early_with_upstream_code(self):
        for bad in ("0.2.0", "", "0.1", "1.0.0", "0.1.0 "):
            with self.subTest(bad=bad):
                with self.assertRaises(UnsupportedContractVersion) as cm:
                    require_supported("sense", bad)
                self.assertEqual(cm.exception.code, "UNSUPPORTED_CONTRACT_VERSION")
                self.assertEqual(cm.exception.path, "contract_version")

    def test_wrong_type_is_malformed_field_not_unsupported(self):
        for bad in (None, 1, 0.1, True, ["0.1.0"], b"0.1.0"):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractError) as cm:
                    require_supported("sense", bad)
                self.assertEqual(cm.exception.code, "MALFORMED_FIELD")
                self.assertNotIsInstance(cm.exception, UnsupportedContractVersion)

    def test_unknown_contract_name_is_programming_error(self):
        with self.assertRaises(ValueError):
            require_supported("mind", "0.1.0")


class ErrorsTest(unittest.TestCase):
    def test_hierarchy(self):
        self.assertTrue(issubclass(ContractError, SdkError))
        self.assertTrue(issubclass(UnsupportedContractVersion, ContractError))
        self.assertTrue(issubclass(SdkError, Exception))

    def test_violation_tuple_shape_and_order(self):
        a = Violation(path="b", code="Z", message="m")
        b = Violation(path="a", code="Z", message="m")
        c = Violation(path="a", code="A", message="m")
        self.assertEqual(a.as_tuple(), ("Z", "b", "m"))
        err = ContractError([a, b, c])
        self.assertEqual(err.violations, (c, b, a))
        self.assertEqual((err.code, err.path, err.message), ("A", "a", "m"))

    def test_requires_a_violation(self):
        with self.assertRaises(ValueError):
            ContractError([])

    def test_violations_are_immutable(self):
        v = Violation(path="p", code="C", message="m")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            v.code = "X"  # type: ignore[misc]

    def test_message_names_rejected_version_only(self):
        with self.assertRaises(UnsupportedContractVersion) as cm:
            require_supported("sense", "7.7.7")
        self.assertIn("7.7.7", str(cm.exception))
        self.assertIn("0.1.0", str(cm.exception))


class ConfigTest(unittest.TestCase):
    def test_defaults_are_explicit_and_supported(self):
        self.assertEqual(SdkConfig().sense_contract_version, "0.1.0")

    def test_immutable(self):
        cfg = SdkConfig()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            cfg.sense_contract_version = "0.2.0"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            cfg.extra = 1  # type: ignore[attr-defined]

    def test_equal_and_hashable(self):
        self.assertEqual(SdkConfig(), SdkConfig("0.1.0"))
        self.assertEqual(len({SdkConfig(), SdkConfig("0.1.0")}), 1)

    def test_unsupported_version_rejected_at_construction(self):
        with self.assertRaises(UnsupportedContractVersion) as cm:
            SdkConfig(sense_contract_version="0.2.0")
        self.assertEqual(cm.exception.path, "sense_contract_version")

    def test_non_string_version_rejected(self):
        with self.assertRaises(ContractError) as cm:
            SdkConfig(sense_contract_version=1)  # type: ignore[arg-type]
        self.assertEqual(cm.exception.code, "MALFORMED_FIELD")

    def test_no_environment_or_global_state(self):
        import os
        old = os.environ.get("KRITVA_SENSE_CONTRACT_VERSION")
        os.environ["KRITVA_SENSE_CONTRACT_VERSION"] = "9.9.9"
        try:
            self.assertEqual(SdkConfig().sense_contract_version, "0.1.0")
        finally:
            if old is None:
                del os.environ["KRITVA_SENSE_CONTRACT_VERSION"]
            else:
                os.environ["KRITVA_SENSE_CONTRACT_VERSION"] = old

    def test_fields_are_only_the_documented_ones(self):
        self.assertEqual([f.name for f in dataclasses.fields(SdkConfig)], ["sense_contract_version"])


class BaseImportTest(unittest.TestCase):
    def test_new_modules_import_no_forbidden_modules(self):
        import importlib
        for m in ("kritva_sdk.errors", "kritva_sdk.compat", "kritva_sdk.config"):
            importlib.import_module(m)
        for name in ("rclpy", "ament_index_python", "requests", "urllib3", "httpx", "jsonschema", "kritva_sense"):
            self.assertNotIn(name, sys.modules)


if __name__ == "__main__":
    unittest.main()
