"""Render a PNG beside each chart SVG, for the email edition of the newsletter.

Gmail and Outlook don't show SVG images, so the feed (which Buttondown turns into email) points at a PNG copy of
each chart; the web pages keep the SVG. Each PNG is 1200 px wide, Buttondown's recommended maximum, which is 2x an
email's ~600 px column. Rendering uses headless Edge or Chrome, so the text is drawn the way a browser draws it.

charts/png-manifest.json records the SVG's sha256 and the PNG's size; scripts/check_feed.py fails the build when an
SVG has changed since its PNG was made. Re-run this after adding or editing a chart:

    python scripts/render_chart_pngs.py            # from site/; renders only what is missing or stale
    python scripts/render_chart_pngs.py --all      # re-render everything
"""

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

CHARTS = Path(__file__).resolve().parent.parent / "public" / "charts"
MANIFEST = CHARTS / "png-manifest.json"
WIDTH = 1200
BROWSERS = [
    os.environ.get("CHART_BROWSER", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def svg_size(path: Path) -> tuple[float, float]:
    head = re.search(r"<svg\b[^>]*>", path.read_text(encoding="utf-8"))
    box = head and re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"', head.group(0))
    if not box:
        sys.exit(f"render_chart_pngs: {path.name} has no viewBox")
    return float(box.group(1)), float(box.group(2))


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"render_chart_pngs: {path.name} is not a PNG")
    return struct.unpack(">II", data[16:24])


def render(browser: str, svg: Path, png: Path) -> tuple[int, int]:
    w, h = svg_size(svg)
    scale = WIDTH / w
    css_h = round(h)
    # A wrapper page pins the SVG to its viewBox width, so SVGs with and without width/height render the same.
    page = (
        "<!doctype html><meta charset='utf-8'><style>html,body{margin:0;background:#fff}"
        f"img{{display:block;width:{w}px;height:{h}px}}</style><img src='{svg.as_uri()}'>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        wrapper = Path(tmp) / "chart.html"
        wrapper.write_text(page, encoding="utf-8")
        subprocess.run(
            [
                browser, "--headless", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                f"--force-device-scale-factor={scale}", f"--window-size={round(w)},{css_h}",
                f"--screenshot={png}", wrapper.as_uri(),
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120,
        )
    return png_size(png)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--all", action="store_true", help="re-render every chart, not only missing or stale ones")
    args = parser.parse_args()
    browser = next((b for b in BROWSERS if b and Path(b).is_file()), None)
    if not browser:
        sys.exit("render_chart_pngs: no Edge or Chrome found; set CHART_BROWSER to its path")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    svgs = sorted(CHARTS.glob("*.svg"))
    rendered = 0
    for svg in svgs:
        png = svg.with_suffix(".png")
        digest = sha256(svg)
        entry = manifest.get(svg.name)
        if not args.all and entry and entry.get("svg_sha256") == digest and png.exists():
            continue
        pw, ph = render(browser, svg, png)
        if pw != WIDTH or ph > WIDTH:
            sys.exit(f"render_chart_pngs: {png.name} came out {pw}x{ph}, expected {WIDTH} wide and at most {WIDTH} tall")
        manifest[svg.name] = {"png": png.name, "svg_sha256": digest, "width": pw, "height": ph}
        rendered += 1
        print(f"rendered {png.name} {pw}x{ph}")
    for name in [n for n in manifest if not (CHARTS / n).exists()]:
        del manifest[name]
    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"render_chart_pngs: {rendered} rendered, {len(svgs)} charts in the manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
