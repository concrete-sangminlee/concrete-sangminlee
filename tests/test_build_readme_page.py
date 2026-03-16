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

## Featured Work
1. [Impact report](https://example.com/impact)
2. Lightweight inspection workflow

## Notes
> Shipping simple, reproducible tools beats novelty without validation.

This section includes a [portfolio](https://example.com/portfolio) link and `code`.

## Links
- Profile site: https://example.com
- GitHub: https://github.com/janedoe
- Email: jane@example.com
"""

MINIMAL_MARKDOWN = """# Jane Doe

Applied machine learning researcher.

Infrastructure-focused machine learning.
"""


class BuildReadmePageTests(unittest.TestCase):
    def test_parse_profile_extracts_richer_blocks(self) -> None:
        profile = MODULE.parse_profile(SAMPLE_MARKDOWN)

        self.assertEqual(profile.title, "Jane Doe")
        self.assertEqual(len(profile.intro), 2)
        self.assertEqual([section.heading for section in profile.sections], ["Focus", "Featured Work", "Notes", "Links"])
        self.assertEqual(profile.sections[0].blocks[0].kind, "list")
        self.assertEqual(profile.sections[0].blocks[0].items, ["Structural health monitoring", "Sensing pipelines"])
        self.assertEqual(profile.sections[1].blocks[0].kind, "ordered_list")
        self.assertEqual(profile.sections[2].blocks[0].kind, "quote")
        self.assertEqual(profile.sections[2].blocks[1].kind, "paragraph")

    def test_render_site_builds_static_html_with_stronger_metadata(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)

        self.assertIn("Jane Doe | Research Profile", output)
        self.assertIn('content="summary_large_image"', output)
        self.assertIn('property="og:image"', output)
        self.assertIn("og-preview.svg", output)
        self.assertIn('"ProfilePage"', output)
        self.assertIn("preview-grid", output)
        self.assertIn("Focus Areas", output)
        self.assertIn("Featured Work", output)
        self.assertIn("2026-03-15 09:00 UTC", output)
        self.assertNotIn("marked.min.js", output)
        self.assertNotIn("Loading profile", output)

    def test_render_site_artifacts_include_auxiliary_outputs(self) -> None:
        artifacts = MODULE.render_site_artifacts(SAMPLE_MARKDOWN, generated_at=FIXED_AT)

        self.assertEqual(artifacts.canonical_url, "https://example.com")
        self.assertIn("<svg", artifacts.og_image)
        self.assertIn("Jane Doe profile preview", artifacts.og_image)
        self.assertIn("<image:image>", artifacts.sitemap)
        self.assertIn("og-preview.svg", artifacts.sitemap)
        self.assertIn("Sitemap: https://example.com/sitemap.xml", artifacts.robots)
        self.assertEqual(artifacts.nojekyll, "")

    def test_render_site_artifacts_are_deterministic_without_timestamp(self) -> None:
        artifacts = MODULE.render_site_artifacts(SAMPLE_MARKDOWN)

        self.assertIn("README snapshot", artifacts.html)
        self.assertNotIn("article:modified_time", artifacts.html)
        self.assertNotIn("<lastmod>", artifacts.sitemap)
        self.assertIn('"ProfilePage"', artifacts.html)

    def test_render_site_hides_empty_section_scaffolding_for_minimal_readme(self) -> None:
        output = MODULE.render_site(MINIMAL_MARKDOWN, generated_at=FIXED_AT)

        self.assertNotIn('<section class="preview-wrap">', output)
        self.assertNotIn('<div class="nav-wrap">', output)
        self.assertNotIn('<section class="content-grid">', output)
        self.assertIn("Jane Doe | Research Profile", output)

    def test_build_writes_expected_output_bundle(self) -> None:
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
            self.assertIn("Research Profile", html)
            self.assertTrue((output_path.parent / "og-preview.svg").exists())
            self.assertTrue((output_path.parent / "sitemap.xml").exists())
            self.assertTrue((output_path.parent / "robots.txt").exists())
            self.assertTrue((output_path.parent / ".nojekyll").exists())
            self.assertIn("README-DRIVEN PROFILE", (output_path.parent / "og-preview.svg").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
