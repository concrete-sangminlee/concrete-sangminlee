"""Generate profile SVG visualizations for the GitHub README.

Produces hero-banner and research-areas SVGs in light and dark variants.
All output is pure SVG built with Python stdlib — no external packages.
"""

from __future__ import annotations

import argparse
import html
import math
import os
import textwrap

# ---------------------------------------------------------------------------
# Design-system palettes
# ---------------------------------------------------------------------------

LIGHT = {
    "bg": "#f6efe3",
    "card": "#ffffff",
    "ink": "#102522",
    "muted": "#556762",
    "accent": "#ca5a3f",
    "teal": "#0f766e",
    "gold": "#d1a654",
    "grid": "#d6cfc3",
    "area_fill": "#ca5a3f",
    "area_fill_opacity": "0.18",
    "area_stroke": "#ca5a3f",
    "dot": "#ca5a3f",
}

DARK = {
    "bg": "#132522",
    "card": "#1a3330",
    "ink": "#f8f2ea",
    "muted": "#8fa69e",
    "accent": "#d1a654",
    "teal": "#0f766e",
    "gold": "#d1a654",
    "grid": "#2a4a45",
    "area_fill": "#d1a654",
    "area_fill_opacity": "0.22",
    "area_stroke": "#d1a654",
    "dot": "#d1a654",
}

# ---------------------------------------------------------------------------
# Hero banner data
# ---------------------------------------------------------------------------

HERO_NAME = "Sang Min Lee"
HERO_SUBTITLE = "Ph.D. Candidate in AI \u00b7 Seoul National University"
HERO_TAGLINE = "AI for Resilient Infrastructure"

# ---------------------------------------------------------------------------
# Research-areas data (label, value 0-1)
# ---------------------------------------------------------------------------

RESEARCH_AREAS = [
    ("Structural Health\nMonitoring", 0.95),
    ("Wind\nEngineering", 0.82),
    ("Automated\nNDT", 0.90),
    ("LLM & RAG\nSystems", 0.78),
    ("Lightweight\nML", 0.74),
    ("AI for\nInfrastructure", 0.85),
]

# ---------------------------------------------------------------------------
# Hero banner SVG
# ---------------------------------------------------------------------------

HERO_W = 840
HERO_H = 200
CARD_PAD = 24
CARD_RADIUS = 14


