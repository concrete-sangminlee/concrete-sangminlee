"""Generate profile SVG visualizations for the GitHub README.

Produces tech-stack and research-areas SVGs in light and dark variants.
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
# Tech-stack data
# ---------------------------------------------------------------------------

TECH_CATEGORIES = [
    (
        "ML & Deep Learning",
        [
            ("Python", "#ca5a3f"),
            ("PyTorch", "#0f766e"),
            ("TensorFlow", "#d1a654"),
            ("scikit-learn", "#556762"),
        ],
    ),
    (
        "Data & Computing",
        [
            ("NumPy", "#0f766e"),
            ("Pandas", "#ca5a3f"),
            ("OpenCV", "#556762"),
            ("CUDA", "#d1a654"),
        ],
    ),
    (
        "Tools & Infrastructure",
        [
            ("Docker", "#0f766e"),
            ("Git", "#ca5a3f"),
            ("LaTeX", "#556762"),
            ("Linux", "#d1a654"),
        ],
    ),
]

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
# Tech-stack SVG
# ---------------------------------------------------------------------------

PILL_H = 34
PILL_PAD_X = 18
PILL_GAP = 10
PILL_RADIUS = 8
PILL_FONT = 13
CATEGORY_FONT = 12
ROW_GAP = 14
CARD_PAD = 24
CARD_RADIUS = 14


def _estimate_text_width(text: str, font_size: int) -> float:
    return len(text) * font_size * 0.58


def _render_tech_stack(palette: dict[str, str]) -> str:
    rows: list[str] = []
    y = CARD_PAD
    max_row_width = 0

    for cat_label, items in TECH_CATEGORIES:
        # Category label
        rows.append(
            f'<text x="{CARD_PAD}" y="{y + 14}" '
            f'font-family="\'Segoe UI\', sans-serif" font-size="{CATEGORY_FONT}" '
            f'font-weight="600" fill="{palette["muted"]}" '
            f'letter-spacing="0.5">{html.escape(cat_label.upper())}</text>'
        )
        y += 24

        # Pills
        x = CARD_PAD
        for name, color in items:
            tw = _estimate_text_width(name, PILL_FONT)
            pw = tw + PILL_PAD_X * 2
            rows.append(
                f'<rect x="{x}" y="{y}" width="{pw}" height="{PILL_H}" '
                f'rx="{PILL_RADIUS}" fill="{color}" opacity="0.92"/>'
            )
            rows.append(
                f'<text x="{x + pw / 2}" y="{y + PILL_H / 2 + 1}" '
                f'font-family="\'Segoe UI\', sans-serif" font-size="{PILL_FONT}" '
                f'font-weight="500" fill="#ffffff" text-anchor="middle" '
                f'dominant-baseline="central">{html.escape(name)}</text>'
            )
            x += pw + PILL_GAP
        max_row_width = max(max_row_width, x)
        y += PILL_H + ROW_GAP

    width = max(max_row_width + CARD_PAD, 500)
    height = y + CARD_PAD - ROW_GAP + 4

    return textwrap.dedent(f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
          <rect width="{width}" height="{height}" rx="{CARD_RADIUS}" fill="{palette['card']}" />
          <rect width="{width}" height="{height}" rx="{CARD_RADIUS}" fill="none"
                stroke="{palette['grid']}" stroke-width="1" />
          {"".join(rows)}
        </svg>""")


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
        "tech-stack.svg": _render_tech_stack(LIGHT),
        "tech-stack-dark.svg": _render_tech_stack(DARK),
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
