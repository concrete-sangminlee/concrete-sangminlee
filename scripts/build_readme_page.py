#!/usr/bin/env python3

from __future__ import annotations

import html
import json
import re
import textwrap
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
OUTPUT_PATH = ROOT / "docs" / "index.html"
REPO_URL = "https://github.com/concrete-sangminlee/concrete-sangminlee"

AUTOLINK_RE = re.compile(r"https?://\S+|[\w.+-]+@[\w.-]+\.\w+")
INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
LINK_ITEM_RE = re.compile(r"^(?P<label>[^:]+):\s*(?P<target>\S.+)$")


@dataclass
class Block:
    kind: str
    items: list[str]


@dataclass
class Section:
    heading: str
    anchor: str
    blocks: list[Block]


@dataclass
class Profile:
    title: str
    intro: list[str]
    sections: list[Section]


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>__PAGE_TITLE__</title>
    <meta name="description" content="__DESCRIPTION__" />
    <meta name="theme-color" content="#14211d" />
    <meta property="og:title" content="__PAGE_TITLE__" />
    <meta property="og:description" content="__DESCRIPTION__" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="__CANONICAL_URL__" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="__PAGE_TITLE__" />
    <meta name="twitter:description" content="__DESCRIPTION__" />
    <link rel="canonical" href="__CANONICAL_URL__" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <style>
      :root {
        color-scheme: light;
        --paper: #f4eadc;
        --paper-strong: #f8f4ee;
        --ink: #14211d;
        --muted: #55635d;
        --line: rgba(20, 33, 29, 0.12);
        --panel: rgba(255, 255, 255, 0.74);
        --panel-strong: rgba(255, 255, 255, 0.9);
        --accent: #c4492d;
        --accent-soft: rgba(196, 73, 45, 0.14);
        --teal: #0f766e;
        --shadow: 0 24px 80px rgba(20, 33, 29, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      html {
        scroll-behavior: smooth;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Manrope", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(196, 73, 45, 0.18), transparent 30%),
          radial-gradient(circle at 85% 10%, rgba(15, 118, 110, 0.16), transparent 24%),
          linear-gradient(180deg, #efe1cf 0%, #f9f6f1 52%, #efe9dd 100%);
      }

      body::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.35;
        background-image:
          linear-gradient(rgba(20, 33, 29, 0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(20, 33, 29, 0.05) 1px, transparent 1px);
        background-size: 28px 28px;
        mask-image: linear-gradient(180deg, #000 10%, transparent 88%);
      }

      a {
        color: inherit;
      }

      .page {
        position: relative;
        width: min(1120px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 28px 0 56px;
      }

      .hero {
        display: grid;
        grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.9fr);
        gap: 24px;
        align-items: stretch;
        padding: 36px;
        border: 1px solid var(--line);
        border-radius: 32px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.6));
        box-shadow: var(--shadow);
        backdrop-filter: blur(20px);
      }

      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 16px;
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }

      .eyebrow::before {
        content: "";
        width: 34px;
        height: 1px;
        background: rgba(20, 33, 29, 0.28);
      }

      .hero h1 {
        margin: 0;
        font-family: "Fraunces", serif;
        font-size: clamp(3rem, 7vw, 5.3rem);
        line-height: 0.92;
        letter-spacing: -0.06em;
      }

      .hero-intro {
        max-width: 52rem;
        margin-top: 18px;
      }

      .hero-intro p {
        margin: 0 0 12px;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.82;
      }

      .tag-list,
      .cta-row,
      .nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .tag-list {
        margin-top: 22px;
      }

      .tag {
        padding: 9px 14px;
        border: 1px solid rgba(20, 33, 29, 0.1);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.9);
        color: var(--ink);
        font-size: 0.9rem;
        font-weight: 700;
      }

      .cta-row {
        margin-top: 24px;
      }

      .button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        min-height: 46px;
        padding: 0 18px;
        border-radius: 999px;
        border: 1px solid transparent;
        text-decoration: none;
        font-weight: 800;
        transition: transform 160ms ease, box-shadow 160ms ease, background-color 160ms ease;
      }

      .button:hover,
      .button:focus-visible,
      .link-card:hover,
      .link-card:focus-visible,
      .nav a:hover,
      .nav a:focus-visible {
        transform: translateY(-2px);
      }

      .button-primary {
        background: var(--ink);
        color: #f7f3ee;
        box-shadow: 0 16px 30px rgba(20, 33, 29, 0.16);
      }

      .button-secondary {
        border-color: rgba(20, 33, 29, 0.12);
        background: rgba(255, 255, 255, 0.82);
        color: var(--ink);
      }

      .status-card {
        position: relative;
        overflow: hidden;
        padding: 24px;
        border-radius: 28px;
        background:
          radial-gradient(circle at top right, rgba(196, 73, 45, 0.32), transparent 34%),
          linear-gradient(180deg, #182824 0%, #101916 100%);
        color: #f6f0e9;
        box-shadow: 0 24px 56px rgba(20, 33, 29, 0.22);
      }

      .status-card::after {
        content: "";
        position: absolute;
        inset: auto -40px -40px auto;
        width: 150px;
        height: 150px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
      }

      .status-label {
        margin: 0 0 12px;
        color: rgba(246, 240, 233, 0.72);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      .status-card h2 {
        position: relative;
        z-index: 1;
        margin: 0;
        font-family: "Fraunces", serif;
        font-size: 2rem;
        line-height: 1.02;
        letter-spacing: -0.04em;
      }

      .status-card p {
        position: relative;
        z-index: 1;
        margin: 14px 0 0;
        color: rgba(246, 240, 233, 0.78);
        line-height: 1.7;
      }

      .status-list {
        position: relative;
        z-index: 1;
        display: grid;
        gap: 12px;
        margin: 20px 0 0;
        padding: 0;
        list-style: none;
      }

      .status-list li {
        padding: 14px 16px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.08);
      }

      .status-list strong,
      .status-list span {
        display: block;
      }

      .status-list strong {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .status-list span {
        margin-top: 6px;
        color: rgba(246, 240, 233, 0.72);
        line-height: 1.55;
      }

      .nav-wrap {
        margin-top: 18px;
      }

      .nav {
        padding: 0;
      }

      .nav a {
        display: inline-flex;
        align-items: center;
        min-height: 42px;
        padding: 0 16px;
        border: 1px solid rgba(20, 33, 29, 0.12);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.76);
        color: var(--ink);
        text-decoration: none;
        font-weight: 700;
        backdrop-filter: blur(10px);
      }

      .content-grid {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 20px;
        margin-top: 24px;
      }

      .panel {
        grid-column: span 6;
        padding: 26px;
        border: 1px solid var(--line);
        border-radius: 28px;
        background: var(--panel);
        box-shadow: 0 18px 42px rgba(20, 33, 29, 0.08);
        backdrop-filter: blur(12px);
      }

      .panel.panel-links {
        grid-column: span 12;
      }

      .panel-label {
        margin: 0 0 10px;
        color: var(--accent);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      .panel h2 {
        margin: 0;
        font-family: "Fraunces", serif;
        font-size: 2rem;
        line-height: 1.05;
        letter-spacing: -0.04em;
      }

      .panel-body {
        margin-top: 18px;
      }

      .panel-body p,
      .panel-body li {
        color: var(--muted);
        line-height: 1.8;
      }

      .panel-body p {
        margin: 0 0 12px;
      }

      .subheading {
        margin: 20px 0 10px;
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
      }

      .detail-list,
      .card-list,
      .link-grid {
        margin: 0;
        padding: 0;
        list-style: none;
      }

      .detail-list {
        display: grid;
        gap: 10px;
      }

      .detail-list li {
        padding-left: 18px;
        position: relative;
      }

      .detail-list li::before {
        content: "";
        position: absolute;
        top: 0.85rem;
        left: 0;
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--accent);
      }

      .card-list {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
      }

      .card-list li {
        min-height: 100%;
        padding: 18px;
        border: 1px solid rgba(20, 33, 29, 0.08);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.72));
        color: var(--ink);
        font-weight: 700;
      }

      .link-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
      }

      .link-card {
        display: grid;
        gap: 12px;
        min-height: 100%;
        padding: 20px;
        border-radius: 24px;
        background: linear-gradient(180deg, #172421 0%, #121a18 100%);
        color: #f8f4ee;
        text-decoration: none;
        box-shadow: 0 22px 46px rgba(20, 33, 29, 0.18);
      }

      .link-card strong {
        font-size: 1.1rem;
      }

      .link-card span {
        color: rgba(248, 244, 238, 0.74);
        line-height: 1.6;
      }

      .link-card small {
        color: #f3c7b9;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .footer {
        display: flex;
        flex-wrap: wrap;
        gap: 14px 22px;
        justify-content: space-between;
        margin-top: 22px;
        padding: 18px 6px 0;
        color: var(--muted);
        font-size: 0.92rem;
      }

      .footer a {
        color: var(--ink);
        text-decoration: none;
        font-weight: 700;
      }

      .accent {
        color: var(--accent);
      }

      @media (max-width: 940px) {
        .hero {
          grid-template-columns: 1fr;
          padding: 26px;
        }

        .panel,
        .panel.panel-links {
          grid-column: span 12;
        }
      }

      @media (max-width: 640px) {
        .page {
          width: min(100vw - 18px, 1120px);
          padding: 14px 0 34px;
        }

        .hero,
        .panel {
          padding: 20px;
          border-radius: 24px;
        }

        .hero h1 {
          font-size: clamp(2.5rem, 16vw, 4rem);
        }

        .panel h2 {
          font-size: 1.7rem;
        }
      }
    </style>
    <script type="application/ld+json">__STRUCTURED_DATA__</script>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <div>
          <p class="eyebrow">Research Profile</p>
          <h1>__TITLE__</h1>
          <div class="hero-intro">__INTRO_HTML__</div>
          <div class="tag-list">__TAG_HTML__</div>
          <div class="cta-row">__CTA_HTML__</div>
        </div>
        <aside class="status-card">
          <p class="status-label">README-driven build</p>
          <h2>Static profile site with a stronger information layout.</h2>
          <p>
            Generated directly from <span class="accent">README.md</span>, styled as a landing
            page, and published as a dependency-light static document.
          </p>
          <ul class="status-list">
            <li>
              <strong>Build</strong>
              <span>No client-side markdown rendering required.</span>
            </li>
            <li>
              <strong>Source of truth</strong>
              <span>Content stays aligned with the profile README.</span>
            </li>
            <li>
              <strong>Build stamp</strong>
              <span>__GENERATED_AT__</span>
            </li>
          </ul>
        </aside>
      </section>

      <div class="nav-wrap">
        <nav class="nav" aria-label="Section navigation">__NAV_HTML__</nav>
      </div>

      <section class="content-grid">
__SECTION_HTML__
      </section>

      <footer class="footer">
        <span>Generated from README.md in <a href="__REPO_URL__">the repository</a>.</span>
        <span>Build stamp: __GENERATED_AT__</span>
      </footer>
    </main>
  </body>
</html>
"""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def parse_blocks(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(Block(kind="paragraph", items=[" ".join(paragraph)]))
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            blocks.append(Block(kind="list", items=list_items.copy()))
            list_items.clear()

    for line in [*lines, ""]:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            blocks.append(Block(kind="subheading", items=[stripped[4:].strip()]))
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
            continue
        flush_list()
        paragraph.append(stripped)

    return blocks


def parse_profile(markdown: str) -> Profile:
    lines = [line.rstrip() for line in markdown.strip().splitlines()]
    title = "Profile"
    body_start = 0

    for index, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body_start = index + 1
            break

    intro_lines: list[str] = []
    sections: list[Section] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    used_anchors: set[str] = set()

    def next_anchor(heading: str) -> str:
        base = slugify(heading)
        anchor = base
        suffix = 2
        while anchor in used_anchors:
            anchor = f"{base}-{suffix}"
            suffix += 1
        used_anchors.add(anchor)
        return anchor

    def flush() -> None:
        nonlocal current_lines
        if current_heading is None:
            intro_lines.extend(current_lines)
        else:
            blocks = parse_blocks(current_lines)
            if blocks:
                sections.append(
                    Section(
                        heading=current_heading,
                        anchor=next_anchor(current_heading),
                        blocks=blocks,
                    )
                )
        current_lines = []

    for line in lines[body_start:]:
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            continue
        current_lines.append(line)
    flush()

    intro_blocks = parse_blocks(intro_lines)
    intro = [block.items[0] for block in intro_blocks if block.kind == "paragraph"]
    return Profile(title=title, intro=intro, sections=sections)


def autolink_plain_text(text: str) -> str:
    parts: list[str] = []
    last_index = 0

    for match in AUTOLINK_RE.finditer(text):
        token = match.group(0)
        end = len(token)
        while end and token[end - 1] in ".,;:)":
            end -= 1
        linked = token[:end]
        trailing = token[end:]
        parts.append(html.escape(text[last_index:match.start()]))
        if linked:
            href = linked if linked.startswith("http") else f"mailto:{linked}"
            parts.append(render_anchor(href, linked))
        parts.append(html.escape(trailing))
        last_index = match.end()

    parts.append(html.escape(text[last_index:]))
    return "".join(parts)


def render_anchor(href: str, label: str) -> str:
    safe_href = html.escape(href, quote=True)
    safe_label = html.escape(label)
    attrs = ' target="_blank" rel="noreferrer"' if href.startswith("http") else ""
    return f'<a href="{safe_href}"{attrs}>{safe_label}</a>'


def render_inline(text: str) -> str:
    parts: list[str] = []
    last_index = 0

    for match in INLINE_LINK_RE.finditer(text):
        parts.append(autolink_plain_text(text[last_index:match.start()]))
        label, target = match.groups()
        href = normalize_href(target)
        parts.append(render_anchor(href, label))
        last_index = match.end()

    parts.append(autolink_plain_text(text[last_index:]))
    return "".join(parts)


def normalize_href(target: str) -> str:
    stripped = target.strip()
    if stripped.startswith(("http://", "https://", "mailto:")):
        return stripped
    if "@" in stripped and " " not in stripped:
        return f"mailto:{stripped}"
    return stripped


def extract_tags(profile: Profile, limit: int = 4) -> list[str]:
    for section in profile.sections:
        if "link" in section.heading.lower():
            continue
        for block in section.blocks:
            if block.kind == "list":
                return block.items[:limit]
    return []


def parse_link_item(item: str) -> tuple[str, str] | None:
    markdown_match = INLINE_LINK_RE.fullmatch(item.strip())
    if markdown_match:
        label, target = markdown_match.groups()
        return label, normalize_href(target)

    match = LINK_ITEM_RE.match(item)
    if match:
        label = match.group("label").strip()
        target = normalize_href(match.group("target").strip())
        return label, target

    href = normalize_href(item)
    if href.startswith(("http://", "https://", "mailto:")):
        label = href.removeprefix("mailto:").split("/")[-1] or "Link"
        return label, href
    return None


def describe_link(href: str) -> str:
    if href.startswith("mailto:"):
        return href.removeprefix("mailto:")
    return href.removeprefix("https://").removeprefix("http://").rstrip("/")


def extract_links(profile: Profile) -> list[tuple[str, str]]:
    for section in profile.sections:
        if "link" not in section.heading.lower():
            continue
        links: list[tuple[str, str]] = []
        for block in section.blocks:
            if block.kind != "list":
                continue
            for item in block.items:
                parsed = parse_link_item(item)
                if parsed:
                    links.append(parsed)
        return links
    return []


def section_label(index: int, section: Section) -> str:
    if "link" in section.heading.lower():
        return "Connect"
    return f"Section {index:02d}"


def render_section(section: Section, index: int) -> str:
    heading = html.escape(section.heading)
    label = html.escape(section_label(index, section))
    body_html = ""
    classes = ["panel"]

    if "link" in section.heading.lower():
        classes.append("panel-links")
        link_cards: list[str] = []
        for block in section.blocks:
            if block.kind != "list":
                continue
            for item in block.items:
                parsed = parse_link_item(item)
                if not parsed:
                    continue
                title, href = parsed
                safe_href = html.escape(href, quote=True)
                target = ' target="_blank" rel="noreferrer"' if href.startswith("http") else ""
                link_cards.append(
                    textwrap.dedent(
                        f"""
                        <a class="link-card" href="{safe_href}"{target}>
                          <small>Open link</small>
                          <strong>{html.escape(title)}</strong>
                          <span>{html.escape(describe_link(href))}</span>
                        </a>"""
                    ).strip()
                )
        body_html = f'<div class="link-grid">{"".join(link_cards)}</div>'
    elif all(block.kind == "list" for block in section.blocks):
        cards = [
            f"<li>{render_inline(item)}</li>"
            for block in section.blocks
            for item in block.items
        ]
        body_html = f'<ul class="card-list">{"".join(cards)}</ul>'
    else:
        parts: list[str] = []
        for block in section.blocks:
            if block.kind == "paragraph":
                parts.append(f"<p>{render_inline(block.items[0])}</p>")
            elif block.kind == "subheading":
                parts.append(f'<p class="subheading">{html.escape(block.items[0])}</p>')
            elif block.kind == "list":
                items = "".join(f"<li>{render_inline(item)}</li>" for item in block.items)
                parts.append(f'<ul class="detail-list">{items}</ul>')
        body_html = "".join(parts)

    class_name = " ".join(classes)
    return textwrap.dedent(
        f"""
        <article class="{class_name}" id="{section.anchor}">
          <p class="panel-label">{label}</p>
          <h2>{heading}</h2>
          <div class="panel-body">{body_html}</div>
        </article>"""
    ).strip()


def pick_primary_url(links: list[tuple[str, str]]) -> str:
    for label, href in links:
        lower_label = label.lower()
        if "site" in lower_label or "profile" in lower_label:
            return href
    for _, href in links:
        if href.startswith("http"):
            return href
    return REPO_URL


def build_structured_data(profile: Profile, description: str, links: list[tuple[str, str]]) -> str:
    payload: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile.title,
        "description": description,
    }
    same_as = [href for _, href in links if href.startswith("http")]
    email = next((href.removeprefix("mailto:") for _, href in links if href.startswith("mailto:")), None)
    canonical_url = pick_primary_url(links)

    if same_as:
        payload["sameAs"] = same_as
    if email:
        payload["email"] = email
    if canonical_url:
        payload["url"] = canonical_url

    return json.dumps(payload, ensure_ascii=False)


def summarize_description(profile: Profile) -> str:
    summary = " ".join(profile.intro).strip()
    if not summary:
        summary = f"{profile.title} profile."
    if len(summary) > 180:
        return summary[:177].rstrip() + "..."
    return summary


def render_site(markdown: str, generated_at: datetime | None = None) -> str:
    profile = parse_profile(markdown)
    links = extract_links(profile)
    generated_label = (
        generated_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
        if generated_at is not None
        else "README snapshot"
    )
    description = summarize_description(profile)
    tags = extract_tags(profile)

    intro_html = "".join(f"<p>{render_inline(paragraph)}</p>" for paragraph in profile.intro)
    if not intro_html:
        intro_html = "<p>Profile content is maintained in README.md.</p>"

    tag_html = "".join(f'<span class="tag">{render_inline(tag)}</span>' for tag in tags)
    if not tag_html:
        tag_html = '<span class="tag">README-driven profile</span>'

    cta_html = ""
    for index, (label, href) in enumerate(links[:3]):
        safe_href = html.escape(href, quote=True)
        target = ' target="_blank" rel="noreferrer"' if href.startswith("http") else ""
        button_class = "button button-primary" if index == 0 else "button button-secondary"
        cta_html += f'<a class="{button_class}" href="{safe_href}"{target}>{html.escape(label)}</a>'
    if not cta_html:
        cta_html = f'<a class="button button-primary" href="{html.escape(REPO_URL, quote=True)}" target="_blank" rel="noreferrer">Repository</a>'

    nav_html = "".join(
        f'<a href="#{section.anchor}">{html.escape(section.heading)}</a>'
        for section in profile.sections
    )
    section_html = textwrap.indent(
        "\n".join(
            render_section(section, index)
            for index, section in enumerate(profile.sections, start=1)
        ),
        "        ",
    )

    page_title = f"{profile.title} | Profile"
    replacements = {
        "__PAGE_TITLE__": html.escape(page_title),
        "__TITLE__": html.escape(profile.title),
        "__DESCRIPTION__": html.escape(description, quote=True),
        "__CANONICAL_URL__": html.escape(pick_primary_url(links), quote=True),
        "__INTRO_HTML__": intro_html,
        "__TAG_HTML__": tag_html,
        "__CTA_HTML__": cta_html,
        "__GENERATED_AT__": generated_label,
        "__NAV_HTML__": nav_html,
        "__SECTION_HTML__": section_html,
        "__REPO_URL__": html.escape(REPO_URL, quote=True),
        "__STRUCTURED_DATA__": build_structured_data(profile, description, links),
    }

    output = HTML_TEMPLATE
    for token, value in replacements.items():
        output = output.replace(token, value)
    return output


def build(
    readme_path: Path = README_PATH,
    output_path: Path = OUTPUT_PATH,
    generated_at: datetime | None = None,
) -> str:
    markdown = readme_path.read_text(encoding="utf-8")
    output = render_site(markdown, generated_at=generated_at)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    return output


if __name__ == "__main__":
    build()
