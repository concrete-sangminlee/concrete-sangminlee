#!/usr/bin/env python3

from __future__ import annotations

import html
import json
import re
import textwrap
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
DOCS_DIR = ROOT / "docs"
OUTPUT_PATH = DOCS_DIR / "index.html"
OG_IMAGE_FILENAME = "og-preview.svg"
SITEMAP_FILENAME = "sitemap.xml"
ROBOTS_FILENAME = "robots.txt"
NOJEKYLL_FILENAME = ".nojekyll"
REPO_URL = "https://github.com/concrete-sangminlee/concrete-sangminlee"
SITE_URL = "https://concrete-sangminlee.github.io/"
SITE_LOCALE = "en_US"
THEME_COLOR = "#102522"
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630

AUTOLINK_RE = re.compile(r"https?://\S+|[\w.+-]+@[\w.-]+\.\w+")
LINKED_IMAGE_RE = re.compile(r"\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_TOKEN_RE = re.compile(
    r"(\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*.+?\*\*|__.+?__|\*[^*\n]+\*|_[^_\n]+_)",
    re.DOTALL,
)
LINK_ITEM_RE = re.compile(r"^(?P<label>[^:]+):\s*(?P<target>\S.+)$")
ORDERED_ITEM_RE = re.compile(r"^\d+\.\s+(?P<item>.+)$")


@dataclass
class Block:
    kind: str
    items: list[str]
    table_data: list[list[str]] | None = None


@dataclass
class Section:
    heading: str
    anchor: str
    blocks: list[Block]


@dataclass
class Profile:
    title: str
    intro: list[str]
    intro_blocks: list[Block]
    sections: list[Section]


@dataclass
class Link:
    label: str
    href: str


@dataclass
class MetricCard:
    value: str
    label: str
    detail: str


@dataclass
class PreviewCard:
    heading: str
    anchor: str
    eyebrow: str
    summary: str
    meta: str


@dataclass
class SiteArtifacts:
    html: str
    og_image: str
    sitemap: str
    robots: str
    nojekyll: str
    canonical_url: str


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>__PAGE_TITLE__</title>
    <meta name="description" content="__DESCRIPTION__" />
    <meta name="keywords" content="__KEYWORDS__" />
    <meta name="author" content="__TITLE__" />
    <meta name="generator" content="build_readme_page.py" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <meta name="theme-color" content="__THEME_COLOR__" />
    <meta property="og:title" content="__PAGE_TITLE__" />
    <meta property="og:description" content="__DESCRIPTION__" />
    <meta property="og:type" content="profile" />
    <meta property="og:url" content="__CANONICAL_URL__" />
    <meta property="og:site_name" content="__TITLE__" />
    <meta property="og:locale" content="__SITE_LOCALE__" />
    <meta property="og:image" content="__OG_IMAGE_URL__" />
    <meta property="og:image:type" content="image/svg+xml" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="__OG_IMAGE_ALT__" />
