"""Check that README.md keeps the shapes the profile site and its structured data rely on.

Usage: python3 scripts/lint_readme.py [path/to/README.md]

The site generator is forgiving: a publication row in an unexpected shape still
shows on the page but silently drops out of the structured data, and a renamed
"Profile Site" badge silently changes the canonical URL. This check turns those
silent changes into errors, so `make check` and CI catch them before deploying.

Errors (exit code 1):
- no "# Name" title, or more than one
- no link labeled "Profile Site" (the canonical URL comes from it)
- an em dash or en dash anywhere (the owner's style rule)
- an image without alt text
- a News item that does not start with a bold year, or News years out of order
- a Research item that is not "**Area**: description"
- a publication row the generator cannot parse, a year that is not four digits,
  or rows not ordered newest first
- a Background row without a bold degree, an institution, or a period
- a Projects item that is not "**Name** (period): funder"
- a Patents paragraph without a bold name, a granted-year badge, or a link
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"

_SPEC = importlib.util.spec_from_file_location("build_readme_page", Path(__file__).with_name("build_readme_page.py"))
assert _SPEC and _SPEC.loader
site = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("build_readme_page", site)
_SPEC.loader.exec_module(site)

DASHES = {"\u2014": "em dash", "\u2013": "en dash"}
YEAR_RE = re.compile(r"^\d{4}$")
NEWS_RE = re.compile(r"^\*\*(?P<year>\d{4})\*\*:\s+\S")
RESEARCH_RE = re.compile(r"^\*\*[^*]+\*\*:\s+\S")
PERIOD_RE = re.compile(r"^\d{4}(-\d{4})?( \(expected\))?$")
ALT_RE = re.compile(r"!\[([^\]]*)\]\(")
PROFILE_LINK_RE = re.compile(r"\[!?\[?Profile Site\]?", re.IGNORECASE)


@dataclass(frozen=True)
class Problem:
    line: int
    message: str


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def lint(markdown: str) -> list[Problem]:
    problems: list[Problem] = []
    lines = markdown.splitlines()

    titles = [index for index, line in enumerate(lines, start=1) if line.startswith("# ")]
    if not titles:
        problems.append(Problem(1, 'No "# Name" title line.'))
    elif len(titles) > 1:
        problems.extend(Problem(index, "More than one top-level title.") for index in titles[1:])

    if not any(PROFILE_LINK_RE.search(line) for line in lines):
        problems.append(Problem(1, 'No "Profile Site" link; the site uses it as its canonical URL.'))

    for number, line in enumerate(lines, start=1):
        for char, name in DASHES.items():
            if char in line:
                problems.append(Problem(number, f"Contains an {name}; use a comma, colon or hyphen."))
        for alt in ALT_RE.findall(line):
            if not alt.strip():
                problems.append(Problem(number, "Image has no alt text."))

    section = ""
    table_header: list[str] | None = None
    table_years: list[tuple[int, int]] = []
    news_years: list[tuple[int, int]] = []
    paragraph: list[tuple[int, str]] = []

    def check_order(years: list[tuple[int, int]], what: str) -> None:
        for (_, previous), (number, year) in zip(years, years[1:]):
            if year > previous:
                problems.append(Problem(number, f"{what} are not ordered newest first."))

    def flush_table() -> None:
        nonlocal table_header, table_years
        if table_years:
            check_order(table_years, "Publication rows")
        table_header, table_years = None, []

    def flush_patent_paragraph() -> None:
        nonlocal paragraph
        if section == "patents" and paragraph:
            number = paragraph[0][0]
            text = " ".join(part for _, part in paragraph)
            if not site.PATENT_NAME_RE.search(text):
                problems.append(Problem(number, "Patent has no **bold name**."))
            if not site.PATENT_BADGE_YEAR_RE.search(text):
                problems.append(Problem(number, "Patent has no Granted_YYYY badge."))
            if not site.PATENT_LINK_RE.search(text):
                problems.append(Problem(number, "Patent has no [[label](url)] link."))
        paragraph = []

    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if raw.startswith("## "):
            flush_table()
            flush_patent_paragraph()
            if news_years:
                check_order(news_years, "News items")
                news_years = []
            section = raw[3:].strip().lower()
            continue
        if not line or line in site.HORIZONTAL_RULES or line.startswith("### "):
            flush_table()
            flush_patent_paragraph()
            continue

        if line.startswith("|"):
            cells = split_row(line)
            if table_header is None:
                table_header = [cell.lower() for cell in cells]
                continue
            if is_separator(cells):
                continue
            if section.startswith("publication"):
                lint_publication_row(number, cells, table_header, problems, table_years)
            elif section.startswith(("background", "education")):
                lint_background_row(number, cells, table_header, problems)
            continue
        flush_table()

        if line.startswith("- "):
            item = line[2:].strip()
            if section == "news":
                match = NEWS_RE.match(item)
                if match:
                    news_years.append((number, int(match.group("year"))))
                else:
                    problems.append(Problem(number, 'News item should start with "**YYYY**: ".'))
            elif section == "research" and not RESEARCH_RE.match(item):
                problems.append(Problem(number, 'Research item should be "**Area**: description".'))
            elif section == "projects" and not site.PROJECT_RE.match(item):
                problems.append(Problem(number, 'Project should be "**Name** (period): funder".'))
            continue

        if section == "patents" and not line.startswith("<"):
            paragraph.append((number, line))

    flush_table()
    flush_patent_paragraph()
    if news_years:
        check_order(news_years, "News items")
    return sorted(problems, key=lambda problem: problem.line)


def column(header: list[str], *names: str) -> int | None:
    return next((index for index, cell in enumerate(header) if any(name in cell for name in names)), None)


def lint_publication_row(
    number: int,
    cells: list[str],
    header: list[str],
    problems: list[Problem],
    years: list[tuple[int, int]],
) -> None:
    year_index = column(header, "year", "date")
    pub_index = column(header, "publication", "title", "citation")
    if pub_index is None:
        pub_index = 1 if len(header) > 1 else 0
    if year_index is not None and year_index < len(cells):
        year = site.strip_markdown(cells[year_index]).strip()
        if YEAR_RE.match(year):
            years.append((number, int(year)))
        else:
            problems.append(Problem(number, f'Year "{year}" is not four digits.'))
    if pub_index >= len(cells):
        problems.append(Problem(number, "Publication row is missing its publication cell."))
        return
    text = site.DOI_LINK_RE.sub("", cells[pub_index]).strip(" .")
    if not site.PUBLICATION_RE.match(text):
        problems.append(Problem(
            number,
            'Publication should read: Authors. "Title." *Venue* volume(issue). '
            "This row would be left out of the structured data.",
        ))


def lint_background_row(number: int, cells: list[str], header: list[str], problems: list[Problem]) -> None:
    degree_index = column(header, "degree")
    institution_index = column(header, "institution", "school", "university")
    period_index = column(header, "period", "year", "date")
    if degree_index is not None and degree_index < len(cells) and not cells[degree_index].startswith("**"):
        problems.append(Problem(number, "Background row should start with a **bold degree**."))
    if institution_index is None or institution_index >= len(cells) or not cells[institution_index]:
        problems.append(Problem(number, "Background row has no institution."))
    if period_index is not None:
        period = cells[period_index] if period_index < len(cells) else ""
        if not PERIOD_RE.match(period):
            problems.append(Problem(number, f'Period "{period}" should look like 2021-2023 or 2023-2027 (expected).'))


def report(problem: Problem, path: Path) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::error file={path.name},line={problem.line}::{problem.message}")
    else:
        print(f"error: {path.name}:{problem.line}: {problem.message}")


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else README_PATH
    problems = lint(path.read_text(encoding="utf-8"))
    for problem in problems:
        report(problem, path)
    if problems:
        print(f"{path.name}: {len(problems)} problem(s).")
        return 1
    print(f"{path.name}: OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
