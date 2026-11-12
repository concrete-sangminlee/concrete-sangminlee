"""Rasterize docs/og-preview.svg into docs/og-preview.png.

Usage: python3 scripts/render_og_png.py [--require] [--svg PATH] [--png PATH]

Social platforms (X, LinkedIn, Slack, KakaoTalk and others) do not render SVG
link previews, so the pages reference og-preview.png. The site build itself
uses only the Python standard library and cannot draw text, so this step asks a
headless Chromium-family browser to take a 1200x630 screenshot of the SVG.

- The browser is taken from $CHROME_BIN, or the first of chrome-headless-shell,
  google-chrome, google-chrome-stable, chromium, chromium-browser and
  microsoft-edge on PATH.
  GitHub-hosted Ubuntu runners ship Google Chrome.
- Without --require, a missing browser is only a notice, so local builds work
  on machines that have no browser. With --require (used in CI), a missing
  browser or a wrong-sized image fails the run, because the deployed page would
  otherwise point at a preview image that does not exist.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
SVG_PATH = DOCS_DIR / "og-preview.svg"
PNG_PATH = DOCS_DIR / "og-preview.png"
WIDTH = 1200
HEIGHT = 630
# chrome-headless-shell is a screenshot-only build; prefer it when present.
BROWSER_NAMES = (
    "chrome-headless-shell",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
)
# Newer browsers use --headless=new; older ones only know --headless.
HEADLESS_FLAGS = ("--headless=new", "--headless")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def find_browser(env: Mapping[str, str] | None = None) -> str | None:
    env = os.environ if env is None else env
    override = env.get("CHROME_BIN", "").strip()
    if override:
        found = shutil.which(override)
        if found:
            return found
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def png_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) from a PNG header, or None if the file is not a PNG."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != PNG_SIGNATURE or head[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def rasterize(browser: str, svg_path: Path, png_path: Path, timeout: float = 60.0) -> bool:
    """Screenshot the SVG at 1200x630. True only if a PNG of exactly that size was written."""
    for headless_flag in HEADLESS_FLAGS:
        png_path.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory() as profile_dir:
            command = [
                browser,
                headless_flag,
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={WIDTH},{HEIGHT}",
                f"--user-data-dir={profile_dir}",
                f"--screenshot={png_path}",
                svg_path.resolve().as_uri(),
            ]
            try:
                subprocess.run(command, capture_output=True, timeout=timeout, check=False)
            except (OSError, subprocess.TimeoutExpired):
                continue
        if png_size(png_path) == (WIDTH, HEIGHT):
            return True
    png_path.unlink(missing_ok=True)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rasterize the social preview SVG to PNG.")
    parser.add_argument("--svg", type=Path, default=SVG_PATH)
    parser.add_argument("--png", type=Path, default=PNG_PATH)
    parser.add_argument("--require", action="store_true", help="fail if the PNG cannot be produced")
    args = parser.parse_args(argv)

    if not args.svg.is_file():
        print(f"error: {args.svg} does not exist; run the site build first.", file=sys.stderr)
        return 1

    browser = find_browser()
    if browser is None:
        message = (
            f"No Chromium-family browser found, so {args.png.name} was not rendered. "
            "Set CHROME_BIN or install Chrome or Chromium."
        )
        if args.require:
            print(f"error: {message}", file=sys.stderr)
            return 1
        print(f"notice: {message} CI renders it before deploying.")
        return 0

    if rasterize(browser, args.svg, args.png):
        print(f"Rendered {args.png.name} ({WIDTH}x{HEIGHT}) with {Path(browser).name}.")
        return 0

    message = f"{Path(browser).name} did not produce a {WIDTH}x{HEIGHT} PNG from {args.svg.name}."
    if args.require:
        print(f"error: {message}", file=sys.stderr)
        return 1
    print(f"notice: {message} CI renders it before deploying.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
