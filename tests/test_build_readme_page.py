from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_readme_page.py"
SPEC = importlib.util.spec_from_file_location("build_readme_page", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

FIXED_AT = datetime(2026, 3, 15, 9, 0, tzinfo=UTC)
SAMPLE_MARKDOWN = """# Jane Doe

Applied machine learning researcher working on robust engineering systems.
Interested in reproducible workflows and deployment-minded experimentation.

## Focus
- Structural health monitoring
- Sensing pipelines

## Notes
This section includes a [portfolio](https://example.com/portfolio) link.

## Links
- GitHub: https://github.com/janedoe
- Email: jane@example.com
"""


class BuildReadmePageTests(unittest.TestCase):
    def test_parse_profile_extracts_title_intro_and_sections(self) -> None:
        profile = MODULE.parse_profile(SAMPLE_MARKDOWN)

        self.assertEqual(profile.title, "Jane Doe")
        self.assertEqual(len(profile.intro), 1)
        self.assertIn("deployment-minded experimentation", profile.intro[0])
        self.assertEqual([section.heading for section in profile.sections], ["Focus", "Notes", "Links"])
        self.assertEqual(profile.sections[0].blocks[0].items, ["Structural health monitoring", "Sensing pipelines"])

    def test_render_site_builds_static_html(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)

        self.assertIn("Jane Doe | Profile", output)
        self.assertIn("Structural health monitoring", output)
        self.assertIn("https://github.com/janedoe", output)
        self.assertIn("2026-03-15 09:00 UTC", output)
        self.assertNotIn("marked.min.js", output)
        self.assertNotIn("Loading profile", output)

    def test_build_writes_expected_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            readme_path = temp_root / "README.md"
            output_path = temp_root / "docs" / "index.html"
            readme_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")

            html = MODULE.build(
                readme_path=readme_path,
                output_path=output_path,
                generated_at=FIXED_AT,
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), html)
            self.assertIn("GitHub", html)


if __name__ == "__main__":
    unittest.main()
