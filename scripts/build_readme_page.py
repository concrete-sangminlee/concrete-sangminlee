#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
OUTPUT_PATH = ROOT / "docs" / "index.html"


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sang Min Lee | Profile</title>
    <meta name="description" content="Sang Min Lee's GitHub profile and research focus." />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown.min.css" />
    <style>
      :root {
        color-scheme: light;
        --bg: #f3efe6;
        --bg-accent: rgba(194, 65, 12, 0.16);
        --surface: rgba(255, 252, 245, 0.88);
        --surface-border: rgba(28, 25, 23, 0.12);
        --ink: #1c1917;
        --muted: #57534e;
        --accent: #c2410c;
        --accent-soft: #ffedd5;
        --shadow: 0 30px 80px rgba(28, 25, 23, 0.14);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Space Grotesk", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, var(--bg-accent), transparent 36%),
          linear-gradient(180deg, #fff8ef 0%, var(--bg) 55%, #efe7dc 100%);
      }

      .page {
        width: min(1080px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 32px 0 56px;
      }

      .hero {
        position: relative;
        overflow: hidden;
        margin-bottom: 20px;
        padding: 28px;
        border: 1px solid var(--surface-border);
        border-radius: 28px;
        background:
          linear-gradient(140deg, rgba(255, 255, 255, 0.9), rgba(255, 247, 237, 0.88)),
          linear-gradient(135deg, rgba(194, 65, 12, 0.08), transparent 60%);
        box-shadow: var(--shadow);
      }

      .hero::after {
        content: "";
        position: absolute;
        right: -48px;
        top: -48px;
        width: 180px;
        height: 180px;
        border-radius: 36px;
        background: linear-gradient(135deg, rgba(194, 65, 12, 0.22), rgba(251, 146, 60, 0.08));
        transform: rotate(18deg);
      }

      .eyebrow {
        position: relative;
        z-index: 1;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 14px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255, 237, 213, 0.8);
        color: var(--accent);
        font: 500 12px/1.2 "IBM Plex Mono", monospace;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      h1 {
        position: relative;
        z-index: 1;
        margin: 0;
        max-width: 640px;
        font-size: clamp(2.2rem, 6vw, 4.6rem);
        line-height: 0.95;
        letter-spacing: -0.05em;
      }

      .subtitle {
        position: relative;
        z-index: 1;
        max-width: 620px;
        margin: 16px 0 0;
        color: var(--muted);
        font-size: clamp(1rem, 2.4vw, 1.15rem);
        line-height: 1.7;
      }

      .hero-links {
        position: relative;
        z-index: 1;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 22px;
      }

      .hero-links a {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border: 1px solid rgba(194, 65, 12, 0.18);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.7);
        color: var(--ink);
        text-decoration: none;
        transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
      }

      .hero-links a:hover {
        transform: translateY(-1px);
        border-color: rgba(194, 65, 12, 0.45);
        background: rgba(255, 255, 255, 0.95);
      }

      .shell {
        padding: 22px;
        border: 1px solid var(--surface-border);
        border-radius: 28px;
        background: var(--surface);
        box-shadow: var(--shadow);
        backdrop-filter: blur(16px);
      }

      .meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 0 0 18px;
        color: var(--muted);
        font: 500 12px/1.2 "IBM Plex Mono", monospace;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .meta span {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 999px;
        background: rgba(28, 25, 23, 0.045);
      }

      .markdown-body {
        color: var(--ink);
        background: transparent;
        font-family: "Space Grotesk", sans-serif;
      }

      .markdown-body h1,
      .markdown-body h2,
      .markdown-body h3 {
        font-weight: 700;
        letter-spacing: -0.03em;
      }

      .markdown-body h1 {
        font-size: clamp(2rem, 4vw, 3rem);
        line-height: 1;
      }

      .markdown-body h2 {
        padding-bottom: 0.3em;
        border-bottom-color: rgba(28, 25, 23, 0.08);
      }

      .markdown-body a {
        color: var(--accent);
      }

      .markdown-body img {
        border-radius: 14px;
      }

      .fallback {
        white-space: pre-wrap;
        font: 400 0.95rem/1.7 "IBM Plex Mono", monospace;
      }

      @media (max-width: 720px) {
        .page {
          width: min(100vw - 20px, 1080px);
          padding: 18px 0 32px;
        }

        .hero,
        .shell {
          padding: 18px;
          border-radius: 22px;
        }
      }
    </style>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <p class="eyebrow">GitHub Profile / README</p>
        <h1>Sang Min Lee</h1>
        <p class="subtitle">
          Machine learning research, cleaner experiment pipelines, and shipping work
          that survives outside a notebook.
        </p>
        <div class="hero-links">
          <a href="https://github.com/concrete-sangminlee">GitHub</a>
          <a href="https://github.com/concrete-sangminlee/concrete-sangminlee/blob/main/README.md">README Source</a>
        </div>
      </section>

      <section class="shell">
        <div class="meta">
          <span>Auto-published from README.md</span>
          <span>Updated __GENERATED_AT__</span>
        </div>
        <article class="markdown-body" id="content">
          <div class="fallback">Loading profile...</div>
        </article>
      </section>
    </main>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
      const markdownSource = __MARKDOWN_JSON__;
      const content = document.getElementById("content");

      if (window.marked?.parse) {
        content.innerHTML = window.marked.parse(markdownSource);
      } else {
        const fallback = document.createElement("pre");
        fallback.className = "fallback";
        fallback.textContent = markdownSource;
        content.replaceChildren(fallback);
      }
    </script>
  </body>
</html>
"""


def build() -> None:
    markdown = README_PATH.read_text(encoding="utf-8")
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    html = HTML_TEMPLATE.replace("__GENERATED_AT__", generated_at).replace(
        "__MARKDOWN_JSON__", json.dumps(markdown)
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    build()
