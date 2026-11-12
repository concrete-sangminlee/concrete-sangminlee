from __future__ import annotations

import contextlib
import importlib.util
import io
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "render_og_png.py"
SPEC = importlib.util.spec_from_file_location("render_og_png", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def tiny_png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return MODULE.PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IEND", b"")


class RenderOgPngTests(unittest.TestCase):
    def test_png_size_reads_header_and_rejects_other_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "a.png"
            png.write_bytes(tiny_png(1200, 630))
            self.assertEqual(MODULE.png_size(png), (1200, 630))
            svg = Path(tmp) / "a.svg"
            svg.write_text("<svg/>", encoding="utf-8")
            self.assertIsNone(MODULE.png_size(svg))
            self.assertIsNone(MODULE.png_size(Path(tmp) / "missing.png"))

    def test_find_browser_prefers_chrome_bin(self) -> None:
        with mock.patch.object(MODULE.shutil, "which", side_effect=lambda name: f"/bin/{name}"):
            self.assertEqual(MODULE.find_browser({"CHROME_BIN": "my-chrome"}), "/bin/my-chrome")
            self.assertEqual(MODULE.find_browser({}), "/bin/chrome-headless-shell")
        with mock.patch.object(MODULE.shutil, "which", return_value=None):
            self.assertIsNone(MODULE.find_browser({}))

    def run_main(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = MODULE.main(argv)
        return code, out.getvalue()

    def test_missing_browser_is_a_notice_locally_and_an_error_in_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svg = Path(tmp) / "og-preview.svg"
            svg.write_text("<svg/>", encoding="utf-8")
            args = ["--svg", str(svg), "--png", str(Path(tmp) / "og-preview.png")]
            with mock.patch.object(MODULE, "find_browser", return_value=None):
                code, out = self.run_main(args)
                self.assertEqual(code, 0)
                self.assertIn("notice:", out)
                code, out = self.run_main([*args, "--require"])
                self.assertEqual(code, 1)
                self.assertIn("error:", out)

    def test_wrong_sized_output_fails_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svg = Path(tmp) / "og-preview.svg"
            svg.write_text("<svg/>", encoding="utf-8")
            png = Path(tmp) / "og-preview.png"

            def fake_run(command: list[str], **_: object) -> None:
                png.write_bytes(tiny_png(800, 600))

            with mock.patch.object(MODULE, "find_browser", return_value="/bin/chrome"), mock.patch.object(
                MODULE.subprocess, "run", side_effect=fake_run
            ):
                code, _ = self.run_main(["--svg", str(svg), "--png", str(png), "--require"])
            self.assertEqual(code, 1)
            self.assertFalse(png.exists())

    def test_missing_svg_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_main(["--svg", str(Path(tmp) / "none.svg")])
        self.assertEqual(code, 1)
        self.assertIn("run the site build first", out)


if __name__ == "__main__":
    unittest.main()
