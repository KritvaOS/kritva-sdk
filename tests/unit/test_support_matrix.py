"""The support matrix in API.md agrees with what the SDK declares (KOS-SDK-005 AC-006 and AC-014). Standard library only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kritva_sdk import supported_contracts  # noqa: E402

CONTRACT_ROWS = {"Sense sample": "sense", "Sense stream": "stream", "Sense frame graph": "frame_graph"}


def matrix_rows():
    text = (ROOT / "API.md").read_text(encoding="utf-8")
    section = text.split("### Support matrix", 1)[1].split("\n## ", 1)[0].split("\nModels are hand-written", 1)[0]
    rows = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and not cells[0].startswith(("Contract", "---")):
            rows[cells[0]] = cells
    return rows


class SupportMatrixTest(unittest.TestCase):
    def test_every_declared_contract_is_listed_as_implemented_with_its_version(self):
        rows = matrix_rows()
        declared = supported_contracts()
        for label, key in CONTRACT_ROWS.items():
            with self.subTest(contract=label):
                self.assertIn(label, rows)
                self.assertIn(key, declared)
                self.assertEqual(rows[label][1], declared[key][0])
                self.assertTrue(rows[label][2].startswith("implemented"), rows[label])
                self.assertRegex(rows[label][3], r"^`kritva_sdk\.[a-z_]+`$")

    def test_nothing_is_declared_that_the_matrix_does_not_list_and_the_reverse(self):
        rows = matrix_rows()
        implemented = {k for k, c in rows.items() if c[2].startswith("implemented")}
        self.assertEqual(implemented, set(CONTRACT_ROWS))
        self.assertEqual(set(supported_contracts()), set(CONTRACT_ROWS.values()))

    def test_unsupported_versions_are_stated_and_never_silent(self):
        rows = matrix_rows()
        other = next(c for k, c in rows.items() if k.startswith("Any other"))
        self.assertIn("unsupported", other[2])
        self.assertIn("never accepted silently", other[2])

    def test_non_goals_are_stated(self):
        text = (ROOT / "API.md").read_text(encoding="utf-8")
        for needle in ("freshness", "calibration", "clock synchronisation", "physical correctness", "safety",
                       "no transport"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
