"""TUI smoke test: headless Textual pilot, no network, no LLM. python tests/tui_smoke.py"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from textual.widgets import Input, TabbedContent, TextArea

from src.tui.app import ScraperApp
from src.tui.widgets.form import ScraperForm
from src.tui.widgets.viewer import ResultViewer

RESULT = {
    "url": "https://e.com",
    "engine": "curl_cffi",
    "reduction": 0.9,
    "data": [{"title": "Chapter 1", "link": "/c/1"}, {"title": "Chapter 2", "link": None}],
}


async def _run(check, app_class=ScraperApp) -> None:
    app = app_class()
    async with app.run_test() as pilot:
        await check(app, pilot)


class RecordingApp(ScraperApp):
    """Captures RunRequests instead of running the scraper."""

    requests: list

    def __init__(self) -> None:
        super().__init__()
        self.requests = []

    def run_scrape(self, request) -> None:
        self.requests.append(request)


def test_viewer_tree_and_save() -> None:
    async def check(app, pilot):
        viewer = app.query_one("#viewer", ResultViewer)
        viewer.load(RESULT)
        await pilot.pause()

        labels = [str(n.label) for n in viewer.query_one("#tree").root.children]
        assert any("data [2]" in s for s in labels), labels
        assert any("engine: 'curl_cffi'" in s for s in labels), labels

        with TemporaryDirectory() as tmp:
            path = viewer.save(directory=Path(tmp))
            assert json.loads(path.read_text()) == RESULT, "saved JSON mismatch"

    asyncio.run(_run(check))


def test_viewer_save_without_result() -> None:
    async def check(app, pilot):
        try:
            app.query_one("#viewer", ResultViewer).save()
        except ValueError:
            return
        raise AssertionError("save() accepted an empty viewer")

    asyncio.run(_run(check))


def test_form_rejects_bad_url() -> None:
    async def check(app, pilot):
        form = app.query_one("#form", ScraperForm)

        form.query_one("#url", Input).value = "not-a-url"
        form.query_one("#prompt", TextArea).text = "title"
        form.submit()
        await pilot.pause()
        assert not app.requests, "bad URL was submitted"
        assert "http" in str(form.query_one("#error").renderable)

        form.query_one("#url", Input).value = "https://e.com"
        form.query_one("#prompt", TextArea).text = ""
        form.submit()
        await pilot.pause()
        assert not app.requests, "empty prompt was submitted"

    asyncio.run(_run(check, RecordingApp))


def test_form_submits_valid_request() -> None:
    async def check(app, pilot):
        form = app.query_one("#form", ScraperForm)
        form.query_one("#url", Input).value = "https://e.com"
        form.query_one("#prompt", TextArea).text = "title, link"
        form.submit()
        await pilot.pause()

        assert len(app.requests) == 1, app.requests
        req = app.requests[0]
        assert (req.url, req.mode, req.render) == ("https://e.com", "direct", False), req
        assert req.prompt == "title, link", req
        assert app.query_one(TabbedContent).active == "tab-logs"

    asyncio.run(_run(check, RecordingApp))


def test_bindings_and_tabs() -> None:
    async def check(app, pilot):
        tabs = app.query_one(TabbedContent)
        assert tabs.active == "tab-runner", tabs.active
        keys = {b[0] if isinstance(b, tuple) else b.key for b in ScraperApp.BINDINGS}
        assert {"ctrl+s", "ctrl+r", "ctrl+q"} <= keys, keys

        app.query_one("#viewer", ResultViewer).load(RESULT)
        app.log_line("hello")
        app.set_status("busy")
        await pilot.pause()
        assert app.sub_title == "busy"

    asyncio.run(_run(check))


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
