"""Smoke test: no network, no LLM. python tests/smoke.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app
from src import ai_client, cleaner, fetcher, mode_selector

SAMPLE = """<html><head><style>.x{color:red}</style><script>var a=1;</script></head>
<body><nav>menu junk</nav>
<h1 class="title">Novel Alpha</h1>
<ul class="chapters">
  <li class="item"><a class="ch" href="/c/1">Chapter 1</a><span class="d">2026-01-01</span></li>
  <li class="item"><a class="ch" href="/c/2">Chapter 2</a><span class="d">2026-01-02</span></li>
</ul>
<footer>footer junk</footer></body></html>"""

CONFIG = {
    "container": "li.item",
    "fields": {
        "title": {"selector": "a.ch", "attr": "text"},
        "link": {"selector": "a.ch", "attr": "href"},
        "date": {"selector": "span.d", "attr": "text"},
    },
}


def test_cleaner() -> None:
    reduced = cleaner.clean_html(SAMPLE)
    assert "var a=1" not in reduced, "script not stripped"
    assert "menu junk" not in reduced and "footer junk" not in reduced, "nav/footer not stripped"
    assert "Novel Alpha" in reduced, "content lost"

    md = cleaner.to_markdown(SAMPLE)
    assert "Novel Alpha" in md, f"title missing from markdown: {md!r}"
    assert cleaner.reduction_ratio(SAMPLE, md) > 0.5, "reduction too low"


def test_fetcher_guard() -> None:
    try:
        fetcher.fetch("ftp://example.com")
    except ValueError:
        return
    raise AssertionError("fetch accepted a non-http scheme")


def test_selector_engine() -> None:
    rows = mode_selector.apply_config(SAMPLE, CONFIG)
    assert rows == [
        {"title": "Chapter 1", "link": "/c/1", "date": "2026-01-01"},
        {"title": "Chapter 2", "link": "/c/2", "date": "2026-01-02"},
    ], rows

    single = mode_selector.apply_config(SAMPLE, {"fields": {"t": {"selector": "h1.title"}}})
    assert single == {"t": "Novel Alpha"}, single

    missing = mode_selector.apply_config(SAMPLE, {"fields": {"t": {"selector": ".nope"}}})
    assert missing == {"t": None}, missing


def test_config_roundtrip() -> None:
    with TemporaryDirectory() as tmp:
        d = Path(tmp)
        mode_selector.save_config("novel", CONFIG, directory=d)
        assert mode_selector.load_config("novel", directory=d) == CONFIG
    for bad in ("../evil", "a/b", ""):
        try:
            mode_selector.save_config(bad, CONFIG)
        except ValueError:
            continue
        raise AssertionError(f"save_config accepted unsafe name {bad!r}")


def test_json_parsing() -> None:
    assert ai_client.extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert ai_client.extract_json('here you go: [{"a": 2}] done') == [{"a": 2}]
    assert ai_client.extract_json('{"a": null}') == {"a": None}
    try:
        ai_client.extract_json("no json at all")
    except ValueError:
        return
    raise AssertionError("extract_json accepted junk")


def test_api() -> None:
    c = TestClient(app)
    assert c.get("/health").json() == {"status": "ok"}
    assert c.post("/api/scrape", json={"urls": ["https://e.com"]}).status_code == 400
    assert c.post("/api/extract", json={"url": "not-a-url", "prompt": "x"}).status_code == 422
    assert "/api/generate-selector" in json.dumps(c.get("/openapi.json").json())


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
