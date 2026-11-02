"""Source-backed visualization and Power BI theme sanity checks."""
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


class BiAssetTests(unittest.TestCase):
    def test_dashboard_preview_is_parseable_and_discloses_scope(self):
        preview = (ROOT / "assets" / "dashboard-preview.svg").read_text(encoding="utf-8")
        root = ElementTree.fromstring(preview)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("SYNTHETIC DATA ONLY", preview)
        self.assertIn("not an exported or validated Power BI screenshot", preview)
        report = json.loads((ROOT / "docs" / "bi_reference.json").read_text(encoding="utf-8"))
        for value in (f'{report["total_lines"]:,}', f'{report["flagged_lines"]:,}',
                      f'{report["flagged_rate_pct"]:.2f}%'):
            self.assertIn(value, preview)
        for group in report["by_specialty"]:
            self.assertIn(group["specialty"], preview)
            self.assertIn(f'{group["flagged_rate_pct"]:.2f}%', preview)

    def test_theme_is_valid_minimal_powerbi_json(self):
        theme = json.loads((ROOT / "powerBI" / "pharmacy-audit-theme.json").read_text(encoding="utf-8"))
        self.assertIsInstance(theme["name"], str)
        self.assertGreaterEqual(len(theme["dataColors"]), 3)
        for color in theme["dataColors"] + [theme["background"], theme["foreground"], theme["tableAccent"]]:
            self.assertRegex(color, r"^#[0-9A-Fa-f]{6}$")


if __name__ == "__main__":
    unittest.main()
