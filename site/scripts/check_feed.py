"""Check the built newsletter feed (site/dist/newsletter/rss.xml) before the site deploys.

Fails (exit 1) if the feed is missing or doesn't parse, if its item count isn't the number of issue files, if an item
lacks its full content, if an item lacks its date or description, if any link or image in it is relative,
misses the /rnd base or names a page the build didn't make, if it carries any author field
other than dc:creator mcp-tool-shop, if its HTML has a <div> or a class attribute (it is also the
email edition), if an image in it is an SVG (email clients don't show SVG), or if a chart's PNG
is missing, older than its SVG, or not the one recorded (charts/png-manifest.json; re-run
scripts/render_chart_pngs.py), or if an item's HTML is over 90,000 bytes (Gmail clips an email at about 102 KB).
Usage, from site/: python scripts/check_feed.py
With --charts-only it checks only the chart PNGs, which needs no build; PR CI runs it that way.
"""
import hashlib
import json
import pathlib
import re
import struct
import sys
import urllib.parse
import xml.etree.ElementTree as ET

SITE = "https://mcp-tool-shop-org.github.io/rnd/"
STUDIO = "mcp-tool-shop"
HOST = "https://mcp-tool-shop-org.github.io/"
MAX_EMAIL_BYTES = 90_000
NS = {"content": "http://purl.org/rss/1.0/modules/content/", "dc": "http://purl.org/dc/elements/1.1/",
      "atom": "http://www.w3.org/2005/Atom"}

here = pathlib.Path(__file__).resolve().parent.parent
feed = here / "dist" / "newsletter" / "rss.xml"
issues = sorted((here / "src" / "content" / "docs" / "newsletter").glob("issue-*.md"))
errors = []
dist = here / "dist"
# Top-level folders of this site's build; a host URL starting with one of them has lost its /rnd base.
TOP_LEVEL = {p.name for p in dist.iterdir()} if dist.is_dir() else set()


def built(url: str) -> bool:
    """True when a SITE URL names a page or file in dist (a fragment or query is ignored)."""
    path = urllib.parse.unquote(url[len(SITE):].split("#")[0].split("?")[0])
    target = dist / path
    return target.is_file() or (target / "index.html").is_file()


def svg_digest(svg: pathlib.Path) -> str:
    """sha256 of an SVG with CRLF read as LF, so a Windows working copy and CI's LF checkout agree."""
    return hashlib.sha256(svg.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def chart_errors() -> list[str]:
    """Every chart has the PNG made from its current SVG, at most 1200x1200 (Buttondown's recommended maximum)."""
    found = []
    charts = here / "public" / "charts"
    manifest_path = charts / "png-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    for svg in sorted(charts.glob("*.svg")):
        entry = manifest.get(svg.name)
        png = charts / (entry or {}).get("png", svg.with_suffix(".png").name)
        if not entry or not png.is_file():
            found.append(f"chart {svg.name} has no PNG; run scripts/render_chart_pngs.py")
        elif entry.get("svg_sha256") != svg_digest(svg):
            found.append(f"chart {svg.name} changed since its PNG was made; run scripts/render_chart_pngs.py")
        elif entry.get("png_sha256") != hashlib.sha256(png.read_bytes()).hexdigest():
            found.append(f"chart {png.name} isn't the PNG the manifest recorded; run scripts/render_chart_pngs.py")
        else:
            w, h = struct.unpack(">II", png.read_bytes()[16:24])
            if (w, h) != (entry.get("width"), entry.get("height")) or w > 1200 or h > 1200:
                found.append(f"chart {png.name} is {w}x{h}; expected the manifest's size, at most 1200x1200")
    return found


if "--charts-only" in sys.argv[1:]:
    errors = chart_errors()
    if errors:
        print("check_feed: FAIL", *errors, sep="\n  ")
        sys.exit(1)
    print("check_feed: OK, every chart has its current PNG")
    sys.exit(0)

if not feed.is_file():
    sys.exit(f"check_feed: {feed} is missing; run the build first")
try:
    channel = ET.parse(feed).getroot().find("channel")
except ET.ParseError as e:
    sys.exit(f"check_feed: rss.xml doesn't parse: {e}")

items = channel.findall("item")
if len(items) != len(issues):
    errors.append(f"{len(items)} feed items, but {len(issues)} issue files")
# The feed names its author only as the studio, in dc:creator; it carries no address fields at all.
for tag in ("managingEditor", "webMaster", "author"):
    if channel.find(tag) is not None or any(i.find(tag) is not None for i in channel.findall("item")):
        errors.append(f"the feed carries a <{tag}> field; it should name only {STUDIO}, in dc:creator")
self_link = channel.find("atom:link", NS)
if self_link is None or self_link.get("href") != SITE + "newsletter/rss.xml":
    errors.append("the atom:link self href isn't the feed's own URL")

for item in items:
    title = item.findtext("title") or "(untitled)"
    if not (item.findtext("link") or "").startswith(SITE):
        errors.append(f"{title}: link isn't under {SITE}")
    if (item.findtext("dc:creator", namespaces=NS) or "") != STUDIO:
        errors.append(f"{title}: dc:creator isn't {STUDIO}")
    html = item.findtext("content:encoded", namespaces=NS) or ""
    if len(html) < 200:
        errors.append(f"{title}: content:encoded is missing or empty")
    # Gmail clips an email whose HTML passes about 102 KB, and a daily issue holds several articles.
    size = len(html.encode("utf-8"))
    if size > MAX_EMAIL_BYTES:
        errors.append(f"{title}: content is {size} bytes, over {MAX_EMAIL_BYTES}; Gmail would clip the email")
    for field in ("pubDate", "description"):
        if not (item.findtext(field) or "").strip():
            errors.append(f"{title}: <{field}> is missing or empty")
    for url in re.findall(r'(?:href|src)="([^"]*)"', html):
        if not url.startswith(("https://", "http://", "mailto:")):
            errors.append(f"{title}: relative URL in content: {url}")
        # A link to this site that misses the /rnd base, or names a page or file the build didn't make, is broken.
        elif url.startswith(HOST) and not url.startswith(SITE) and url.split("/")[3] in TOP_LEVEL:
            errors.append(f"{title}: link to this site without the /rnd base: {url}")
        elif url.startswith(SITE) and not built(url):
            errors.append(f"{title}: links to a page or file the build didn't make: {url}")
    # The feed is also the email edition (Buttondown): classless <div>s can error in its editor, and class names do
    # nothing in email, where styles must be inline.
    if re.search(r"<div[\s>]", html):
        errors.append(f"{title}: content has a <div>; email HTML should carry none")
    if " class=" in html:
        errors.append(f"{title}: content has a class attribute; email styles must be inline")
    # Gmail and Outlook don't show SVG images.
    for src in re.findall(r'<img[^>]*\ssrc="([^"]*)"', html):
        if urllib.parse.urlsplit(src).path.lower().endswith(".svg"):
            errors.append(f"{title}: image is an SVG, which email clients don't show: {src}")

errors += chart_errors()

if errors:
    print("check_feed: FAIL", *errors, sep="\n  ")
    sys.exit(1)
print(f"check_feed: OK, {len(items)} items, one per issue file")
