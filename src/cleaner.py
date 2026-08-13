"""DOM cleaner: strip noise tags, convert HTML to compact Markdown."""

from __future__ import annotations

import html2text
from bs4 import BeautifulSoup

NOISE_TAGS = (
    "script", "style", "noscript", "iframe", "svg", "canvas", "template",
    "nav", "footer", "header", "aside", "form", "button", "input", "select",
)
NOISE_ATTRS_KEEP = {"href", "src", "alt", "title", "class", "id"}


def clean_html(html: str) -> str:
    """Remove noise tags/attrs. Returns reduced HTML (still parseable by selectors)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(list(NOISE_TAGS)):
        tag.decompose()
    for el in soup.find_all(True):
        el.attrs = {k: v for k, v in el.attrs.items() if k in NOISE_ATTRS_KEEP}
    return str(soup)


def to_markdown(html: str, *, max_chars: int = 40000, ignore_links: bool = False) -> str:
    """Clean HTML then convert to Markdown. Truncated at max_chars to bound tokens."""
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.ignore_images = True
    h.ignore_emphasis = True
    h.body_width = 0
    md = h.handle(clean_html(html))
    md = "\n".join(line.rstrip() for line in md.splitlines() if line.strip())
    return md[:max_chars]


def reduction_ratio(raw_html: str, markdown: str) -> float:
    """Fraction of characters removed, 0.0-1.0."""
    if not raw_html:
        return 0.0
    return 1.0 - (len(markdown) / len(raw_html))
