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
SCRIPT_PATH = ROOT / "scripts" / "check_dois.py"
SPEC = importlib.util.spec_from_file_location("check_dois", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

SAMPLE = """# Jane Doe

| 2025 | Paper one. *J. One* 1(1). [[DOI](https://doi.org/10.1007/s10921-025-01260-3)] |
| 2025 | Paper two. *J. Two* 2(2). [[DOI](https://ascelibrary.org/doi/10.1061/JSENDH.STENG-14823)] |

[Google Scholar](https://scholar.google.com/citations?user=abc)
"""


class CheckDoisTests(unittest.TestCase):
    def run_check(self, markdown: str, answers: dict[str, bool | None]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text(markdown, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}):
                code = MODULE.check(path, lookup=lambda doi: answers[doi])
        return code, out.getvalue()

    def test_find_doi_links_reads_doi_org_and_publisher_urls(self) -> None:
        links = MODULE.find_doi_links(SAMPLE)
        self.assertEqual(
            [(link.doi, link.via_doi_org, link.line) for link in links],
            [("10.1007/s10921-025-01260-3", True, 3), ("10.1061/JSENDH.STENG-14823", False, 4)],
        )

    def test_unregistered_doi_org_link_fails(self) -> None:
        code, out = self.run_check(
            SAMPLE, {"10.1007/s10921-025-01260-3": False, "10.1061/JSENDH.STENG-14823": False}
        )
        self.assertEqual(code, 1)
        self.assertIn("ERROR: README.md:3:", out)
        self.assertIn("1 broken", out)

    def test_unregistered_publisher_link_is_only_a_notice(self) -> None:
        code, out = self.run_check(
            SAMPLE, {"10.1007/s10921-025-01260-3": True, "10.1061/JSENDH.STENG-14823": False}
        )
        self.assertEqual(code, 0)
        self.assertIn("NOTICE: README.md:4:", out)
        self.assertIn("not registered with doi.org yet", out)

    def test_registered_publisher_link_suggests_doi_org(self) -> None:
        code, out = self.run_check(
            SAMPLE, {"10.1007/s10921-025-01260-3": True, "10.1061/JSENDH.STENG-14823": True}
        )
        self.assertEqual(code, 0)
        self.assertIn("https://doi.org/10.1061/JSENDH.STENG-14823", out)

    def test_unreachable_doi_org_is_a_warning_not_a_failure(self) -> None:
        code, out = self.run_check(
            SAMPLE, {"10.1007/s10921-025-01260-3": None, "10.1061/JSENDH.STENG-14823": None}
        )
        self.assertEqual(code, 0)
        self.assertIn("WARNING: README.md:3:", out)

    def test_github_actions_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text(SAMPLE, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                MODULE.check(path, lookup=lambda doi: False)
        self.assertIn("::error file=README.md,line=3::", out.getvalue())


if __name__ == "__main__":
    unittest.main()
