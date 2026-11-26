from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "lint_readme.py"
SPEC = importlib.util.spec_from_file_location("lint_readme", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

VALID = """<div align="center">

# Jane Doe

[![Profile Site](https://img.shields.io/badge/Profile_Site-B84A30)](https://example.org/)

</div>

## News

- **2026**: Paper accepted.
- **2025**: Award received.

## Research

- **Structural Health Monitoring**: Anomaly detection

## Publications

### Journal Articles

| Year | Publication |
|:----:|-------------|
| 2025 | **J. Doe**, A. Kim. "A journal paper." *J. Structures* 1(2). [[DOI](https://doi.org/10.1234/a)] |
| 2024 | **J. Doe**. "An older paper." *J. Structures* 1(1). |

### Selected Conference Papers

| Year | Publication |
|:----:|-------------|
| 2026 | **J. Doe**, T. Kang. "A conference paper." *JCDL 2026*. |

## Patents

![KR 1, granted 2023](https://img.shields.io/badge/KR_1-Granted_2023-0f766e) **A patent** [[Google Patents](https://patents.google.com/patent/KR1/en)]

## Projects

- **A Project** (2021-2027): NRF Korea

## Background

| Degree | Institution | Period |
|--------|-------------|--------|
| **Ph.D.**, AI | Seoul National University | 2023-2027 (expected) |
| **M.S.**, Structures | Seoul National University | 2021-2023 |
"""


def problems(markdown: str) -> list[tuple[int, str]]:
    return [(problem.line, problem.message) for problem in MODULE.lint(markdown)]


class LintReadmeTests(unittest.TestCase):
    def test_valid_readme_has_no_problems(self) -> None:
        self.assertEqual(problems(VALID), [])

    def test_real_readme_passes(self) -> None:
        self.assertEqual(problems((ROOT / "README.md").read_text(encoding="utf-8")), [])

    def assert_problem(self, markdown: str, line: int, fragment: str) -> None:
        found = problems(markdown)
        self.assertTrue(
            any(number == line and fragment in message for number, message in found),
            f"expected line {line} with {fragment!r}, got {found}",
        )

    def test_missing_title_and_profile_site(self) -> None:
        markdown = VALID.replace("# Jane Doe", "Jane Doe").replace("[![Profile Site]", "[![Home]")
        found = [message for _, message in problems(markdown)]
        self.assertTrue(any("title" in message for message in found))
        self.assertTrue(any("Profile Site" in message for message in found))

    def test_dashes_and_missing_alt_text(self) -> None:
        self.assert_problem(VALID.replace("Anomaly detection", "Anomaly \u2014 detection"), 16, "em dash")
        self.assert_problem(VALID.replace("Anomaly detection", "2021\u20132023"), 16, "en dash")
        self.assert_problem(VALID.replace("![KR 1, granted 2023]", "![]"), 35, "alt text")

    def test_news_format_and_order(self) -> None:
        self.assert_problem(VALID.replace("- **2025**: Award", "- 2025: Award"), 12, "**YYYY**")
        self.assert_problem(VALID.replace("- **2025**: Award", "- **2027**: Award"), 12, "newest first")

    def test_research_and_project_shapes(self) -> None:
        self.assert_problem(VALID.replace("- **Structural Health Monitoring**: Anomaly", "- Structural health"), 16, "**Area**")
        self.assert_problem(VALID.replace("(2021-2027): NRF", "2021-2027: NRF"), 39, "**Name** (period)")

    def test_publication_rows_must_parse_and_be_ordered(self) -> None:
        self.assert_problem(VALID.replace('"A journal paper."', "A journal paper."), 24, "left out of the structured data")
        self.assert_problem(VALID.replace("| 2025 | **J. Doe**, A. Kim.", "| 25 | **J. Doe**, A. Kim."), 24, "four digits")
        self.assert_problem(VALID.replace("| 2024 | **J. Doe**. ", "| 2026 | **J. Doe**. "), 25, "newest first")

    def test_background_rows(self) -> None:
        self.assert_problem(VALID.replace("| **M.S.**, Structures", "| M.S., Structures"), 46, "bold degree")
        self.assert_problem(VALID.replace("| 2021-2023 |", "| 2021~2023 |"), 46, "Period")

    def test_patent_needs_badge_name_and_link(self) -> None:
        markdown = VALID.replace(" **A patent** [[Google Patents](https://patents.google.com/patent/KR1/en)]", " A patent")
        found = [message for number, message in problems(markdown) if number == 35]
        self.assertTrue(any("bold name" in message for message in found))
        self.assertTrue(any("link" in message for message in found))

    def test_main_reports_errors_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text(VALID.replace("- **2025**: Award", "- 2025: Award"), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                code = MODULE.main(["lint_readme.py", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("::error file=README.md,line=12::", out.getvalue())


if __name__ == "__main__":
    unittest.main()
