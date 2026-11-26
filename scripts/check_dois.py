"""Check that the DOIs linked from README.md are registered with doi.org.

Usage: python3 scripts/check_dois.py [path/to/README.md]

- A https://doi.org/<doi> link whose DOI is not registered fails the run,
  because visitors who click it see "DOI Not Found".
- A publisher link that carries a DOI (for example
  https://ascelibrary.org/doi/10.1061/...) never fails the run. It is reported
  as a notice, so the link can be switched to doi.org once the DOI resolves.
- If doi.org cannot be reached, that DOI is reported as a warning and does not
  fail the run.
- For a table row with a quoted "Title.", the title registered for the DOI is
  compared with the README's title. A DOI that points to a clearly different
  work (a typo can land on another registered DOI) fails the run; a moderate
  difference is a warning.
- With --fail-on-action (used by the weekly scheduled run), a publisher link
  whose DOI now resolves at doi.org also fails the run, so the owner is
  notified that the link can be switched.

On GitHub Actions the results are printed as workflow annotations.
"""

from __future__ import annotations

import argparse
import difflib
import html
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
TITLE_RE = re.compile(r'"([^"]{8,})"')
CSL_JSON = "application/vnd.citationstyles.csl+json"
# Below DIFFERENT_WORK the DOI almost certainly names another paper; below
# SAME_WORK the titles differ enough to be worth a look.
DIFFERENT_WORK = 0.6
SAME_WORK = 0.9

# doi.org handle API response codes: 1 = found, 100 = handle not found,
# 200 = handle exists but has no values.
FOUND = 1
NOT_FOUND = {100, 200}


@dataclass(frozen=True)
class DoiLink:
    url: str
    doi: str
    line: int
    title: str | None = None

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
                title_match = TITLE_RE.search(line)
                title = title_match.group(1).strip().rstrip(".") if title_match else None
                links.append(DoiLink(url=url, doi=doi_match.group(1), line=line_number, title=title))
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


def fetch_doi_title(doi: str, timeout: float = 15.0, attempts: int = 2) -> str | None:
    """Return the title registered for a DOI (CSL JSON from doi.org), or None if unavailable."""
    url = "https://doi.org/" + urllib.parse.quote(doi, safe="/()")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": CSL_JSON})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.load(response)
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError):
            body = None
        if isinstance(body, dict):
            title = body.get("title")
            if isinstance(title, list):
                title = title[0] if title else None
            if isinstance(title, str) and title.strip():
                return title.strip()
            return None
        if attempt + 1 < attempts:
            time.sleep(2**attempt)
    return None


def normalize_title(title: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", title)).lower()
    return " ".join(re.sub(r"[^0-9a-z]+", " ", text).split())


def title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def report(level: str, message: str, path: Path, line: int) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::{level} file={path.name},line={line}::{message}")
    else:
        print(f"{level.upper()}: {path.name}:{line}: {message}")


def check(
    path: Path,
    lookup: Callable[[str], bool | None] = lookup_doi,
    fetch_title: Callable[[str], str | None] = fetch_doi_title,
    fail_on_action: bool = False,
) -> int:
    links = find_doi_links(path.read_text(encoding="utf-8"))
    broken = 0
    actions = 0
    # A DOI can be linked more than once (News and Publications); ask doi.org once per DOI.
    answers: dict[str, bool | None] = {}
    titles: dict[str, str | None] = {}
    for link in links:
        if link.doi not in answers:
            answers[link.doi] = lookup(link.doi)
        registered = answers[link.doi]
        if registered and link.title:
            if link.doi not in titles:
                titles[link.doi] = fetch_title(link.doi)
            registered_title = titles[link.doi]
            if registered_title:
                score = title_similarity(link.title, registered_title)
                if score < DIFFERENT_WORK:
                    broken += 1
                    report(
                        "error",
                        f"{link.doi} is registered for a different work: \"{registered_title}\". "
                        "Check the DOI for a typo.",
                        path,
                        link.line,
                    )
                    continue
                if score < SAME_WORK:
                    report(
                        "warning",
                        f"The README title differs from the title registered for {link.doi}: \"{registered_title}\".",
                        path,
                        link.line,
                    )
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
            if fail_on_action:
                actions += 1
            report(
                "error" if fail_on_action else "notice",
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
    summary = f"Checked {len(links)} DOI link(s) in {path.name}: {broken} broken."
    if fail_on_action:
        summary += f" {actions} link(s) to update."
    print(summary)
    return 1 if broken or actions else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check the DOIs linked from the README.")
    parser.add_argument("path", nargs="?", type=Path, default=README_PATH)
    parser.add_argument(
        "--fail-on-action",
        action="store_true",
        help="also fail when a publisher link can now be switched to doi.org",
    )
    args = parser.parse_args(argv[1:])
    return check(args.path, fail_on_action=args.fail_on_action)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
