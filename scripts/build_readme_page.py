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
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown.min.css" />
    <style>
      :root {
        color-scheme: light;
        --bg: #f5f5f4;
        --surface: #ffffff;
        --surface-border: #e7e5e4;
        --ink: #1c1917;
        --muted: #78716c;
        --accent: #0f766e;
        --shadow: 0 18px 50px rgba(28, 25, 23, 0.08);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "IBM Plex Sans", sans-serif;
        color: var(--ink);
        background: var(--bg);
      }

      .page {
        width: min(760px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 48px 0 56px;
      }

      h1 {
        margin: 0;
        font-size: clamp(2rem, 5vw, 3rem);
        line-height: 1;
        letter-spacing: -0.04em;
      }

      .shell {
        padding: 28px;
        border: 1px solid var(--surface-border);
        border-radius: 20px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), #ffffff);
        box-shadow: var(--shadow);
      }

      .header {
        margin-bottom: 24px;
      }

      .kicker {
        margin: 0 0 10px;
        color: var(--accent);
        font: 500 12px/1.2 "IBM Plex Mono", monospace;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .subtitle {
        margin: 12px 0 0;
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.7;
      }

      .meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 0 0 18px;
        color: var(--muted);
        font: 500 12px/1.2 "IBM Plex Mono", monospace;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .meta span {
        display: inline-flex;
        align-items: center;
        padding: 7px 10px;
        border-radius: 999px;
        background: #f5f5f4;
      }

      .markdown-body {
        color: var(--ink);
        background: transparent;
        font-family: "IBM Plex Sans", sans-serif;
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

      .fallback {
        white-space: pre-wrap;
        font: 400 0.95rem/1.7 "IBM Plex Mono", monospace;
      }

      @media (max-width: 720px) {
        .page {
          width: min(100vw - 20px, 760px);
          padding: 18px 0 32px;
        }

        .shell {
          padding: 18px;
        }
      }
    </style>
  </head>
  <body>
    <main class="page">
      <section class="shell">
        <header class="header">
          <p class="kicker">GitHub Profile</p>
          <h1>Sang Min Lee</h1>
          <p class="subtitle">
            Minimal profile page generated from the repository README.
          </p>
        </header>
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
