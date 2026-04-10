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

MEDIA_MARKDOWN = """# Jane Doe

[![Profile Site](https://img.shields.io/badge/Profile_Site-0f766e?style=for-the-badge)](https://example.com)
[![GitHub Stats](https://github-readme-stats.vercel.app/api?username=janedoe)](https://github.com/janedoe)

Applied machine learning researcher.

## GitHub Activity
[![Streak Stats](https://streak-stats.demolab.com?user=janedoe)](https://git.io/streak-stats)
![Contribution Snake](https://raw.githubusercontent.com/janedoe/janedoe/output/github-snake.svg)
"""

MINIMAL_MARKDOWN = """# Jane Doe

Applied machine learning researcher.

Infrastructure-focused machine learning.
"""

HTML_BLOCK_MARKDOWN = """# Jane Doe

Applied machine learning researcher.

## Gallery

<picture>
<source media="(prefers-color-scheme: dark)" srcset="https://example.com/dark.svg" />
<source media="(prefers-color-scheme: light)" srcset="https://example.com/light.svg" />
<img alt="Visual" src="https://example.com/light.svg" width="100%" />
</picture>

## Publications

<details>
<summary><strong>Selected Papers</strong></summary>

- Paper one about structural monitoring.
- Paper two about wind engineering.

</details>
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
        self.assertIn("Research Themes", output)
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

        self.assertIn("Profile snapshot", artifacts.html)
        self.assertNotIn("article:modified_time", artifacts.html)
        self.assertNotIn("<lastmod>", artifacts.sitemap)
        self.assertIn('"ProfilePage"', artifacts.html)

    def test_render_site_hides_empty_section_scaffolding_for_minimal_readme(self) -> None:
        output = MODULE.render_site(MINIMAL_MARKDOWN, generated_at=FIXED_AT)

        self.assertNotIn('<section class="preview-wrap">', output)
        self.assertNotIn('<div class="nav-wrap">', output)
        self.assertNotIn('<section class="content-grid">', output)
        self.assertIn("Jane Doe | Research Profile", output)

    def test_render_site_supports_badges_and_images(self) -> None:
        output = MODULE.render_site(MEDIA_MARKDOWN, generated_at=FIXED_AT)

        self.assertIn("markdown-image-badge", output)
        self.assertIn("markdown-image-stats", output)
        self.assertIn("media-group-stats", output)
        self.assertIn("markdown-image-snake", output)
        self.assertNotIn("img.shields.io", MODULE.summarize_description(MODULE.parse_profile(MEDIA_MARKDOWN), []))

    def test_markdown_tables_render_as_html_tables(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Data

| Degree | Institution | Period |
|--------|------------|--------|
| Ph.D. in AI | SNU | 2023-2027 |
| M.S. | SNU | 2021-2023 |
"""
        profile = MODULE.parse_profile(md)
        data_section = next(s for s in profile.sections if s.heading == "Data")
        table_blocks = [b for b in data_section.blocks if b.kind == "html"]
        self.assertEqual(len(table_blocks), 1)
        self.assertIn('<div class="table-wrap"><table', table_blocks[0].items[0])
        self.assertIn('<th scope="col">Degree</th>', table_blocks[0].items[0])
        self.assertIn('<td scope="row">Ph.D. in AI</td>', table_blocks[0].items[0])
        self.assertNotIn("|-----", table_blocks[0].items[0])

    def test_html_blocks_pass_through_unchanged(self) -> None:
        profile = MODULE.parse_profile(HTML_BLOCK_MARKDOWN)

        gallery = next(s for s in profile.sections if s.heading == "Gallery")
        self.assertEqual(len(gallery.blocks), 1)
        self.assertEqual(gallery.blocks[0].kind, "html")
        self.assertIn("<picture>", gallery.blocks[0].items[0])
        self.assertIn("</picture>", gallery.blocks[0].items[0])

        pubs = next(s for s in profile.sections if s.heading == "Publications")
        html_blocks = [b for b in pubs.blocks if b.kind == "html"]
        list_blocks = [b for b in pubs.blocks if b.kind == "list"]
        self.assertTrue(any("<details>" in b.items[0] for b in html_blocks))
        self.assertTrue(any("</details>" in b.items[0] for b in html_blocks))
        self.assertEqual(len(list_blocks), 1)

        output = MODULE.render_site(HTML_BLOCK_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn("<picture>", output)
        self.assertIn("<details>", output)
        self.assertNotIn("&lt;picture&gt;", output)

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
            self.assertIn("ACADEMIC RESEARCH PROFILE", (output_path.parent / "og-preview.svg").read_text(encoding="utf-8"))


    def test_table_alignment_preserved(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Data

| Year | Publication |
|:----:|-------------|
| 2025 | Some paper |
"""
        profile = MODULE.parse_profile(md)
        data_section = next(s for s in profile.sections if s.heading == "Data")
        table_html = data_section.blocks[0].items[0]
        self.assertIn('style="text-align:center"', table_html)

    def test_dark_mode_support(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn("prefers-color-scheme: dark", output)
        self.assertIn("data-theme", output)
        self.assertIn("theme-toggle", output)
        self.assertIn("localStorage", output)

    def test_table_css_present(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn(".md-table", output)
        self.assertIn(".table-wrap", output)

    def test_print_styles(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn("@media print", output)

    def test_dns_prefetch(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn('rel="dns-prefetch"', output)
        self.assertIn("img.shields.io", output)

    def test_section_labels_meaningful(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Code
- [repo](https://github.com/example/repo): A tool

## Background

| Degree | Field | Institution | Period |
|--------|-------|-------------|--------|
| Ph.D. | AI | SNU | 2023-2027 |
"""
        profile = MODULE.parse_profile(md)
        code_section = next(s for s in profile.sections if s.heading == "Code")
        bg_section = next(s for s in profile.sections if s.heading == "Background")
        self.assertEqual(MODULE.section_label(5, code_section), "Open Source")
        self.assertEqual(MODULE.section_label(6, bg_section), "Background")

    def test_signal_grid_uses_focus_label(self) -> None:
        result = MODULE.render_signal_grid(["Item one", "Item two"])
        self.assertIn("Focus 01", result)
        self.assertIn("Focus 02", result)
        self.assertNotIn("Signal", result)

    def test_skip_link_present(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn('class="skip-link"', output)
        self.assertIn('href="#main-content"', output)
        self.assertIn('id="main-content"', output)

    def test_table_scope_attributes(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Data

| Year | Publication |
|------|-------------|
| 2025 | Some paper |
"""
        profile = MODULE.parse_profile(md)
        data_section = next(s for s in profile.sections if s.heading == "Data")
        table_html = data_section.blocks[0].items[0]
        self.assertIn('scope="col"', table_html)
        self.assertIn('scope="row"', table_html)

    def test_reduced_motion_support(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn("prefers-reduced-motion: reduce", output)

    def test_focus_visible_outline(self) -> None:
        output = MODULE.render_site(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        self.assertIn(":focus-visible", output)
        self.assertIn("outline:", output)

    def test_educational_credentials_in_schema(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Background

| Degree | Field | Institution | Period |
|--------|-------|-------------|--------|
| **Ph.D.** | Artificial Intelligence | Seoul National University | 2023-2027 |
| **M.S.** | Structural Engineering | Seoul National University | 2021-2023 |
"""
        output = MODULE.render_site(md, generated_at=FIXED_AT)
        self.assertIn('"EducationalOccupationalCredential"', output)
        self.assertIn('"alumniOf"', output)
        self.assertIn('"CollegeOrUniversity"', output)
        self.assertIn("Seoul National University", output)
        self.assertIn('"Doctorate"', output)
        self.assertIn('"Masters"', output)

    def test_publications_parsed_into_scholarly_articles(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Publications

### Journal Articles

| Year | Publication |
|:----:|-------------|
| 2025 | **J. Doe**, A. Smith. "Deep learning for structural monitoring." *J. Structural Engineering* 151(12). [[DOI](https://doi.org/10.1234/example)] |

### Selected Conference Papers

| Year | Publication |
|:----:|-------------|
| 2024 | **J. Doe**, B. Lee. "Wind pressure clustering." *EACWE 2024*. |
"""
        profile = MODULE.parse_profile(md)
        person_id = "https://example.com/#person"
        pubs = MODULE.extract_publications(profile, person_id)
        self.assertEqual(len(pubs), 2)

        journal = pubs[0]
        self.assertEqual(journal["@type"], "ScholarlyArticle")
        self.assertEqual(journal["name"], "Deep learning for structural monitoring")
        self.assertEqual(journal["datePublished"], "2025")
        self.assertEqual(journal["isPartOf"]["@type"], "Periodical")
        self.assertEqual(journal["isPartOf"]["name"], "J. Structural Engineering")
        self.assertEqual(journal["isPartOf"]["issueNumber"], "151(12)")
        self.assertEqual(journal["sameAs"], "https://doi.org/10.1234/example")
        self.assertEqual(journal["identifier"]["value"], "10.1234/example")
        self.assertEqual(journal["identifier"]["propertyID"], "DOI")

        conference = pubs[1]
        self.assertEqual(conference["isPartOf"]["@type"], "PublicationEvent")
        self.assertEqual(conference["isPartOf"]["name"], "EACWE 2024")
        self.assertNotIn("identifier", conference)

    def test_publication_authors_link_self_to_person(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Publications

| Year | Publication |
|:----:|-------------|
| 2025 | A. Smith, **J. Doe**, C. Lee. "Test paper." *Test Journal* 1(1). |
"""
        profile = MODULE.parse_profile(md)
        person_id = "https://example.com/#person"
        pubs = MODULE.extract_publications(profile, person_id)
        self.assertEqual(len(pubs), 1)
        authors = pubs[0]["author"]
        self.assertEqual(len(authors), 3)
        self.assertEqual(authors[0]["name"], "A. Smith")
        self.assertEqual(authors[1], {"@id": person_id})
        self.assertEqual(authors[2]["name"], "C. Lee")

    def test_publications_in_rendered_schema(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Publications

| Year | Publication |
|:----:|-------------|
| 2025 | **J. Doe**. "Sample title." *Sample Journal* 1(1). |
"""
        output = MODULE.render_site(md, generated_at=FIXED_AT)
        self.assertIn('"ScholarlyArticle"', output)
        self.assertIn("Sample title", output)
        self.assertIn("Sample Journal", output)

    def test_metric_cards_count_table_publications_and_intro_badges(self) -> None:
        md = """# Test Person

[![Site](https://shields.io/badge/site-x?style=for-the-badge)](https://example.com)
[![Scholar](https://shields.io/badge/scholar-x?style=for-the-badge)](https://scholar.google.com/x)
[![ORCID](https://shields.io/badge/orcid-x?style=for-the-badge)](https://orcid.org/x)

ML researcher.

## Focus
- Theme one
- Theme two

## Publications

| Year | Publication |
|------|-------------|
| 2025 | Paper one |
| 2024 | Paper two |
| 2023 | Paper three |

## Patents

![Granted](https://shields.io/badge/x-y) **Patent A** [[link](https://example.com/a)]

![Granted](https://shields.io/badge/x-y) **Patent B** [[link](https://example.com/b)]
"""
        profile = MODULE.parse_profile(md)
        links = MODULE.extract_links(profile)
        tags = MODULE.extract_tags(profile, limit=5)
        cards = MODULE.build_metric_cards(profile, links, tags)
        by_label = {c.label: c.value for c in cards}
        self.assertEqual(by_label["Selected Outputs"], "5")
        self.assertEqual(by_label["Public Links"], "3")
        self.assertNotEqual(by_label["Selected Outputs"], "1")
        self.assertNotEqual(by_label["Public Links"], "1")

    def test_credential_parsing_handles_empty_degree(self) -> None:
        md = """# Jane Doe

Applied researcher.

## Background

| Degree | Field | Institution | Period |
|--------|-------|-------------|--------|
| **Ph.D.** | AI | Seoul National University | 2023-2027 |
| | Science | KAIST Science Academy | 2013-2016 |
"""
        profile = MODULE.parse_profile(md)
        creds = MODULE.extract_credentials(profile)
        self.assertEqual(len(creds), 2)
        kaist = next(c for c in creds if "KAIST" in c["recognizedBy"]["name"])
        self.assertEqual(kaist["credentialCategory"], "training")
        self.assertNotIn("educationalLevel", kaist)
        snu = next(c for c in creds if "Seoul" in c["recognizedBy"]["name"])
        self.assertEqual(snu["credentialCategory"], "degree")
        self.assertEqual(snu["educationalLevel"], "Doctorate")


if __name__ == "__main__":
    unittest.main()