def _render_hero_banner(palette: dict[str, str]) -> str:
    bg = palette["bg"]
    card = palette["card"]
    ink = palette["ink"]
    accent = palette["accent"]
    teal = palette.get("teal", accent)
    muted = palette["muted"]
    grid = palette["grid"]

    name_escaped = html.escape(HERO_NAME)
    subtitle_escaped = html.escape(HERO_SUBTITLE)
    tagline_escaped = html.escape(HERO_TAGLINE)

    # Build a unique gradient id based on palette to avoid collisions
    is_dark = palette is DARK
    suffix = "dark" if is_dark else "light"

    svg = textwrap.dedent(f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {HERO_W} {HERO_H}" width="{HERO_W}" height="{HERO_H}">
          <defs>
            <linearGradient id="bgGrad_{suffix}" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="{bg}" />
              <stop offset="100%" stop-color="{card}" />
            </linearGradient>
            <linearGradient id="accentLine_{suffix}" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="{accent}" />
              <stop offset="100%" stop-color="{teal}" />
            </linearGradient>
          </defs>

          <!-- Outer background -->
          <rect width="{HERO_W}" height="{HERO_H}" rx="{CARD_RADIUS}" fill="url(#bgGrad_{suffix})" />

          <!-- Card -->
          <rect x="16" y="16" width="{HERO_W - 32}" height="{HERO_H - 32}" rx="{CARD_RADIUS}" fill="{card}" />
          <rect x="16" y="16" width="{HERO_W - 32}" height="{HERO_H - 32}" rx="{CARD_RADIUS}" fill="none" stroke="{grid}" stroke-width="1" />

          <!-- Accent bar at top of card -->
          <rect x="16" y="16" width="{HERO_W - 32}" height="4" rx="2" fill="url(#accentLine_{suffix})" />

          <!-- Decorative dots -->
          <circle cx="{HERO_W - 60}" cy="50" r="30" fill="{accent}" opacity="0.06" />
          <circle cx="{HERO_W - 90}" cy="80" r="50" fill="{teal}" opacity="0.05" />
          <circle cx="{HERO_W - 50}" cy="140" r="20" fill="{accent}" opacity="0.04" />

          <!-- Name -->
          <text x="48" y="72"
                font-family="'Segoe UI', system-ui, sans-serif" font-size="28"
                font-weight="700" fill="{ink}"
                letter-spacing="-0.5">{name_escaped}</text>

          <!-- Subtitle -->
          <text x="48" y="100"
                font-family="'Segoe UI', system-ui, sans-serif" font-size="14"
                font-weight="400" fill="{muted}">{subtitle_escaped}</text>

          <!-- Divider line -->
          <line x1="48" y1="118" x2="260" y2="118" stroke="{grid}" stroke-width="1" />

          <!-- Tagline -->
          <text x="48" y="148"
                font-family="'Segoe UI', system-ui, sans-serif" font-size="16"
                font-weight="600" fill="{accent}"
                letter-spacing="0.3">{tagline_escaped}</text>
        </svg>""")

    return svg


# ---------------------------------------------------------------------------
# Research-areas radar SVG
# ---------------------------------------------------------------------------

RADAR_CX = 250
RADAR_CY = 210
RADAR_R = 150
RADAR_RINGS = 5
RADAR_LABEL_OFFSET = 28
RADAR_W = 500
RADAR_H = 440


def _polar(cx: float, cy: float, angle: float, r: float) -> tuple[float, float]:
    rad = math.radians(angle - 90)  # start from top
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _render_radar(palette: dict[str, str]) -> str:
    n = len(RESEARCH_AREAS)
    step = 360 / n
    parts: list[str] = []

    # Background card
    parts.append(
        f'<rect width="{RADAR_W}" height="{RADAR_H}" rx="{CARD_RADIUS}" '
        f'fill="{palette["card"]}" />'
    )
    parts.append(
        f'<rect width="{RADAR_W}" height="{RADAR_H}" rx="{CARD_RADIUS}" '
        f'fill="none" stroke="{palette["grid"]}" stroke-width="1" />'
    )

    # Concentric rings
    for ring in range(1, RADAR_RINGS + 1):
        r = RADAR_R * ring / RADAR_RINGS
        points = " ".join(
            f"{_polar(RADAR_CX, RADAR_CY, i * step, r)[0]:.1f},"
            f"{_polar(RADAR_CX, RADAR_CY, i * step, r)[1]:.1f}"
            for i in range(n)
        )
        parts.append(
            f'<polygon points="{points}" fill="none" '
            f'stroke="{palette["grid"]}" stroke-width="1" />'
        )

    # Axis lines
    for i in range(n):
        x, y = _polar(RADAR_CX, RADAR_CY, i * step, RADAR_R)
        parts.append(
            f'<line x1="{RADAR_CX}" y1="{RADAR_CY}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="{palette["grid"]}" stroke-width="1" />'
        )

    # Data polygon
    data_points = " ".join(
        f"{_polar(RADAR_CX, RADAR_CY, i * step, RADAR_R * val)[0]:.1f},"
        f"{_polar(RADAR_CX, RADAR_CY, i * step, RADAR_R * val)[1]:.1f}"
        for i, (_, val) in enumerate(RESEARCH_AREAS)
    )
    parts.append(
        f'<polygon points="{data_points}" '
        f'fill="{palette["area_fill"]}" fill-opacity="{palette["area_fill_opacity"]}" '
        f'stroke="{palette["area_stroke"]}" stroke-width="2" />'
    )

    # Data dots
    for i, (_, val) in enumerate(RESEARCH_AREAS):
        x, y = _polar(RADAR_CX, RADAR_CY, i * step, RADAR_R * val)
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" '
            f'fill="{palette["dot"]}" />'
        )

    # Labels
    for i, (label, _) in enumerate(RESEARCH_AREAS):
        angle = i * step
        lx, ly = _polar(RADAR_CX, RADAR_CY, angle, RADAR_R + RADAR_LABEL_OFFSET)
        anchor = "middle"
        if 45 < angle < 180:
            anchor = "start"
        elif 180 < angle < 315:
            anchor = "end"
        lines = label.split("\n")
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + li * 16:.1f}" '
                f'font-family="\'Segoe UI\', sans-serif" font-size="12" '
                f'font-weight="500" fill="{palette["ink"]}" '
                f'text-anchor="{anchor}" dominant-baseline="central">'
                f'{html.escape(line)}</text>'
            )

    return textwrap.dedent(f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {RADAR_W} {RADAR_H}" width="{RADAR_W}" height="{RADAR_H}">
          {"".join(parts)}
        </svg>""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate profile SVGs")
    parser.add_argument(
        "--output-dir",
        default="dist",
        help="Directory to write SVG files into (default: dist)",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    files = {
        "hero-banner.svg": _render_hero_banner(LIGHT),
        "hero-banner-dark.svg": _render_hero_banner(DARK),
        "research-areas.svg": _render_radar(LIGHT),
        "research-areas-dark.svg": _render_radar(DARK),
    }

    for name, svg in files.items():
        path = os.path.join(args.output_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  wrote {path}")


if __name__ == "__main__":
    main()
