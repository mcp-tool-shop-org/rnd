"""Check the built newsletter feed (site/dist/newsletter/rss.xml) before the site deploys.

Fails (exit 1) if the feed is missing or doesn't parse, if its item count isn't the number of issue files, if an item
lacks its full content, if an item lacks its date or description, if any link or image in it is relative,
misses the /rnd base or names a page the build didn't make, or if it carries any author field
other than dc:creator mcp-tool-shop. Usage, from site/: python scripts/check_feed.py
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SITE = "https://mcp-tool-shop-org.github.io/rnd/"
STUDIO = "mcp-tool-shop"
HOST = "https://mcp-tool-shop-org.github.io/"
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
    path = url[len(SITE):].split("#")[0].split("?")[0]
    target = dist / path
    return target.is_file() or (target / "index.html").is_file()

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

if errors:
    print("check_feed: FAIL", *errors, sep="\n  ")
    sys.exit(1)
print(f"check_feed: OK, {len(items)} items, one per issue file")
