from __future__ import annotations

import contextlib
import http.client
import importlib.util
import io
import os
import sys
import tempfile
import unittest
import urllib.error
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

    def test_each_doi_is_looked_up_once(self) -> None:
        markdown = SAMPLE + "\n- [Paper one](https://doi.org/10.1007/s10921-025-01260-3) again\n"
        calls: list[str] = []

        def lookup(doi: str) -> bool:
            calls.append(doi)
            return True

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text(markdown, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), mock.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}):
                MODULE.check(path, lookup=lookup)
        self.assertEqual(sorted(calls), ["10.1007/s10921-025-01260-3", "10.1061/JSENDH.STENG-14823"])


    def test_find_doi_links_handles_parentheses_encoding_and_www(self) -> None:
        markdown = (
            "[a](https://doi.org/10.1061/(ASCE)ST.1943-541X.0002345)\n"
            "[b](https://www.doi.org/10.1007/s10921-025-01260-3)\n"
            "[c](https://doi.org/10.1002%2Feqe.1234)\n"
        )
        links = MODULE.find_doi_links(markdown)
        self.assertEqual(
            [(link.doi, link.via_doi_org) for link in links],
            [
                ("10.1061/(ASCE)ST.1943-541X.0002345", True),
                ("10.1007/s10921-025-01260-3", True),
                ("10.1002/eqe.1234", True),
            ],
        )

    def _lookup_with(self, side_effect: object) -> bool | None:
        with mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=side_effect), mock.patch.object(
            MODULE.time, "sleep"
        ):
            return MODULE.lookup_doi("10.1234/example", attempts=2)

    @staticmethod
    def _http_error(code: int, body: bytes) -> urllib.error.HTTPError:
        return urllib.error.HTTPError("https://doi.org/x", code, "error", {}, io.BytesIO(body))

    def test_lookup_reads_doi_org_answers(self) -> None:
        found = mock.MagicMock()
        found.__enter__.return_value = io.BytesIO(b'{"responseCode": 1}')
        self.assertIs(self._lookup_with([found]), True)
        self.assertIs(self._lookup_with([self._http_error(404, b'{"responseCode": 100}')] * 2), False)

    def test_lookup_treats_unclear_failures_as_unchecked(self) -> None:
        # A dropped connection used to escape as a traceback and fail the run.
        self.assertIsNone(self._lookup_with(http.client.RemoteDisconnected("closed")))
        self.assertIsNone(self._lookup_with(http.client.IncompleteRead(b"")))
        # A 404 page that is not doi.org's JSON (a proxy or CDN) is not proof of absence.
        self.assertIsNone(self._lookup_with([self._http_error(404, b"<html>Not Found</html>")] * 2))
        self.assertIsNone(self._lookup_with([self._http_error(503, b"busy")] * 2))


if __name__ == "__main__":
    unittest.main()
