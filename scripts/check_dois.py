"""Check that the DOIs linked from README.md are registered with doi.org.

Usage: python3 scripts/check_dois.py [path/to/README.md]

- A https://doi.org/<doi> link whose DOI is not registered fails the run,
  because visitors who click it see "DOI Not Found".
- A publisher link that carries a DOI (for example
  https://ascelibrary.org/doi/10.1061/...) never fails the run. It is reported
  as a notice, so the link can be switched to doi.org once the DOI resolves.
- If doi.org cannot be reached, that DOI is reported as a warning and does not
  fail the run.

On GitHub Actions the results are printed as workflow annotations.
"""

from __future__ import annotations

import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
HANDLE_API = "https://doi.org/api/handles/"
DOI_HOSTS = {"doi.org", "dx.doi.org"}
# Link targets may contain balanced parentheses, as DOIs like 10.1061/(ASCE)ST.1943-541X.0002345 do.
LINK_RE = re.compile(r"\]\((https?://(?:[^()\s]|\([^()\s]*\))+)\)")
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s?#]+)")
USER_AGENT = "profile-readme-doi-check/1.0"

# doi.org handle API response codes: 1 = found, 100 = handle not found,
# 200 = handle exists but has no values.
FOUND = 1
NOT_FOUND = {100, 200}


@dataclass(frozen=True)
class DoiLink:
    url: str
    doi: str
    line: int

    @property
    def via_doi_org(self) -> bool:
        host = (urllib.parse.urlsplit(self.url).hostname or "").lower().removeprefix("www.")
        return host in DOI_HOSTS


def find_doi_links(markdown: str) -> list[DoiLink]:
    links: list[DoiLink] = []
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            url = match.group(1)
            # Decode first so 10.1002%2F... and %28ASCE%29 compare equal to their plain spelling.
            doi_match = DOI_RE.search(urllib.parse.unquote(url))
            if doi_match:
                links.append(DoiLink(url=url, doi=doi_match.group(1), line=line_number))
    return links


def lookup_doi(doi: str, timeout: float = 15.0, attempts: int = 3) -> bool | None:
    """Return True if doi.org knows the DOI, False if it does not, None if it could not be checked."""
    url = HANDLE_API + urllib.parse.quote(doi, safe="/")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        code: int | None = None
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.load(response)
                code = body.get("responseCode") if isinstance(body, dict) else None
        except urllib.error.HTTPError as error:
            # Only doi.org's own JSON answer is proof of absence. A 404 page from a proxy
            # or CDN is treated like any other failure and retried.
            if error.code == 404:
                try:
                    body = json.load(error)
                    code = body.get("responseCode") if isinstance(body, dict) else None
                except (ValueError, OSError, http.client.HTTPException):
                    code = None
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError, AttributeError):
            # Dropped connections (RemoteDisconnected), truncated bodies (IncompleteRead),
            # timeouts and malformed JSON all mean "could not check", never a crash.
            code = None
        if code == FOUND:
            return True
        if code in NOT_FOUND:
            return False
        if attempt + 1 < attempts:
            time.sleep(2**attempt)
    return None


def report(level: str, message: str, path: Path, line: int) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::{level} file={path.name},line={line}::{message}")
    else:
        print(f"{level.upper()}: {path.name}:{line}: {message}")


def check(path: Path, lookup: Callable[[str], bool | None] = lookup_doi) -> int:
    links = find_doi_links(path.read_text(encoding="utf-8"))
    broken = 0
    # A DOI can be linked more than once (News and Publications); ask doi.org once per DOI.
    answers: dict[str, bool | None] = {}
    for link in links:
        if link.doi not in answers:
            answers[link.doi] = lookup(link.doi)
        registered = answers[link.doi]
        if registered is None:
            report("warning", f"Could not reach doi.org to check {link.doi}.", path, link.line)
        elif link.via_doi_org and not registered:
            broken += 1
            report(
                "error",
                f"{link.url} shows 'DOI Not Found': {link.doi} is not registered with doi.org. "
                "Check the DOI, or link to the publisher's page until it is registered.",
                path,
                link.line,
            )
        elif not link.via_doi_org and registered:
            report(
                "notice",
                f"{link.doi} now resolves at doi.org, so {link.url} can become https://doi.org/{link.doi}.",
                path,
                link.line,
            )
        elif not link.via_doi_org:
            report(
                "notice",
                f"{link.doi} is not registered with doi.org yet; keep the publisher link {link.url} for now.",
                path,
                link.line,
            )
        else:
            print(f"ok: {link.doi}")
    print(f"Checked {len(links)} DOI link(s) in {path.name}: {broken} broken.")
    return 1 if broken else 0


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else README_PATH
    return check(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