__MODIFIED_META__
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="__PAGE_TITLE__" />
    <meta name="twitter:description" content="__DESCRIPTION__" />
    <meta name="twitter:image" content="__OG_IMAGE_URL__" />
    <meta name="twitter:image:alt" content="__OG_IMAGE_ALT__" />
    <link rel="canonical" href="__CANONICAL_URL__" />
    <link rel="sitemap" type="application/xml" href="__SITEMAP_URL__" />
    <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
    <link rel="dns-prefetch" href="https://fonts.gstatic.com" />
    <link rel="dns-prefetch" href="https://img.shields.io" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <style>
      :root {
        color-scheme: light dark;
        --bg: #f6efe3;
        --bg-alt: #fcf8f2;
        --surface: rgba(255, 251, 245, 0.88);
        --surface-strong: rgba(255, 255, 255, 0.96);
        --surface-dark: #132522;
        --ink: #102522;
        --muted: #556762;
        --line: rgba(16, 37, 34, 0.12);
        --accent: #ca5a3f;
        --accent-soft: rgba(202, 90, 63, 0.14);
        --teal: #0f766e;
        --teal-soft: rgba(15, 118, 110, 0.14);
        --gold: #d1a654;
        --shadow-lg: 0 24px 72px rgba(16, 37, 34, 0.12);
        --shadow-md: 0 16px 42px rgba(16, 37, 34, 0.08);
        --ink-003: rgba(16, 37, 34, 0.03);
        --ink-004: rgba(16, 37, 34, 0.04);
        --ink-005: rgba(16, 37, 34, 0.05);
        --ink-008: rgba(16, 37, 34, 0.08);
        --ink-010: rgba(16, 37, 34, 0.10);
        --ink-016: rgba(16, 37, 34, 0.16);
        --ink-018: rgba(16, 37, 34, 0.18);
        --ink-028: rgba(16, 37, 34, 0.28);
        --white-008: rgba(255, 255, 255, 0.08);
        --white-076: rgba(255, 255, 255, 0.76);
        --white-078: rgba(255, 255, 255, 0.78);
        --white-084: rgba(255, 255, 255, 0.84);
        --white-088: rgba(255, 255, 255, 0.88);
        --white-090: rgba(255, 255, 255, 0.90);
        --white-092: rgba(255, 255, 255, 0.92);
        --hero-main-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 252, 247, 0.72));
        --preview-card-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 253, 249, 0.72));
        --body-bg:
          radial-gradient(circle at top left, rgba(202, 90, 63, 0.12), transparent 28%),
          radial-gradient(circle at 88% 8%, rgba(15, 118, 110, 0.10), transparent 26%),
          linear-gradient(180deg, #f6efe3 0%, #fcf8f2 54%, #f6efe3 100%);
        --grid-line: rgba(16, 37, 34, 0.05);
        --hero-after-bg: rgba(15, 118, 110, 0.06);
      }

      @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) {
          --bg: #0f1c1a;
          --bg-alt: #132522;
          --surface: rgba(26, 51, 48, 0.88);
          --surface-strong: rgba(30, 58, 54, 0.96);
          --surface-dark: #0a1412;
          --ink: #f8f2ea;
          --muted: #8fa69e;
          --line: rgba(248, 242, 234, 0.12);
          --accent: #e07050;
          --accent-soft: rgba(224, 112, 80, 0.16);
          --teal: #2dd4bf;
          --teal-soft: rgba(45, 212, 191, 0.14);
          --gold: #d1a654;
          --shadow-lg: 0 24px 72px rgba(0, 0, 0, 0.32);
          --shadow-md: 0 16px 42px rgba(0, 0, 0, 0.22);
          --ink-003: rgba(248, 242, 234, 0.03);
          --ink-004: rgba(248, 242, 234, 0.04);
          --ink-005: rgba(248, 242, 234, 0.05);
          --ink-008: rgba(248, 242, 234, 0.08);
          --ink-010: rgba(248, 242, 234, 0.10);
          --ink-016: rgba(248, 242, 234, 0.16);
          --ink-018: rgba(248, 242, 234, 0.18);
          --ink-028: rgba(248, 242, 234, 0.28);
          --white-008: rgba(26, 51, 48, 0.08);
          --white-076: rgba(26, 51, 48, 0.76);
          --white-078: rgba(26, 51, 48, 0.78);
          --white-084: rgba(26, 51, 48, 0.84);
          --white-088: rgba(26, 51, 48, 0.88);
          --white-090: rgba(26, 51, 48, 0.90);
          --white-092: rgba(26, 51, 48, 0.92);
          --hero-main-bg: linear-gradient(180deg, rgba(26, 51, 48, 0.9), rgba(20, 42, 38, 0.72));
          --preview-card-bg: linear-gradient(180deg, rgba(26, 51, 48, 0.9), rgba(20, 42, 38, 0.72));
          --body-bg:
            radial-gradient(circle at top left, rgba(224, 112, 80, 0.12), transparent 28%),
            radial-gradient(circle at 88% 8%, rgba(45, 212, 191, 0.10), transparent 26%),
            linear-gradient(180deg, #0a1412 0%, #0f1c1a 54%, #0a1412 100%);
          --grid-line: rgba(248, 242, 234, 0.05);
          --hero-after-bg: rgba(45, 212, 191, 0.06);
          --section-links-bg: linear-gradient(180deg, rgba(22, 46, 42, 0.94), rgba(18, 38, 34, 0.76));
          --section-focus-bg:
            radial-gradient(circle at top right, rgba(45, 212, 191, 0.08), transparent 38%),
            linear-gradient(180deg, rgba(22, 46, 42, 0.94), rgba(18, 38, 34, 0.78));
          --section-collab-bg:
            radial-gradient(circle at top left, rgba(224, 112, 80, 0.10), transparent 34%),
            linear-gradient(180deg, rgba(22, 46, 42, 0.94), rgba(18, 38, 34, 0.74));
        }
      }

      :root[data-theme="dark"] {
        --bg: #0f1c1a;
        --bg-alt: #132522;
        --surface: rgba(26, 51, 48, 0.88);
        --surface-strong: rgba(30, 58, 54, 0.96);
        --surface-dark: #0a1412;
        --ink: #f8f2ea;
        --muted: #8fa69e;
        --line: rgba(248, 242, 234, 0.12);
        --accent: #e07050;
        --accent-soft: rgba(224, 112, 80, 0.16);
        --teal: #2dd4bf;
        --teal-soft: rgba(45, 212, 191, 0.14);
        --gold: #d1a654;
        --shadow-lg: 0 24px 72px rgba(0, 0, 0, 0.32);
        --shadow-md: 0 16px 42px rgba(0, 0, 0, 0.22);
        --ink-003: rgba(248, 242, 234, 0.03);
        --ink-004: rgba(248, 242, 234, 0.04);
        --ink-005: rgba(248, 242, 234, 0.05);
        --ink-008: rgba(248, 242, 234, 0.08);
        --ink-010: rgba(248, 242, 234, 0.10);
        --ink-016: rgba(248, 242, 234, 0.16);
        --ink-018: rgba(248, 242, 234, 0.18);
        --ink-028: rgba(248, 242, 234, 0.28);
        --white-008: rgba(26, 51, 48, 0.08);
        --white-076: rgba(26, 51, 48, 0.76);
        --white-078: rgba(26, 51, 48, 0.78);
        --white-084: rgba(26, 51, 48, 0.84);
        --white-088: rgba(26, 51, 48, 0.88);
        --white-090: rgba(26, 51, 48, 0.90);
        --white-092: rgba(26, 51, 48, 0.92);
        --hero-main-bg: linear-gradient(180deg, rgba(26, 51, 48, 0.9), rgba(20, 42, 38, 0.72));
        --preview-card-bg: linear-gradient(180deg, rgba(26, 51, 48, 0.9), rgba(20, 42, 38, 0.72));
        --body-bg:
          radial-gradient(circle at top left, rgba(224, 112, 80, 0.12), transparent 28%),
          radial-gradient(circle at 88% 8%, rgba(45, 212, 191, 0.10), transparent 26%),
          linear-gradient(180deg, #0a1412 0%, #0f1c1a 54%, #0a1412 100%);
        --grid-line: rgba(248, 242, 234, 0.05);
        --hero-after-bg: rgba(45, 212, 191, 0.06);
        --section-links-bg: linear-gradient(180deg, rgba(22, 46, 42, 0.94), rgba(18, 38, 34, 0.76));
        --section-focus-bg:
          radial-gradient(circle at top right, rgba(45, 212, 191, 0.08), transparent 38%),
          linear-gradient(180deg, rgba(22, 46, 42, 0.94), rgba(18, 38, 34, 0.78));
        --section-collab-bg:
          radial-gradient(circle at top left, rgba(224, 112, 80, 0.10), transparent 34%),
          linear-gradient(180deg, rgba(22, 46, 42, 0.94), rgba(18, 38, 34, 0.74));
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
        background: var(--body-bg);
      }

      body::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.34;
        background-image:
          linear-gradient(var(--grid-line) 1px, transparent 1px),
          linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
        background-size: 28px 28px;
        mask-image: linear-gradient(180deg, rgba(0, 0, 0, 1), transparent 92%);
      }

      a {
        color: inherit;
      }

      code {
        padding: 0.12rem 0.36rem;
        border-radius: 0.5rem;
        background: var(--ink-008);
        font-family: "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace;
        font-size: 0.92em;
      }

      img {
        max-width: 100%;
        height: auto;
      }

      .page {
        position: relative;
        width: min(1160px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 28px 0 56px;
      }

      .hero {
        display: grid;
        grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.95fr);
        gap: 22px;
        align-items: stretch;
      }

      .hero-main,
      .hero-side,
      .preview-card,
      .section-card {
        animation: rise-in 720ms cubic-bezier(0.16, 1, 0.3, 1) both;
      }

      .hero-main,
      .hero-side,
      .section-card {
        border: 1px solid var(--line);
        border-radius: 32px;
        box-shadow: var(--shadow-lg);
      }

      .hero-main {
        position: relative;
        overflow: hidden;
        padding: 36px;
        background:
          radial-gradient(circle at 8% 0%, var(--accent-soft), transparent 26%),
          var(--hero-main-bg);
        backdrop-filter: blur(18px);
      }

      .hero-main::after {
        content: "";
        position: absolute;
        inset: auto -60px -60px auto;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: var(--hero-after-bg);
      }

      .hero-side {
        padding: 26px;
        background:
          linear-gradient(180deg, #152926 0%, #0d1a18 100%);
        color: #f8f2ea;
        overflow: hidden;
      }

      .eyebrow,
      .section-intro p,
      .preview-kicker,
      .section-label,
      .footer-note {
        margin: 0;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }

      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        color: var(--muted);
      }

      .eyebrow::before,
      .section-intro p::before {
        content: "";
        width: 34px;
        height: 1px;
        background: var(--ink-028);
      }

      .section-intro p {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        color: var(--accent);
      }

      .hero-title {
        margin: 18px 0 0;
        max-width: 10ch;
        font-family: "Fraunces", serif;
        font-size: clamp(3.1rem, 7vw, 5.8rem);
        line-height: 0.92;
        letter-spacing: -0.06em;
      }

      .hero-copy {
        position: relative;
        z-index: 1;
      }

      .hero-intro {
        max-width: 54rem;
        margin-top: 18px;
      }

      .hero-intro p {
        margin: 0 0 14px;
        color: var(--muted);
        font-size: 1.03rem;
        line-height: 1.85;
      }

      .media-group {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        margin: 0 0 16px;
      }

      .media-group-badges {
        gap: 10px;
      }

      .media-group-stats {
        align-items: stretch;
      }

      .media-group-banner,
      .media-group-snake {
        display: grid;
      }

      .image-link,
      .image-link:hover,
      .image-link:focus-visible {
        display: inline-flex;
        text-decoration: none;
        transform: none;
      }

      .markdown-image {
        display: block;
        border-radius: 18px;
        border: 1px solid var(--ink-008);
        background: var(--white-090);
      }

      .markdown-image-badge {
        border: none;
        border-radius: 999px;
        background: transparent;
      }

      .markdown-image-stats {
        width: min(100%, 420px);
        box-shadow: var(--shadow-md);
      }

      .markdown-image-banner,
      .markdown-image-snake {
        width: 100%;
        box-shadow: var(--shadow-md);
      }

      .tag-list,
      .cta-row,
      .nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .tag-list {
        margin-top: 24px;
      }

      .tag {
        display: inline-flex;
        align-items: center;
        min-height: 38px;
        padding: 0 14px;
        border-radius: 999px;
        border: 1px solid var(--ink-008);
        background: var(--white-084);
        font-size: 0.92rem;
        font-weight: 700;
      }

      .cta-row {
        margin-top: 24px;
      }

      .button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 48px;
        padding: 0 18px;
        border-radius: 999px;
        border: 1px solid transparent;
        text-decoration: none;
        font-weight: 800;
        transition: transform 160ms ease, box-shadow 160ms ease, background-color 160ms ease;
      }

      .button:hover,
      .button:focus-visible,
      .preview-card:hover,
      .preview-card:focus-visible,
      .nav a:hover,
      .nav a:focus-visible,
      .link-card:hover,
      .link-card:focus-visible {
        transform: translateY(-2px);
      }

      .button-primary {
        background: var(--ink);
        color: #f8f2ea;
        box-shadow: 0 16px 30px var(--ink-016);
      }

      .button-secondary {
        background: var(--white-078);
        border-color: var(--ink-010);
      }

      .hero-side > * {
        position: relative;
        z-index: 1;
      }

      .hero-side::after {
        content: "";
        position: absolute;
        inset: auto -50px -40px auto;
        width: 160px;
        height: 160px;
        border-radius: 999px;
        background: var(--white-008);
      }

      .hero-side .eyebrow {
        color: rgba(248, 242, 234, 0.72);
      }

      .hero-side .eyebrow::before {
        background: rgba(248, 242, 234, 0.32);
      }

      .hero-side h2 {
        margin: 16px 0 0;
        font-family: "Fraunces", serif;
        font-size: 2.05rem;
        line-height: 1.02;
        letter-spacing: -0.04em;
      }

      .hero-side p {
        margin: 14px 0 0;
        color: rgba(248, 242, 234, 0.76);
        line-height: 1.75;
      }

      .metric-grid {
        display: grid;
        gap: 12px;
        margin-top: 22px;
      }

      .metric-card {
        padding: 16px 18px;
        border-radius: 22px;
        background: var(--white-008);
      }

      .metric-card strong,
      .metric-card span,
      .metric-card small {
        display: block;
      }

      .metric-card strong {
        font-family: "Fraunces", serif;
        font-size: 2rem;
        line-height: 1;
        letter-spacing: -0.04em;
      }

      .metric-card span {
        margin-top: 6px;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .metric-card small {
        margin-top: 8px;
        color: rgba(248, 242, 234, 0.72);
        line-height: 1.55;
      }

      .preview-wrap {
        margin-top: 22px;
      }

      .preview-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin-top: 16px;
      }

      .preview-card {
        display: grid;
        gap: 12px;
        min-height: 100%;
        padding: 22px;
        border: 1px solid var(--line);
        border-radius: 28px;
        background: var(--preview-card-bg);
        box-shadow: var(--shadow-md);
        text-decoration: none;
      }

      .preview-card:nth-child(2),
      .section-card:nth-child(2) {
        animation-delay: 90ms;
      }

      .preview-card:nth-child(3),
      .section-card:nth-child(3) {
        animation-delay: 140ms;
      }

      .preview-card strong {
        font-family: "Fraunces", serif;
        font-size: 1.5rem;
        line-height: 1.08;
        letter-spacing: -0.03em;
      }

      .preview-card p {
        margin: 0;
        color: var(--muted);
        line-height: 1.72;
      }

      .preview-meta {
        color: var(--ink);
        font-size: 0.84rem;
        font-weight: 700;
      }

      .preview-kicker {
        color: var(--accent);
      }

      .nav-wrap {
        margin-top: 22px;
      }

      .nav {
        padding: 0;
      }

      .nav a {
        display: inline-flex;
        align-items: center;
        min-height: 42px;
        padding: 0 16px;
        border-radius: 999px;
        border: 1px solid var(--ink-010);
        background: var(--white-076);
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

      .section-card {
        grid-column: span 6;
        padding: 26px;
        background: var(--surface);
        backdrop-filter: blur(12px);
      }

      .section-card.section-span-12 {
        grid-column: span 12;
      }

      .section-card.section-span-7 {
        grid-column: span 7;
      }

      .section-card.section-span-5 {
        grid-column: span 5;
      }

      .section-card.section-links {
        background: var(--section-links-bg, linear-gradient(180deg, rgba(255, 250, 244, 0.94), rgba(255, 252, 248, 0.76)));
      }

      .section-card.section-focus {
        background: var(--section-focus-bg,
          radial-gradient(circle at top right, rgba(15, 118, 110, 0.1), transparent 38%),
          linear-gradient(180deg, rgba(255, 253, 249, 0.94), rgba(255, 250, 245, 0.78)));
      }

      .section-card.section-collaboration {
        background: var(--section-collab-bg,
          radial-gradient(circle at top left, rgba(202, 90, 63, 0.12), transparent 34%),
          linear-gradient(180deg, rgba(255, 252, 247, 0.94), rgba(255, 249, 243, 0.74)));
      }

      .section-label {
        color: var(--accent);
      }

      .section-title {
        margin: 10px 0 0;
        font-family: "Fraunces", serif;
        font-size: 2rem;
        line-height: 1.05;
        letter-spacing: -0.04em;
      }

      .section-body {
        margin-top: 18px;
      }

      .section-body p,
      .section-body li,
      .section-body blockquote {
        color: var(--muted);
        line-height: 1.8;
      }

      .section-body p {
        margin: 0 0 12px;
      }

      .section-body .media-group:last-child,
      .hero-intro .media-group:last-child {
        margin-bottom: 0;
      }

      .subheading {
        margin: 20px 0 10px;
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
      }

      .signal-grid,
      .stack-grid,
      .link-grid,
      .timeline-list,
      .detail-list {
        margin: 0;
        padding: 0;
        list-style: none;
      }

      .signal-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
      }

      .signal-grid li {
        min-height: 100%;
        padding: 16px;
        border-radius: 22px;
        border: 1px solid var(--ink-008);
        background: var(--white-092);
      }

      .signal-grid strong {
        display: block;
        margin-bottom: 10px;
        color: var(--teal);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      .stack-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
      }

      .stack-grid li {
        min-height: 100%;
        padding: 18px;
        border-radius: 22px;
        border: 1px solid var(--ink-008);
        background: var(--white-090);
        color: var(--ink);
        font-weight: 700;
      }

      .detail-list {
        display: grid;
        gap: 10px;
      }

      .detail-list li {
        position: relative;
        padding-left: 18px;
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

      .timeline-list {
        display: grid;
        gap: 14px;
      }

      .timeline-item {
        display: grid;
        grid-template-columns: 54px minmax(0, 1fr);
        gap: 14px;
        align-items: start;
        padding: 16px;
        border-radius: 24px;
        background: var(--white-088);
        border: 1px solid var(--ink-008);
      }

      .timeline-item strong {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      .timeline-item span {
        color: var(--muted);
        line-height: 1.7;
      }

      .quote-block {
        margin: 18px 0;
        padding: 20px 22px;
        border-left: 4px solid var(--accent);
        border-radius: 0 20px 20px 0;
        background: var(--accent-soft);
      }

      .quote-block p {
        margin: 0;
        color: var(--ink);
        font-size: 1.02rem;
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
        background: linear-gradient(180deg, #172b27 0%, #101b18 100%);
        color: #f8f4ee;
        text-decoration: none;
        box-shadow: 0 22px 46px var(--ink-018);
      }

      .link-card strong {
        font-size: 1.12rem;
      }

      .link-card span {
        color: rgba(248, 244, 238, 0.72);
        line-height: 1.6;
      }

      .link-card small {
        color: #f3c8bc;
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
        align-items: center;
        margin-top: 24px;
        padding: 18px 6px 0;
        color: var(--muted);
        font-size: 0.92rem;
      }

      .footer a {
        color: var(--ink);
        font-weight: 700;
        text-decoration: none;
      }

      .footer-note {
        color: var(--accent);
      }

      .skip-link {
        position: absolute;
        top: -48px;
        left: 8px;
        z-index: 200;
        padding: 10px 16px;
        background: var(--ink);
        color: var(--bg);
        text-decoration: none;
        font-weight: 800;
        border-radius: 8px;
        transition: top 160ms ease;
      }

      .skip-link:focus {
        top: 8px;
      }

      :focus-visible {
        outline: 2px solid var(--accent);
        outline-offset: 3px;
        border-radius: 4px;
      }

      .theme-toggle:focus-visible,
      .skip-link:focus-visible {
        outline-offset: 2px;
      }

      .theme-toggle {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 100;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: var(--surface-strong);
        color: var(--ink);
        cursor: pointer;
        box-shadow: var(--shadow-md);
        backdrop-filter: blur(12px);
        transition: transform 160ms ease, box-shadow 160ms ease;
      }

      .theme-toggle:hover,
      .theme-toggle:focus-visible {
        transform: translateY(-2px);
      }

      .theme-toggle-sun { display: none; }
      .theme-toggle-moon { display: block; }

      @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) .theme-toggle-sun { display: block; }
        :root:not([data-theme="light"]) .theme-toggle-moon { display: none; }
      }
      :root[data-theme="dark"] .theme-toggle-sun { display: block; }
      :root[data-theme="dark"] .theme-toggle-moon { display: none; }
      :root[data-theme="light"] .theme-toggle-sun { display: none; }
      :root[data-theme="light"] .theme-toggle-moon { display: block; }

      .table-wrap {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin: 18px 0;
        border-radius: 22px;
        border: 1px solid var(--line);
        background: var(--white-088);
      }

      .md-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.94rem;
        line-height: 1.7;
      }

      .md-table th,
      .md-table td {
        padding: 12px 18px;
        text-align: left;
        border-bottom: 1px solid var(--line);
      }

      .md-table th {
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        background: var(--ink-004);
        white-space: nowrap;
      }

      .md-table tbody tr:last-child td {
        border-bottom: none;
      }

      .md-table tbody tr:hover {
        background: var(--ink-003);
      }

      .md-table td:first-child {
        font-weight: 700;
        white-space: nowrap;
      }

      @keyframes rise-in {
        from {
          opacity: 0;
          transform: translateY(22px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @media (max-width: 1024px) {
        .hero {
          grid-template-columns: 1fr;
        }

        .preview-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }

      @media (max-width: 940px) {
        .section-card,
        .section-card.section-span-12,
        .section-card.section-span-7,
        .section-card.section-span-5 {
          grid-column: span 12;
        }
      }

      @media (max-width: 680px) {
        .page {
          width: min(100vw - 18px, 1160px);
          padding: 14px 0 34px;
        }

        .hero-main,
        .hero-side,
        .section-card,
        .preview-card {
          padding: 20px;
          border-radius: 24px;
        }

        .preview-grid {
          grid-template-columns: 1fr;
        }

        .hero-title {
          font-size: clamp(2.7rem, 16vw, 4.4rem);
        }

        .section-title {
          font-size: 1.72rem;
        }

        .timeline-item {
          grid-template-columns: 1fr;
        }

        .md-table th,
        .md-table td {
          padding: 10px 14px;
          font-size: 0.88rem;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
      }

      @media print {
        *, *::before, *::after {
          animation: none !important;
          transition: none !important;
        }

        body {
          background: #fff;
          color: #000;
          font-size: 11pt;
          line-height: 1.5;
        }

        body::before { display: none; }

        .page { width: 100%; padding: 0; }

        .hero { grid-template-columns: 1fr; }

        .hero-main, .hero-side, .section-card, .preview-card {
          backdrop-filter: none;
          box-shadow: none;
          background: #fff;
          border: 1px solid #ccc;
        }

        .hero-main::after, .hero-side::after { display: none; }

        .hero-title { font-size: 28pt; }
        .section-title { font-size: 16pt; }

        .hero-side {
          background: #f5f5f5;
          color: #000;
        }
        .hero-side .eyebrow { color: #666; }
        .hero-side .eyebrow::before { background: #999; }
        .hero-side p { color: #333; }
        .hero-side h2 { color: #000; }
        .metric-card { background: #eee; color: #000; }
        .metric-card small { color: #555; }

        .content-grid { display: block; }
        .section-card,
        .section-card.section-span-12,
        .section-card.section-span-7,
        .section-card.section-span-5 {
          margin-bottom: 16pt;
        }

        .preview-grid { grid-template-columns: 1fr; }

        .link-card {
          background: #f5f5f5;
          color: #000;
          box-shadow: none;
        }
        .link-card span { color: #333; }
        .link-card small { color: #666; }

        a[href^="http"]::after {
          content: " (" attr(href) ")";
          font-size: 0.8em;
          font-weight: 400;
          color: #666;
          word-break: break-all;
        }
        .image-link::after, .nav a::after, .button::after,
        .preview-card::after, .link-card a::after { content: none; }

        .nav-wrap, .preview-wrap, .cta-row, .tag-list, .theme-toggle {
          display: none;
        }

        .section-card, img, h1, h2, h3 {
          page-break-inside: avoid;
          break-inside: avoid;
        }
        h1, h2, h3 {
          page-break-after: avoid;
          break-after: avoid;
        }
      }
    </style>
    <script>(function(){var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);})()</script>
    <script type="application/ld+json">__STRUCTURED_DATA__</script>
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <main class="page" id="main-content">
      <section class="hero">
        <div class="hero-main">
          <div class="hero-copy">
            <p class="eyebrow">Academic Researcher</p>
            <h1 class="hero-title">__TITLE__</h1>
            <div class="hero-intro">__INTRO_HTML__</div>
            <div class="tag-list">__TAG_HTML__</div>
            <div class="cta-row">__CTA_HTML__</div>
          </div>
        </div>
        <aside class="hero-side">
          <p class="eyebrow">Research Profile</p>
          <h2>Selected outputs, active directions, and direct paths for collaboration.</h2>
          <p>
            The page turns the repository profile into a research-facing overview with focus areas,
            recent highlights, publications, projects, and verifiable links for deeper context.
          </p>
          <div class="metric-grid">__METRIC_HTML__</div>
        </aside>
      </section>

__PREVIEW_SECTION__

__NAV_SECTION__

__CONTENT_SECTION__

      <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Toggle dark mode">
        <svg class="theme-toggle-sun" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        <svg class="theme-toggle-moon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
      <footer class="footer">
        <span>Maintained in <a href="__REPO_URL__">the profile repository</a> and published as static output.</span>__BUILD_STAMP_HTML__
      </footer>
    </main>
    <script>(function(){var b=document.getElementById('theme-toggle');b&&b.addEventListener('click',function(){var r=document.documentElement,c=r.getAttribute('data-theme'),d=c==='dark'||(c!=='light'&&window.matchMedia('(prefers-color-scheme:dark)').matches);var n=d?'light':'dark';r.setAttribute('data-theme',n);localStorage.setItem('theme',n);});})()</script>
  </body>
</html>
"""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def strip_markdown(text: str) -> str:
    output = LINKED_IMAGE_RE.sub(lambda match: match.group(1), text)
    output = IMAGE_RE.sub(lambda match: match.group(1), output)
    output = INLINE_LINK_RE.sub(lambda match: match.group(1), output)
    output = re.sub(r"`([^`]+)`", r"\1", output)
    output = re.sub(r"(\*\*|__)(.+?)\1", r"\2", output)
    output = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", output)
    output = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", output)
    return " ".join(output.split())


def is_media_only_text(text: str) -> bool:
    stripped = LINKED_IMAGE_RE.sub("", text)
    stripped = IMAGE_RE.sub("", stripped)
    return not stripped.strip()


def classify_image_kind(src: str, alt: str) -> str:
    lower_src = src.lower()
    lower_alt = alt.lower()
    if "shields.io" in lower_src:
        return "badge"
    if "github-readme-stats" in lower_src or "streak-stats" in lower_src:
        return "stats"
    if "snake" in lower_src or "snake" in lower_alt:
        return "snake"
    if "banner" in lower_src or "banner" in lower_alt:
        return "banner"
    return "content"


def collect_media_kinds(text: str) -> list[str]:
    kinds: list[str] = []

    def collect_linked(match: re.Match[str]) -> str:
        kinds.append(classify_image_kind(match.group(2), match.group(1)))
        return " "

    intermediate = LINKED_IMAGE_RE.sub(collect_linked, text)

    def collect_image(match: re.Match[str]) -> str:
        kinds.append(classify_image_kind(match.group(2), match.group(1)))
        return " "

    IMAGE_RE.sub(collect_image, intermediate)
    return kinds


def media_group_class(text: str) -> str:
    kinds = collect_media_kinds(text)
    classes = ["media-group"]
    if kinds and all(kind == "badge" for kind in kinds):
        classes.append("media-group-badges")
    elif "stats" in kinds:
        classes.append("media-group-stats")
    elif "banner" in kinds:
        classes.append("media-group-banner")
    elif "snake" in kinds:
        classes.append("media-group-snake")
    return " ".join(classes)


def truncate(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    if limit <= 3:
        return cleaned[:limit]
    return cleaned[: limit - 3].rstrip() + "..."


def parse_blocks(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    bullets: list[str] = []
    ordered: list[str] = []
    quote: list[str] = []
    html_block: list[str] = []
    table_rows: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(Block(kind="paragraph", items=[" ".join(paragraph)]))
            paragraph.clear()

    def flush_bullets() -> None:
        if bullets:
            blocks.append(Block(kind="list", items=bullets.copy()))
            bullets.clear()

    def flush_ordered() -> None:
        if ordered:
            blocks.append(Block(kind="ordered_list", items=ordered.copy()))
            ordered.clear()

    def flush_quote() -> None:
        if quote:
            blocks.append(Block(kind="quote", items=[" ".join(quote)]))
            quote.clear()

    def flush_html() -> None:
        if html_block:
            blocks.append(Block(kind="html", items=["\n".join(html_block)]))
            html_block.clear()

    def flush_table() -> None:
        if table_rows:
            rows = [r.strip().strip("|").split("|") for r in table_rows]
            rows = [[c.strip() for c in r] for r in rows]
            header = rows[0] if rows else []
            aligns: list[str] = []
            if len(rows) > 1:
                for cell in rows[1]:
                    cell = cell.strip()
                    if cell.startswith(":") and cell.endswith(":"):
                        aligns.append("center")
                    elif cell.endswith(":"):
                        aligns.append("right")
                    else:
                        aligns.append("left")
            data = [r for i, r in enumerate(rows) if i >= 2] if len(rows) > 1 else []

            def align_attr(col_idx: int) -> str:
                if col_idx < len(aligns) and aligns[col_idx] != "left":
                    return f' style="text-align:{aligns[col_idx]}"'
                return ""

            head_html = "".join(
                f'<th scope="col"{align_attr(i)}>{render_inline(c)}</th>'
                for i, c in enumerate(header)
            )
            body_html = "".join(
                "<tr>"
                + "".join(
                    (f'<td scope="row"{align_attr(i)}>{render_inline(c)}</td>'
                     if i == 0 else
                     f"<td{align_attr(i)}>{render_inline(c)}</td>")
                    for i, c in enumerate(r)
                )
                + "</tr>"
                for r in data
            )
            blocks.append(Block(
                kind="html",
                items=[
                    f'<div class="table-wrap"><table class="md-table"><thead><tr>{head_html}</tr></thead>'
                    f"<tbody>{body_html}</tbody></table></div>"
                ],
                table_data=[header, *data],
            ))
            table_rows.clear()

    def flush_all() -> None:
        flush_paragraph()
        flush_bullets()
        flush_ordered()
        flush_quote()
        flush_html()
        flush_table()

    for line in [*lines, ""]:
        stripped = line.strip()
        if stripped in {"---", "***", "___"}:
            flush_all()
            continue
        if not stripped:
            flush_all()
            continue
        if stripped.startswith("### "):
            flush_all()
            blocks.append(Block(kind="subheading", items=[stripped[4:].strip()]))
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            flush_bullets()
            flush_ordered()
            flush_html()
            quote.append(stripped[2:].strip())
            continue
        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            flush_ordered()
            flush_quote()
            flush_html()
            bullets.append(stripped[2:].strip())
            continue
        ordered_match = ORDERED_ITEM_RE.match(stripped)
        if ordered_match:
            flush_paragraph()
            flush_bullets()
            flush_quote()
            flush_html()
            ordered.append(ordered_match.group("item").strip())
            continue

        if stripped.startswith("|") and "|" in stripped[1:]:
            flush_paragraph()
            flush_bullets()
            flush_ordered()
            flush_quote()
            flush_html()
            table_rows.append(stripped)
            continue

        flush_table()

        if stripped.startswith("<"):
            flush_paragraph()
            flush_bullets()
            flush_ordered()
            flush_quote()
            html_block.append(stripped)
            continue

        flush_bullets()
        flush_ordered()
        flush_quote()
        flush_html()
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
    intro = [
        block.items[0]
        for block in intro_blocks
        if block.kind == "paragraph" and not is_media_only_text(block.items[0])
    ]
    return Profile(title=title, intro=intro, intro_blocks=intro_blocks, sections=sections)


def normalize_href(target: str) -> str:
    stripped = target.strip()
    if stripped.startswith(("http://", "https://", "mailto:")):
        return stripped
    if "@" in stripped and " " not in stripped:
        return f"mailto:{stripped}"
    return stripped


def parse_link_item(item: str) -> Link | None:
    markdown_match = INLINE_LINK_RE.fullmatch(item.strip())
    if markdown_match:
        label, target = markdown_match.groups()
        return Link(label=label, href=normalize_href(target))

    match = LINK_ITEM_RE.match(item)
    if match:
        return Link(
            label=match.group("label").strip(),
            href=normalize_href(match.group("target").strip()),
        )

    href = normalize_href(item)
    if href.startswith(("http://", "https://", "mailto:")):
        label = href.removeprefix("mailto:").split("/")[-1] or "Link"
        return Link(label=label, href=href)
    return None


def is_link_section(section: Section) -> bool:
    heading = section.heading.lower()
    return any(token in heading for token in ("link", "contact", "connect"))


def extract_links(profile: Profile) -> list[Link]:
    links: list[Link] = []
    seen: set[str] = set()

    def add(link: Link | None) -> None:
        if link and link.href not in seen:
            seen.add(link.href)
            links.append(link)

    for block in profile.intro_blocks:
        for item in block.items:
            for match in LINKED_IMAGE_RE.finditer(item):
                alt, _src, target = match.groups()
                add(Link(label=strip_markdown(alt).strip() or "Link", href=normalize_href(target)))

    for section in profile.sections:
        if not is_link_section(section):
            continue
        for block in section.blocks:
            if block.kind not in {"list", "ordered_list"}:
                continue
            for item in block.items:
                add(parse_link_item(item))
    return links


def build_cta_priority(label: str) -> tuple[int, str]:
    lower = label.lower()
    priority = [
        "profile",
        "site",
        "homepage",
        "portfolio",
        "github",
        "scholar",
        "linkedin",
        "orcid",
        "email",
    ]
    for index, token in enumerate(priority):
        if token in lower:
            return index, lower
    return len(priority), lower


def pick_primary_url(links: list[Link]) -> str:
    preferred_tokens = ("profile", "site", "homepage", "portfolio")
    for link in links:
        lower = link.label.lower()
        if any(token in lower for token in preferred_tokens) and link.href.startswith("http"):
            return link.href
    for link in links:
        if link.href.startswith("http"):
            return link.href
    return SITE_URL


def describe_link(href: str) -> str:
    if href.startswith("mailto:"):
        return href.removeprefix("mailto:")
    return href.removeprefix("https://").removeprefix("http://").rstrip("/")


def collect_focus_items(profile: Profile, limit: int = 6) -> list[str]:
    keyword_groups = (
        ("research area", "research areas", "focus", "theme", "interest", "expertise"),
        ("collaboration", "approach", "services"),
        ("research",),
    )

    for keywords in keyword_groups:
        items: list[str] = []
        for section in profile.sections:
            heading = section.heading.lower()
            if not any(token in heading for token in keywords):
                continue
            for block in section.blocks:
                if block.kind in {"list", "ordered_list"}:
                    items.extend(block.items)
        if items:
            return items[:limit]

    for section in profile.sections:
        if is_link_section(section):
            continue
        for block in section.blocks:
            if block.kind in {"list", "ordered_list"}:
                return block.items[:limit]
    return []


def compact_tag(text: str, limit: int = 44) -> str:
    cleaned = strip_markdown(text).strip().rstrip(".")
    if len(cleaned) <= limit:
        return cleaned

    for delimiter in (";", ",", ":", " with ", " under ", " using ", " tailored to "):
        if delimiter not in cleaned:
            continue
        candidate = cleaned.split(delimiter, 1)[0].strip()
        if 12 <= len(candidate) <= limit:
            return candidate

    words = cleaned.split()
    for word_limit in (7, 6, 5):
        candidate = " ".join(words[:word_limit]).strip()
        if len(candidate) >= 18:
            return truncate(candidate, limit)

    return truncate(cleaned, limit)


def extract_tags(profile: Profile, limit: int = 5) -> list[str]:
    tags: list[str] = []
    for item in collect_focus_items(profile, limit=limit + 2):
        compacted = compact_tag(item)
        if compacted and compacted not in tags:
            tags.append(compacted)
        if len(tags) >= limit:
            break
    return tags


def summarize_description(profile: Profile, tags: list[str]) -> str:
    cleaned: list[str] = []
    for paragraph in profile.intro:
        text = strip_markdown(paragraph).strip()
        if not text:
            continue
        if text[-1] not in ".!?":
            text += "."
        cleaned.append(text)
    summary = " ".join(cleaned).strip()
    if tags:
        focus_summary = ", ".join(tags[:3])
        if summary:
            summary = f"{summary} Focus areas include {focus_summary}."
        else:
            summary = f"{profile.title} profile. Focus areas include {focus_summary}."
    if not summary:
        summary = f"{profile.title} profile."
    return truncate(summary, 180)


def build_keywords(profile: Profile, tags: list[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in [profile.title, *tags]:
        cleaned = strip_markdown(candidate).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
        if len(ordered) >= 12:
            break
    return ", ".join(ordered)


def section_variant(section: Section) -> str:
    heading = section.heading.lower()
    if is_link_section(section):
        return "links"
    if any(block.kind == "ordered_list" for block in section.blocks):
        return "timeline"
    if any(token in heading for token in ("timeline", "experience", "journey", "selected", "featured", "work")):
        return "timeline"
    if any(token in heading for token in ("research", "focus", "theme", "interest", "expertise")):
        return "focus"
    if any(token in heading for token in ("collaboration", "services", "approach", "offer")):
        return "collaboration"
    if section.blocks and all(block.kind in {"list", "ordered_list"} for block in section.blocks):
        return "stack"
    return "story"


def section_has_media(section: Section) -> bool:
    return any(
        block.kind == "paragraph" and any(is_media_only_text(item) for item in block.items)
        for block in section.blocks
    )


def section_span(section: Section) -> str:
    if section_has_media(section):
        return "section-span-12"
    variant = section_variant(section)
    if variant in {"links", "timeline"}:
        return "section-span-12"
    if variant == "focus":
        return "section-span-5"
    if variant == "collaboration":
        return "section-span-7"
    if variant == "story":
        return "section-span-7"
    return "section-span-6"


def section_label(index: int, section: Section) -> str:
    heading = section.heading.lower()
    if "github" in heading:
        return "GitHub Profile"
    if any(token in heading for token in ("contribution", "activity")):
        return "Activity"
    if any(token in heading for token in ("research agenda", "research interests", "current directions", "focus", "theme")):
        return "Research Agenda"
    if any(token in heading for token in ("highlight", "news", "update")):
        return "Recent Signals"
    if any(token in heading for token in ("publication", "paper", "output")):
        return "Research Outputs"
    if any(token in heading for token in ("project", "funding", "grant")):
        return "Projects & Funding"
    if any(token in heading for token in ("education", "training")):
        return "Training"
    if any(token in heading for token in ("recognition", "award", "service", "membership")):
        return "Recognition"
    if any(token in heading for token in ("patent", "intellectual property", "ip")):
        return "Patents"
    if any(token in heading for token in ("code", "repository", "software", "tool", "open source")):
        return "Open Source"
    if any(token in heading for token in ("background", "bio", "about", "profile")):
        return "Background"

    labels = {
        "links": "Connect",
        "timeline": "Selected Track",
        "focus": "Research Agenda",
        "collaboration": "Working Style",
        "stack": f"Section {index:02d}",
        "story": f"Section {index:02d}",
    }
    return labels[section_variant(section)]


def section_item_count(section: Section) -> int:
    count = 0
    for block in section.blocks:
        if block.kind in {"list", "ordered_list"}:
            count += len(block.items)
        elif block.table_data and len(block.table_data) > 1:
            count += len(block.table_data) - 1
    if count == 0:
        for block in section.blocks:
            if block.kind == "paragraph" and block.items:
                if not is_media_only_text(block.items[0]):
                    count += 1
    return count


def count_intro_badges(profile: Profile) -> int:
    count = 0
    for block in profile.intro_blocks:
        for item in block.items:
            count += len(LINKED_IMAGE_RE.findall(item))
    return count


def summarize_section(section: Section, limit: int = 150) -> str:
    fragments: list[str] = []
    for block in section.blocks:
        if block.kind == "subheading":
            continue
        if block.table_data and len(block.table_data) > 1:
            data_rows = block.table_data[1:]
            content_col = len(block.table_data[0]) - 1
            for row in data_rows[:2]:
                if content_col < len(row):
                    cell = strip_markdown(row[content_col]).strip()
                    if cell:
                        fragments.append(cell)
        elif block.kind in {"paragraph", "quote"}:
            for item in block.items:
                if is_media_only_text(item):
                    continue
                cleaned = strip_markdown(item).strip()
                if cleaned:
                    fragments.append(cleaned)
        elif block.kind in {"list", "ordered_list"}:
            fragments.extend(strip_markdown(item) for item in block.items[:2])
        if fragments:
            break
    if not fragments:
        fragments.append(section.heading)
    return truncate(" / ".join(fragment for fragment in fragments if fragment), limit)


def count_items_for_sections(profile: Profile, keywords: tuple[str, ...]) -> int:
    count = 0
    for section in profile.sections:
        heading = section.heading.lower()
        if any(token in heading for token in keywords):
            count += section_item_count(section)
    return count


def build_metric_cards(profile: Profile, links: list[Link], tags: list[str]) -> list[MetricCard]:
    selected_outputs = count_items_for_sections(profile, ("publication", "paper", "patent", "output"))
    external_links = sum(1 for link in links if link.href.startswith("http"))
    intro_badges = count_intro_badges(profile)
    public_links = max(external_links, intro_badges)

    return [
        MetricCard(
            value=str(max(len(tags), 1)),
            label="Research Themes",
            detail="Primary directions surfaced from the profile narrative.",
        ),
        MetricCard(
            value=str(max(selected_outputs, 1)),
            label="Selected Outputs",
            detail="Highlighted publications and patents visible on the page.",
        ),
        MetricCard(
            value=str(max(public_links, 1)),
            label="Public Links",
            detail="Homepage, scholar, ORCID, GitHub, and direct contact endpoints.",
        ),
    ]


def build_preview_cards(profile: Profile, limit: int = 3) -> list[PreviewCard]:
    previews: list[PreviewCard] = []
    for section in profile.sections:
        if is_link_section(section):
            continue
        count = section_item_count(section)
        meta = f"{count} items" if count else "Narrative"
        previews.append(
            PreviewCard(
                heading=section.heading,
                anchor=section.anchor,
                eyebrow=section_label(len(previews) + 1, section),
                summary=summarize_section(section),
                meta=meta,
            )
        )
        if len(previews) >= limit:
            break
    return previews


def collect_knows_about(profile: Profile, tags: list[str]) -> list[str]:
    topics: list[str] = []
    for candidate in tags:
        cleaned = strip_markdown(candidate).strip()
        if not cleaned or cleaned in topics:
            continue
        topics.append(cleaned)
        if len(topics) >= 12:
            break
    return topics


def render_anchor(href: str, label: str) -> str:
    safe_href = html.escape(href, quote=True)
    safe_label = html.escape(label)
    attrs = ' target="_blank" rel="noreferrer"' if href.startswith("http") else ""
    return f'<a href="{safe_href}"{attrs}>{safe_label}</a>'


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


def render_image(src: str, alt: str) -> str:
    kind = classify_image_kind(src, alt)
    safe_src = html.escape(src.strip(), quote=True)
    safe_alt = html.escape((alt or "image").strip(), quote=True)
    return (
        f'<img class="markdown-image markdown-image-{kind}" src="{safe_src}" '
        f'alt="{safe_alt}" loading="lazy" decoding="async" />'
    )


def render_inline(text: str) -> str:
    parts: list[str] = []
    last_index = 0

    for match in INLINE_TOKEN_RE.finditer(text):
        parts.append(autolink_plain_text(text[last_index:match.start()]))
        token = match.group(0)
        linked_image_match = LINKED_IMAGE_RE.fullmatch(token)
        image_match = IMAGE_RE.fullmatch(token)
        if linked_image_match:
            alt, src, href = linked_image_match.groups()
            safe_href = html.escape(normalize_href(href), quote=True)
            attrs = ' target="_blank" rel="noreferrer"' if href.startswith("http") else ""
            kind = classify_image_kind(src, alt)
            parts.append(f'<a class="image-link image-link-{kind}" href="{safe_href}"{attrs}>{render_image(src, alt)}</a>')
        elif image_match:
            alt, src = image_match.groups()
            parts.append(render_image(src, alt))
        elif token.startswith("["):
            label, target = INLINE_LINK_RE.fullmatch(token).groups()
            href = normalize_href(target)
            safe_href = html.escape(href, quote=True)
            inner = render_inline(label)
            link_attrs = ' target="_blank" rel="noreferrer"' if href.startswith("http") else ""
            parts.append(f'<a href="{safe_href}"{link_attrs}>{inner}</a>')
        elif token.startswith("`"):
            parts.append(f"<code>{html.escape(token[1:-1])}</code>")
        elif token.startswith(("**", "__")):
            parts.append(f"<strong>{autolink_plain_text(token[2:-2])}</strong>")
        elif token.startswith(("*", "_")):
            parts.append(f"<em>{autolink_plain_text(token[1:-1])}</em>")
        last_index = match.end()

    parts.append(autolink_plain_text(text[last_index:]))
    return "".join(parts)


def render_signal_grid(items: list[str]) -> str:
    rendered_items = "".join(
        textwrap.dedent(
            f"""
            <li>
              <strong>Focus {index:02d}</strong>
              <span>{render_inline(item)}</span>
            </li>"""
        ).strip()
        for index, item in enumerate(items, start=1)
    )
    return f'<ul class="signal-grid">{rendered_items}</ul>'


def render_stack_grid(items: list[str]) -> str:
    rendered_items = "".join(f"<li>{render_inline(item)}</li>" for item in items)
    return f'<ul class="stack-grid">{rendered_items}</ul>'


def render_detail_list(items: list[str]) -> str:
    rendered_items = "".join(f"<li>{render_inline(item)}</li>" for item in items)
    return f'<ul class="detail-list">{rendered_items}</ul>'


def render_timeline(items: list[str]) -> str:
    rendered_items = "".join(
        textwrap.dedent(
            f"""
            <li class="timeline-item">
              <strong>{index:02d}</strong>
              <span>{render_inline(item)}</span>
            </li>"""
        ).strip()
        for index, item in enumerate(items, start=1)
    )
    return f'<ol class="timeline-list">{rendered_items}</ol>'


def render_blocks(blocks: list[Block]) -> str:
    parts: list[str] = []
    for block in blocks:
        if block.kind == "paragraph":
            if is_media_only_text(block.items[0]):
                parts.append(f'<div class="{media_group_class(block.items[0])}">{render_inline(block.items[0])}</div>')
            else:
                parts.append(f"<p>{render_inline(block.items[0])}</p>")
        elif block.kind == "subheading":
            parts.append(f'<p class="subheading">{html.escape(block.items[0])}</p>')
        elif block.kind == "quote":
            parts.append(f'<blockquote class="quote-block"><p>{render_inline(block.items[0])}</p></blockquote>')
        elif block.kind == "list":
            parts.append(render_detail_list(block.items))
        elif block.kind == "ordered_list":
            parts.append(render_timeline(block.items))
        elif block.kind == "html":
            parts.append(block.items[0])
    return "".join(parts)


def render_section(section: Section, index: int) -> str:
    variant = section_variant(section)
    classes = f"section-card {section_span(section)} section-{variant}"
    label = html.escape(section_label(index, section))
    title = html.escape(section.heading)

    if variant == "links":
        link_cards: list[str] = []
        for block in section.blocks:
            if block.kind not in {"list", "ordered_list"}:
                continue
            for item in block.items:
                parsed = parse_link_item(item)
                if not parsed:
                    continue
                safe_href = html.escape(parsed.href, quote=True)
                target = ' target="_blank" rel="noreferrer"' if parsed.href.startswith("http") else ""
                link_cards.append(
                    textwrap.dedent(
                        f"""
                        <a class="link-card" href="{safe_href}"{target}>
                          <small>Open Link</small>
                          <strong>{html.escape(parsed.label)}</strong>
                          <span>{html.escape(describe_link(parsed.href))}</span>
                        </a>"""
                    ).strip()
                )
        body_html = f'<div class="link-grid">{"".join(link_cards)}</div>'
    elif variant == "focus":
        list_items = [
            item
            for block in section.blocks
            if block.kind in {"list", "ordered_list"}
            for item in block.items
        ]
        non_list_blocks = [block for block in section.blocks if block.kind not in {"list", "ordered_list"}]
        body_html = render_blocks(non_list_blocks)
        if list_items:
            body_html += render_signal_grid(list_items)
    elif variant == "timeline":
        intro_blocks = [block for block in section.blocks if block.kind in {"paragraph", "quote", "subheading"}]
        timeline_items = [
            item
            for block in section.blocks
            if block.kind in {"ordered_list", "list"}
            for item in block.items
        ]
        body_html = render_blocks(intro_blocks)
        if timeline_items:
            body_html += render_timeline(timeline_items)
    elif variant == "stack":
        stack_items = [
            item
            for block in section.blocks
            if block.kind in {"list", "ordered_list"}
            for item in block.items
        ]
        body_html = render_stack_grid(stack_items) if stack_items else render_blocks(section.blocks)
    else:
        body_html = render_blocks(section.blocks)

    return textwrap.dedent(
        f"""
        <article class="{classes}" id="{section.anchor}">
          <p class="section-label">{label}</p>
          <h2 class="section-title">{title}</h2>
          <div class="section-body">{body_html}</div>
        </article>"""
    ).strip()


def render_metric_cards(metrics: list[MetricCard]) -> str:
    return "".join(
        textwrap.dedent(
            f"""
            <article class="metric-card">
              <strong>{html.escape(metric.value)}</strong>
              <span>{html.escape(metric.label)}</span>
              <small>{html.escape(metric.detail)}</small>
            </article>"""
        ).strip()
        for metric in metrics
    )


def render_preview_cards(previews: list[PreviewCard]) -> str:
    if not previews:
        return ""

    return "".join(
        textwrap.dedent(
            f"""
            <a class="preview-card" href="#{html.escape(preview.anchor)}">
              <p class="preview-kicker">{html.escape(preview.eyebrow)}</p>
              <strong>{html.escape(preview.heading)}</strong>
              <p>{html.escape(preview.summary)}</p>
              <span class="preview-meta">{html.escape(preview.meta)}</span>
            </a>"""
        ).strip()
        for preview in previews
    )


def wrap_svg_lines(text: str, width: int, *, max_lines: int | None = None) -> list[str]:
    lines = textwrap.wrap(strip_markdown(text), width=width)
    if not lines:
        return [""]
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1].rstrip()
        target = max(0, width - 3)
        if len(last) > target:
            cut = last[:target]
            last_space = cut.rfind(" ")
            if last_space >= int(target * 0.5):
                cut = cut[:last_space]
            last = cut.rstrip()
        lines[-1] = last + "..."
    return lines


def render_svg_text_block(lines: list[str], x: int, y: int, line_height: int, class_name: str) -> str:
    tspans = "".join(
        f'<tspan x="{x}" dy="{line_height if index else 0}">{html.escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    return f'<text class="{class_name}" x="{x}" y="{y}">{tspans}</text>'


def render_og_image(profile: Profile, description: str, tags: list[str], metrics: list[MetricCard], canonical_url: str) -> str:
    title_lines = wrap_svg_lines(profile.title, width=12, max_lines=2)
    description_lines = wrap_svg_lines(description, width=42, max_lines=3)
    chips = tags[:4] or ["academic profile"]

    chip_lines: list[str] = []
    x = 72
    y = 452
    row_limit = 760
    for chip in chips:
        label = truncate(strip_markdown(chip), 30)
        width = max(132, min(270, 44 + len(label) * 8))
        if x + width > row_limit:
            x = 72
            y += 56
        chip_lines.extend([
            f'  <g transform="translate({x} {y})">',
            f'    <rect width="{width}" height="42" rx="21" fill="rgba(255,255,255,0.16)" stroke="rgba(255,255,255,0.18)" />',
            f'    <text class="chip" x="18" y="27">{html.escape(label)}</text>',
            '  </g>',
        ])
        x += width + 14

    metric_lines: list[str] = []
    for index, metric in enumerate(metrics):
        metric_lines.extend([
            f'  <g transform="translate(840 {126 + index * 138})">',
            '    <rect width="288" height="112" rx="28" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.1)" />',
            f'    <text class="metric-value" x="28" y="48">{html.escape(metric.value)}</text>',
            f'    <text class="metric-label" x="28" y="74">{html.escape(metric.label.upper())}</text>',
            f'    <text class="metric-detail" x="28" y="94">{html.escape(metric.detail)}</text>',
            '  </g>',
        ])

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{OG_IMAGE_WIDTH}" height="{OG_IMAGE_HEIGHT}" viewBox="0 0 {OG_IMAGE_WIDTH} {OG_IMAGE_HEIGHT}" role="img" aria-labelledby="title desc">',
        f'  <title id="title">{html.escape(profile.title)} profile preview</title>',
        f'  <desc id="desc">{html.escape(description)}</desc>',
        '  <defs>',
        '    <linearGradient id="bg" x1="0%" x2="100%" y1="0%" y2="100%">',
        '      <stop offset="0%" stop-color="#132824" />',
        '      <stop offset="52%" stop-color="#0f1c1a" />',
        '      <stop offset="100%" stop-color="#102d28" />',
        '    </linearGradient>',
        '    <radialGradient id="coral" cx="18%" cy="8%" r="58%">',
        '      <stop offset="0%" stop-color="rgba(202,90,63,0.42)" />',
        '      <stop offset="100%" stop-color="rgba(202,90,63,0)" />',
        '    </radialGradient>',
        '    <radialGradient id="teal" cx="88%" cy="0%" r="54%">',
        '      <stop offset="0%" stop-color="rgba(15,118,110,0.42)" />',
        '      <stop offset="100%" stop-color="rgba(15,118,110,0)" />',
        '    </radialGradient>',
        '    <style>',
        '      .eyebrow { fill: rgba(248, 242, 234, 0.72); font: 800 14px Manrope, Arial, sans-serif; letter-spacing: 0.22em; }',
        '      .title { fill: #f8f2ea; font: 700 86px Fraunces, Georgia, serif; letter-spacing: -0.06em; }',
        '      .body { fill: rgba(248, 242, 234, 0.82); font: 500 28px Manrope, Arial, sans-serif; }',
        '      .chip { fill: #f8f2ea; font: 700 18px Manrope, Arial, sans-serif; }',
        '      .metric-value { fill: #f8f2ea; font: 700 42px Fraunces, Georgia, serif; letter-spacing: -0.04em; }',
        '      .metric-label { fill: #f3cab7; font: 800 12px Manrope, Arial, sans-serif; letter-spacing: 0.18em; }',
        '      .metric-detail { fill: rgba(248, 242, 234, 0.7); font: 500 14px Manrope, Arial, sans-serif; }',
        '      .url { fill: rgba(248, 242, 234, 0.64); font: 700 16px Manrope, Arial, sans-serif; letter-spacing: 0.08em; }',
        '    </style>',
        '  </defs>',
        f'  <rect width="{OG_IMAGE_WIDTH}" height="{OG_IMAGE_HEIGHT}" rx="0" fill="url(#bg)" />',
        f'  <rect width="{OG_IMAGE_WIDTH}" height="{OG_IMAGE_HEIGHT}" rx="0" fill="url(#coral)" />',
        f'  <rect width="{OG_IMAGE_WIDTH}" height="{OG_IMAGE_HEIGHT}" rx="0" fill="url(#teal)" />',
        '  <rect x="36" y="36" width="1128" height="558" rx="36" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.09)" />',
        '  <text class="eyebrow" x="72" y="88">ACADEMIC RESEARCH PROFILE</text>',
        f'  {render_svg_text_block(title_lines, 72, 182, 92, "title")}',
        f'  {render_svg_text_block(description_lines, 72, 322, 40, "body")}',
        *chip_lines,
        *metric_lines,
        f'  <text class="url" x="72" y="582">{html.escape(canonical_url)}</text>',
        '</svg>',
        '',
    ]
    return "\n".join(lines)


def build_og_image_alt(profile: Profile, tags: list[str]) -> str:
    if tags:
        return truncate(
            f"{profile.title} profile preview highlighting {', '.join(tags[:3])}.",
            120,
        )
    return truncate(f"{profile.title} profile preview.", 120)


DEGREE_LEVELS: dict[str, str] = {
    "ph.d.": "Doctorate",
    "phd": "Doctorate",
    "doctorate": "Doctorate",
    "m.s.": "Masters",
    "ms": "Masters",
    "master": "Masters",
    "masters": "Masters",
    "b.s.": "Bachelors",
    "bs": "Bachelors",
    "bachelor": "Bachelors",
    "bachelors": "Bachelors",
}


def extract_credentials(profile: Profile) -> list[dict[str, object]]:
    credentials: list[dict[str, object]] = []
    for section in profile.sections:
        heading = section.heading.lower()
        if not any(token in heading for token in ("background", "education", "training")):
            continue
        for block in section.blocks:
            if not block.table_data or len(block.table_data) < 2:
                continue
            headers = [h.lower() for h in block.table_data[0]]
            degree_idx = next((i for i, h in enumerate(headers) if "degree" in h), None)
            field_idx = next((i for i, h in enumerate(headers) if "field" in h or "subject" in h), None)
            inst_idx = next((i for i, h in enumerate(headers) if "institution" in h or "school" in h or "university" in h), None)
            if inst_idx is None:
                continue
            for row in block.table_data[1:]:
                if len(row) <= inst_idx:
                    continue
                institution = strip_markdown(row[inst_idx]).strip()
                if not institution:
                    continue
                degree = strip_markdown(row[degree_idx]).strip() if degree_idx is not None and degree_idx < len(row) else ""
                field = strip_markdown(row[field_idx]).strip() if field_idx is not None and field_idx < len(row) else ""

                if degree and field:
                    name = f"{degree} in {field}"
                elif degree:
                    name = degree
                elif field:
                    name = field
                else:
                    name = "Studies"

                cred: dict[str, object] = {
                    "@type": "EducationalOccupationalCredential",
                    "credentialCategory": "degree" if degree else "training",
                    "name": name,
                    "recognizedBy": {
                        "@type": "CollegeOrUniversity",
                        "name": institution,
                    },
                }
                normalized = degree.lower().strip()
                no_dots = normalized.replace(".", "")
                if normalized in DEGREE_LEVELS:
                    cred["educationalLevel"] = DEGREE_LEVELS[normalized]
                elif no_dots in DEGREE_LEVELS:
                    cred["educationalLevel"] = DEGREE_LEVELS[no_dots]
                credentials.append(cred)
    return credentials


PUBLICATION_RE = re.compile(
    r'^(?P<authors>[^"]+?)\.\s*'
    r'"(?P<title>[^"]+?)\.?"\s*\.?\s*'
    r'\*(?P<venue>[^*]+?)\*'
    r'(?P<rest>.*)$'
)
DOI_LINK_RE = re.compile(r'\[\[DOI\]\(([^)]+)\)\]')
VOLUME_ISSUE_RE = re.compile(r"^(\d+)\s*\(\s*(\d+)\s*\)$")
DOI_PREFIX = "https://doi.org/"
CONFERENCE_TOKENS = ("conference", "congress", "proceedings", "symposium", "workshop")


def parse_authors(authors_str: str, person_id: str) -> list[dict[str, object]]:
    parsed: list[dict[str, object]] = []
    for raw in authors_str.split(","):
        is_self = "**" in raw
        name = strip_markdown(raw).strip(" .")
        if not name:
            continue
        if is_self:
            parsed.append({"@id": person_id})
        else:
            parsed.append({"@type": "Person", "name": name})
    return parsed


def extract_publications(profile: Profile, person_id: str) -> list[dict[str, object]]:
    publications: list[dict[str, object]] = []
    for section in profile.sections:
        heading = section.heading.lower()
        if not any(token in heading for token in ("publication", "paper")):
            continue
        current_subheading = ""
        for block in section.blocks:
            if block.kind == "subheading" and block.items:
                current_subheading = block.items[0].lower()
                continue
            if not block.table_data or len(block.table_data) < 2:
                continue
            headers = [h.lower() for h in block.table_data[0]]
            year_idx = next((i for i, h in enumerate(headers) if "year" in h or "date" in h), None)
            pub_idx = next((i for i, h in enumerate(headers) if "publication" in h or "title" in h or "citation" in h), None)
            if pub_idx is None:
                pub_idx = 1 if len(headers) > 1 else 0
            is_conference = any(token in current_subheading for token in CONFERENCE_TOKENS)
            for row in block.table_data[1:]:
                if len(row) <= pub_idx:
                    continue
                year = ""
                if year_idx is not None and year_idx < len(row):
                    year = strip_markdown(row[year_idx]).strip()
                pub_text = row[pub_idx].strip()

                doi_match = DOI_LINK_RE.search(pub_text)
                doi_url = doi_match.group(1) if doi_match else ""
                pub_text_clean = DOI_LINK_RE.sub("", pub_text).strip(" .")

                match = PUBLICATION_RE.match(pub_text_clean)
                if not match:
                    continue
                authors = parse_authors(match.group("authors"), person_id)
                title = strip_markdown(match.group("title")).strip(" .")
                venue = strip_markdown(match.group("venue")).strip()
                volume = strip_markdown(match.group("rest")).strip(" .,")
                if not title or not venue:
                    continue

                if is_conference:
                    is_part_of: dict[str, object] = {
                        "@type": "PublicationEvent",
                        "name": venue,
                    }
                else:
                    periodical: dict[str, object] = {
                        "@type": "Periodical",
                        "name": venue,
                    }
                    vi_match = VOLUME_ISSUE_RE.match(volume)
                    if vi_match:
                        vol_num, iss_num = vi_match.groups()
                        is_part_of = {
                            "@type": "PublicationIssue",
                            "issueNumber": iss_num,
                            "isPartOf": {
                                "@type": "PublicationVolume",
                                "volumeNumber": vol_num,
                                "isPartOf": periodical,
                            },
                        }
                    elif volume.isdigit():
                        is_part_of = {
                            "@type": "PublicationVolume",
                            "volumeNumber": volume,
                            "isPartOf": periodical,
                        }
                    else:
                        is_part_of = periodical

                article: dict[str, object] = {
                    "@type": "ScholarlyArticle",
                    "headline": title,
                    "name": title,
                    "author": authors,
                    "isPartOf": is_part_of,
                }
                if year:
                    article["datePublished"] = year
                if doi_url:
                    article["sameAs"] = doi_url
                    doi_value = doi_url.removeprefix(DOI_PREFIX)
                    article["identifier"] = {
                        "@type": "PropertyValue",
                        "propertyID": "DOI",
                        "value": doi_value,
                    }
                publications.append(article)
    return publications


def build_structured_data(
    profile: Profile,
    page_title: str,
    description: str,
    canonical_url: str,
    og_image_url: str,
    links: list[Link],
    tags: list[str],
    generated_at: datetime | None,
) -> str:
    page_id = f"{canonical_url}#webpage"
    person_id = f"{canonical_url}#person"
    image_id = f"{canonical_url}#primaryimage"
    website_id = f"{SITE_URL.rstrip('/')}/#website"
    same_as = [
        link.href
        for link in links
        if link.href.startswith("http") and link.href.rstrip("/") != canonical_url.rstrip("/")
    ]
    email = next((link.href.removeprefix("mailto:") for link in links if link.href.startswith("mailto:")), None)
    knows_about = collect_knows_about(profile, tags)

    graph: list[dict[str, object]] = [
        {
            "@type": "WebSite",
            "@id": website_id,
            "url": SITE_URL,
            "name": profile.title,
            "description": description,
            "inLanguage": "en",
            "publisher": {"@id": person_id},
        },
        {
            "@type": "ProfilePage",
            "@id": page_id,
            "url": canonical_url,
            "name": page_title,
            "description": description,
            "inLanguage": "en",
            "isPartOf": {"@id": website_id},
            "about": {"@id": person_id},
            "primaryImageOfPage": {"@id": image_id},
        },
        {
            "@type": "ImageObject",
            "@id": image_id,
            "url": og_image_url,
            "contentUrl": og_image_url,
            "width": OG_IMAGE_WIDTH,
            "height": OG_IMAGE_HEIGHT,
            "caption": build_og_image_alt(profile, tags),
        },
        {
            "@type": "Person",
            "@id": person_id,
            "name": profile.title,
            "url": canonical_url,
            "description": description,
            "image": {"@id": image_id},
        },
    ]

    person = graph[-1]
    if same_as:
        person["sameAs"] = same_as
    if email:
        person["email"] = email
    if knows_about:
        person["knowsAbout"] = knows_about

    credentials = extract_credentials(profile)
    if credentials:
        graph.extend(credentials)
        seen_institutions: set[str] = set()
        alumni_of: list[dict[str, str]] = []
        for cred in credentials:
            institution_name = cred["recognizedBy"]["name"]  # type: ignore[index]
            if institution_name in seen_institutions:
                continue
            seen_institutions.add(institution_name)
            alumni_of.append({
                "@type": "CollegeOrUniversity",
                "name": institution_name,
            })
        if alumni_of:
            person["alumniOf"] = alumni_of

    publications = extract_publications(profile, person_id)
    if publications:
        graph.extend(publications)

    if generated_at is not None:
        graph[1]["dateModified"] = generated_at.date().isoformat()

    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def build_sitemap(canonical_url: str, og_image_url: str, profile: Profile, generated_at: datetime | None) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
        '  <url>',
        f'    <loc>{html.escape(canonical_url)}</loc>',
    ]
    if generated_at is not None:
        lines.append(f'    <lastmod>{generated_at.date().isoformat()}</lastmod>')
    lines.extend([
        '    <image:image>',
        f'      <image:loc>{html.escape(og_image_url)}</image:loc>',
        f'      <image:title>{html.escape(profile.title)}</image:title>',
        '    </image:image>',
        '  </url>',
        '</urlset>',
        '',
    ])
    return "\n".join(lines)


def build_robots(canonical_url: str) -> str:
    sitemap_url = urljoin(canonical_url, SITEMAP_FILENAME)
    return textwrap.dedent(
        f"""\
        User-agent: *
        Allow: /

        Sitemap: {sitemap_url}
        """
    )


def render_site_artifacts(markdown: str, generated_at: datetime | None = None) -> SiteArtifacts:
    built_at = generated_at.astimezone(UTC) if generated_at is not None else None
    profile = parse_profile(markdown)
    links = sorted(extract_links(profile), key=lambda link: build_cta_priority(link.label))
    tags = extract_tags(profile)
    description = summarize_description(profile, tags)
    page_title = f"{profile.title} | Research Profile"
    canonical_url = pick_primary_url(links)
    og_image_url = urljoin(canonical_url, OG_IMAGE_FILENAME)
    og_image_alt = build_og_image_alt(profile, tags)
    keywords = build_keywords(profile, tags)
    if built_at is not None:
        generated_label = built_at.strftime("%Y-%m-%d %H:%M UTC")
        build_stamp_html = f'\n        <span><span class="footer-note">Build stamp</span> {generated_label}</span>'
    else:
        generated_label = ""
        build_stamp_html = ""
    metrics = build_metric_cards(profile, links, tags)
    previews = build_preview_cards(profile)

    intro_html = render_blocks(profile.intro_blocks)
    if not intro_html:
        intro_html = "<p>Profile content is maintained in README.md.</p>"

    tag_html = "".join(f'<span class="tag">{render_inline(tag)}</span>' for tag in tags)
    if not tag_html:
        tag_html = '<span class="tag">README-driven profile</span>'

    cta_links = links[:4]
    cta_html = ""
    for index, link in enumerate(cta_links):
        safe_href = html.escape(link.href, quote=True)
        target = ' target="_blank" rel="noreferrer"' if link.href.startswith("http") else ""
        button_class = "button button-primary" if index == 0 else "button button-secondary"
        cta_html += f'<a class="{button_class}" href="{safe_href}"{target}>{html.escape(link.label)}</a>'
    if not cta_html:
        cta_html = f'<a class="button button-primary" href="{html.escape(REPO_URL, quote=True)}" target="_blank" rel="noreferrer">Repository</a>'

    nav_html = "".join(
        f'<a href="#{section.anchor}">{html.escape(section.heading)}</a>'
        for section in profile.sections
    )
    preview_html = render_preview_cards(previews)
    metric_html = render_metric_cards(metrics)
    section_html = textwrap.indent(
        "\n".join(
            render_section(section, index)
            for index, section in enumerate(profile.sections, start=1)
        ),
        "        ",
    )

    preview_section_html = ""
    nav_section_html = ""
    content_section_html = ""
    if profile.sections:
        preview_section_html = textwrap.dedent(
            f"""
            <section class="preview-wrap">
              <div class="section-intro">
                <p>Research Overview</p>
                <h2 class="section-title">Research directions, outputs, and activity signals at a glance.</h2>
              </div>
              <div class="preview-grid">{preview_html}</div>
            </section>
            """
        ).strip()
        nav_section_html = f'<div class="nav-wrap"><nav class="nav" aria-label="Section navigation">{nav_html}</nav></div>'
        content_section_html = textwrap.dedent(
            f"""
            <section class="content-grid">
{section_html}
            </section>
            """
        ).strip()

    sitemap = build_sitemap(canonical_url, og_image_url, profile, built_at)
    robots = build_robots(canonical_url)
    og_image = render_og_image(profile, description, tags, metrics, canonical_url)
    structured_data = build_structured_data(
        profile=profile,
        page_title=page_title,
        description=description,
        canonical_url=canonical_url,
        og_image_url=og_image_url,
        links=links,
        tags=tags,
        generated_at=built_at,
    )

    replacements = {
        "__PAGE_TITLE__": html.escape(page_title),
        "__TITLE__": html.escape(profile.title),
        "__DESCRIPTION__": html.escape(description, quote=True),
        "__KEYWORDS__": html.escape(keywords, quote=True),
        "__THEME_COLOR__": THEME_COLOR,
        "__CANONICAL_URL__": html.escape(canonical_url, quote=True),
        "__SITE_LOCALE__": SITE_LOCALE,
        "__OG_IMAGE_URL__": html.escape(og_image_url, quote=True),
        "__OG_IMAGE_ALT__": html.escape(og_image_alt, quote=True),
        "__SITEMAP_URL__": html.escape(urljoin(canonical_url, SITEMAP_FILENAME), quote=True),
        "__MODIFIED_META__": (
            f'    <meta property="article:modified_time" content="{built_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")}" />'
            if built_at is not None
            else ""
        ),
        "__STRUCTURED_DATA__": structured_data,
        "__INTRO_HTML__": intro_html,
        "__TAG_HTML__": tag_html,
        "__CTA_HTML__": cta_html,
        "__METRIC_HTML__": metric_html,
        "__PREVIEW_SECTION__": preview_section_html,
        "__NAV_SECTION__": nav_section_html,
        "__CONTENT_SECTION__": content_section_html,
        "__GENERATED_AT__": generated_label,
        "__BUILD_STAMP_HTML__": build_stamp_html,
        "__REPO_URL__": html.escape(REPO_URL, quote=True),
    }

    output = HTML_TEMPLATE
    for token, value in replacements.items():
        output = output.replace(token, value)

    return SiteArtifacts(
        html=output,
        og_image=og_image,
        sitemap=sitemap,
        robots=robots,
        nojekyll="",
        canonical_url=canonical_url,
    )


def render_site(markdown: str, generated_at: datetime | None = None) -> str:
    return render_site_artifacts(markdown, generated_at=generated_at).html


def build(
    readme_path: Path = README_PATH,
    output_path: Path = OUTPUT_PATH,
    generated_at: datetime | None = None,
) -> str:
    markdown = readme_path.read_text(encoding="utf-8")
    artifacts = render_site_artifacts(markdown, generated_at=generated_at)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path.write_text(artifacts.html, encoding="utf-8")
    (output_dir / OG_IMAGE_FILENAME).write_text(artifacts.og_image, encoding="utf-8")
    (output_dir / SITEMAP_FILENAME).write_text(artifacts.sitemap, encoding="utf-8")
    (output_dir / ROBOTS_FILENAME).write_text(artifacts.robots, encoding="utf-8")
    (output_dir / NOJEKYLL_FILENAME).write_text(artifacts.nojekyll, encoding="utf-8")

    return artifacts.html


def _readme_git_mtime() -> datetime | None:
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(README_PATH)],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(README_PATH.parent),
        )
        stamp = result.stdout.strip()
        if not stamp:
            return None
        return datetime.fromisoformat(stamp).astimezone(UTC)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    build(generated_at=_readme_git_mtime())
