"""Mode 1: AI generates a CSS selector config once; the engine then scrapes without an LLM."""

from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

from . import ai_client
from .cleaner import clean_html
from .fetcher import fetch

CONFIG_DIR = Path("configs")

SYSTEM = (
    "You are a CSS selector engineer. Given reduced HTML and a list of target fields, "
    "return JSON only (no prose, no fences) in exactly this shape:\n"
    '{"container": "<css selector or null>", '
    '"fields": {"<field>": {"selector": "<css>", "attr": "<html attribute or text>"}}}\n'
    'Use "text" as attr for text content. Set container to a repeating-item selector only '
    "when the target is a list; otherwise null. Prefer stable class/id selectors over "
    "nth-child chains."
)


def generate_config(
    url: str,
    fields: list[str],
    *,
    render: bool = False,
    max_chars: int = 30000,
    model: str | None = None,
) -> dict:
    """Ask the LLM once for a selector config from a sample page."""
    res = fetch(url, render=render)
    reduced = clean_html(res.html)[:max_chars]
    user = (
        f"Target fields: {', '.join(fields)}\n\n"
        f"Sample page URL: {url}\n\nReduced HTML:\n---\n{reduced}\n---"
    )
    config = ai_client.extract_json(ai_client.complete(SYSTEM, user, model=model))
    if not isinstance(config.get("fields"), dict) or not config["fields"]:
        raise ValueError(f"LLM returned no usable fields: {config!r}")
    config["sample_url"] = url
    return config


def save_config(name: str, config: dict, *, directory: Path = CONFIG_DIR) -> Path:
    if "/" in name or name in ("", ".", ".."):
        raise ValueError(f"invalid config name: {name!r}")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def load_config(name: str, *, directory: Path = CONFIG_DIR) -> dict:
    if "/" in name or name in ("", ".", ".."):
        raise ValueError(f"invalid config name: {name!r}")
    return json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))


def _value(el, attr: str) -> str | None:
    if el is None:
        return None
    if attr in ("text", "", None):
        return el.get_text(strip=True)
    val = el.get(attr)
    return val if isinstance(val, str) or val is None else " ".join(val)


def apply_config(html: str, config: dict) -> list[dict] | dict:
    """Run a selector config against HTML. Returns a list when container is set."""
    soup = BeautifulSoup(html, "html.parser")
    fields: dict = config.get("fields", {})
    container = config.get("container")

    def row(scope) -> dict:
        out = {}
        for name, spec in fields.items():
            sel = spec.get("selector") if isinstance(spec, dict) else spec
            attr = spec.get("attr", "text") if isinstance(spec, dict) else "text"
            out[name] = _value(scope.select_one(sel) if sel else None, attr)
        return out

    if container:
        return [row(node) for node in soup.select(container)]
    return row(soup)


def scrape(urls: list[str], config: dict, *, render: bool = False) -> list[dict]:
    """Bulk scrape with an existing config. No LLM calls."""
    results = []
    for url in urls:
        try:
            res = fetch(url, render=render)
            results.append({"url": url, "data": apply_config(res.html, config)})
        except Exception as exc:
            results.append({"url": url, "error": str(exc)})
    return results
