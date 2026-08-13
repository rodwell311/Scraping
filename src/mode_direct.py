"""Mode 2: Direct zero-schema extraction. HTML -> Markdown -> LLM -> JSON."""

from __future__ import annotations

from . import ai_client
from .cleaner import reduction_ratio, to_markdown
from .fetcher import fetch

SYSTEM = (
    "You extract structured data from webpage content. "
    "Reply with JSON only: no prose, no markdown fences. "
    "Use null for fields you cannot find. Never invent values."
)


def build_prompt(markdown: str, instruction: str, schema: dict | None = None) -> str:
    parts = [f"Task: {instruction}"]
    if schema:
        import json

        parts.append(f"Return JSON matching this schema:\n{json.dumps(schema, indent=2)}")
    parts.append(f"Page content:\n---\n{markdown}\n---")
    return "\n\n".join(parts)


def extract(
    url: str,
    instruction: str,
    *,
    schema: dict | None = None,
    render: bool = False,
    max_chars: int = 40000,
    model: str | None = None,
) -> dict:
    """Fetch, clean, and ask the LLM for structured JSON."""
    res = fetch(url, render=render)
    markdown = to_markdown(res.html, max_chars=max_chars)
    reply = ai_client.complete(
        SYSTEM, build_prompt(markdown, instruction, schema), model=model
    )
    return {
        "url": url,
        "engine": res.engine,
        "reduction": round(reduction_ratio(res.html, markdown), 3),
        "data": ai_client.extract_json(reply),
    }
