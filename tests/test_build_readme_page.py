from __future__ import annotations

import importlib.util
import re
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

        self.assertNotIn("Profile snapshot", artifacts.html)
        self.assertNotIn("Build stamp", artifacts.html)
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
        self.assertEqual(journal["isPartOf"]["@type"], "PublicationIssue")
        self.assertEqual(journal["isPartOf"]["issueNumber"], "12")
        volume = journal["isPartOf"]["isPartOf"]
        self.assertEqual(volume["@type"], "PublicationVolume")
        self.assertEqual(volume["volumeNumber"], "151")
        self.assertEqual(volume["isPartOf"]["@type"], "Periodical")
        self.assertEqual(volume["isPartOf"]["name"], "J. Structural Engineering")
        self.assertEqual(journal["sameAs"], "https://doi.org/10.1234/example")
        self.assertEqual(journal["identifier"]["value"], "10.1234/example")
        self.assertEqual(journal["identifier"]["propertyID"], "DOI")

        conference = pubs[1]
        self.assertEqual(conference["isPartOf"]["@type"], "PublicationEvent")
        self.assertEqual(conference["isPartOf"]["name"], "EACWE 2024")
        self.assertNotIn("issueNumber", conference["isPartOf"])
        self.assertNotIn("identifier", conference)

    def test_conference_with_location_does_not_set_issue_number(self) -> None:
        md = """# Jane Doe

Researcher.

## Publications

### Selected Conference Papers

| Year | Publication |
|:----:|-------------|
| 2024 | **J. Doe**, A. Smith. "Test paper." *Structures Congress*, Seoul. |
"""
        profile = MODULE.parse_profile(md)
        pubs = MODULE.extract_publications(profile, "https://example.com/#person")
        self.assertEqual(len(pubs), 1)
        is_part_of = pubs[0]["isPartOf"]
        self.assertEqual(is_part_of["@type"], "PublicationEvent")
        self.assertEqual(is_part_of["name"], "Structures Congress")
        self.assertNotIn("issueNumber", is_part_of)

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

    def test_og_svg_starts_at_column_zero(self) -> None:
        artifacts = MODULE.render_site_artifacts(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        first_line = artifacts.og_image.split("\n", 1)[0]
        self.assertTrue(first_line.startswith("<svg "),
                        f"SVG should start at column 0, got: {first_line!r}")

    def test_sitemap_xml_declaration_starts_at_column_zero(self) -> None:
        artifacts = MODULE.render_site_artifacts(SAMPLE_MARKDOWN, generated_at=FIXED_AT)
        first_line = artifacts.sitemap.split("\n", 1)[0]
        self.assertEqual(first_line, '<?xml version="1.0" encoding="UTF-8"?>')
        for line in artifacts.sitemap.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("<lastmod>"):
                self.assertTrue(line.startswith("    <lastmod>"),
                                f"lastmod should be indented with 4 spaces, got: {line!r}")

    def test_summarize_section_uses_table_content_not_trailing_paragraph(self) -> None:
        md = """# Jane Doe

Researcher.

## Publications

### Journal Articles

| Year | Publication |
|------|-------------|
| 2025 | First real publication title |
| 2024 | Second publication |

[See full list on Scholar](https://scholar.google.com/x)
"""
        profile = MODULE.parse_profile(md)
        section = next(s for s in profile.sections if s.heading == "Publications")
        summary = MODULE.summarize_section(section)
        self.assertIn("First real publication title", summary)
        self.assertNotIn("Scholar", summary)

    def test_keywords_excludes_section_headings(self) -> None:
        md = """# Jane Doe

Researcher.

## Focus
- Topic alpha
- Topic beta

## Background

| Degree | Field | Institution | Period |
|--------|-------|-------------|--------|
| Ph.D. | AI | SNU | 2023-2027 |

## Code
- [tool](https://example.com): A thing
"""
        output = MODULE.render_site(md, generated_at=FIXED_AT)
        kw_match = re.search(r'<meta name="keywords" content="([^"]+)"', output)
        self.assertIsNotNone(kw_match)
        keywords = [k.strip() for k in kw_match.group(1).split(",")]
        self.assertNotIn("Background", keywords)
        self.assertNotIn("Code", keywords)
        self.assertIn("Jane Doe", keywords)

    def test_knows_about_excludes_section_headings(self) -> None:
        md = """# Jane Doe

Researcher.

## Research
- Topic alpha
- Topic beta

## Background

| Degree | Field | Institution | Period |
|--------|-------|-------------|--------|
| Ph.D. | AI | SNU | 2023-2027 |

## Code
- [tool](https://example.com): A thing
"""
        output = MODULE.render_site(md, generated_at=FIXED_AT)
        self.assertIn('"knowsAbout"', output)
        self.assertNotIn('"Background"', output.split('"knowsAbout"')[1].split(']')[0])
        self.assertNotIn('"Code"', output.split('"knowsAbout"')[1].split(']')[0])

    def test_extract_links_includes_intro_badges(self) -> None:
        md = """# Jane Doe

[![Scholar](https://shields.io/badge/scholar-x?style=for-the-badge)](https://scholar.google.com/x)
[![ORCID](https://shields.io/badge/orcid-x?style=for-the-badge)](https://orcid.org/x)
[![Email](https://shields.io/badge/email-x?style=for-the-badge)](mailto:jane@example.com)

Researcher.
"""
        profile = MODULE.parse_profile(md)
        links = MODULE.extract_links(profile)
        hrefs = [link.href for link in links]
        self.assertIn("https://scholar.google.com/x", hrefs)
        self.assertIn("https://orcid.org/x", hrefs)
        self.assertIn("mailto:jane@example.com", hrefs)

    def test_link_label_renders_markdown_bold(self) -> None:
        md = """# Jane Doe

Researcher.

## Code
- [**myrepo**](https://github.com/x/myrepo): A tool
"""
        output = MODULE.render_site(md, generated_at=FIXED_AT)
        self.assertIn("<strong>myrepo</strong>", output)
        self.assertNotIn(">**myrepo**<", output)
        self.assertNotIn("**myrepo**</a>", output)

    def test_wrap_svg_lines_truncation_indicator(self) -> None:
        long_text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron"
        lines = MODULE.wrap_svg_lines(long_text, width=20, max_lines=2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].endswith("..."), f"Last line should end with ...: {lines[-1]!r}")
        self.assertFalse(lines[-1].rstrip(".").endswith(("a", "e", "i", "o", "u")) and len(lines[-1]) < 5,
                         "Should not cut mid-word with single char")

    def test_summarize_description_separates_intro_paragraphs(self) -> None:
        md = """# Jane Doe

**Senior researcher**

ML engineer working on robust systems
"""
        profile = MODULE.parse_profile(md)
        summary = MODULE.summarize_description(profile, [])
        self.assertIn("Senior researcher. ML engineer", summary)
        self.assertNotIn("researcher ML engineer", summary)

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
