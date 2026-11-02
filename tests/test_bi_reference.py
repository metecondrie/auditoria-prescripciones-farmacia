"""Independent fixed-seed BI aggregate regression, no PostgreSQL required."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bi_reference", ROOT / "py" / "03_export_bi_reference.py"
)
REFERENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REFERENCE)


class BiReferenceTests(unittest.TestCase):
    def test_reference_export_matches_reviewed_fixture(self):
        versioned = json.loads((ROOT / "docs" / "bi_reference.json").read_text(encoding="utf-8"))
        computed = REFERENCE.build_reference()
        self.assertEqual(computed, versioned)
        self.assertEqual(computed["total_lines"], 100000)
        self.assertEqual(computed["flagged_lines"], 960)
        self.assertEqual(round(computed["flagged_rate_pct"], 2), 0.96)
        self.assertEqual(len(computed["by_month"]), 24)
        self.assertEqual(len(computed["by_specialty"]), 5)


if __name__ == "__main__":
    unittest.main()
