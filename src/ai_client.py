"""OpenAI-compatible LLM client (9Router / OpenRouter / OpenAI) with retry backoff."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI

_ENV_LOADED = False


def _load_env() -> None:
    """Minimal .env loader (avoids a python-dotenv dependency)."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    path = Path.cwd() / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip("'\""))


def get_client() -> tuple[OpenAI, str]:
    """Return (client, model) from OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL."""
    _load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set (see .env.example)")
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    return client, os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def complete(
    system: str,
    user: str,
    *,
    model: str | None = None,
    temperature: float = 0.0,
    max_retries: int = 4,
) -> str:
    """Chat completion with exponential backoff on transient errors."""
    client, default_model = get_client()
    delay = 1.0
    last: Exception | None = None
    for _ in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model or default_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:  # rate limit / 5xx / transport
            last = exc
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last}") from last


def extract_json(text: str):
    """Parse JSON out of an LLM reply, tolerating ```json fences and prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON found in LLM reply: {text[:200]!r}")
    return json.loads(match.group(0))
