"""Textual TUI app. Run: python -m src.cli tui"""

from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, RichLog, Static, TabbedContent, TabPane

from .. import ai_client, mode_direct, mode_selector
from ..cleaner import clean_html, reduction_ratio, to_markdown
from ..fetcher import fetch
from .widgets.form import RunRequest, ScraperForm
from .widgets.viewer import ResultViewer

MAX_CHARS = 40000


class ScraperApp(App):
    """Runner + live log + JSON result viewer."""

    TITLE = "AI Scraper"
    SUB_TITLE = "idle"

    CSS = """
    #status { dock: bottom; height: 1; padding: 0 1; background: $panel; color: $text-muted; }
    #log { height: 1fr; }
    """

    BINDINGS = [
        ("ctrl+r", "run", "Run"),
        ("ctrl+s", "save", "Save JSON"),
        ("ctrl+l", "clear_log", "Clear log"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="tab-runner"):
            with TabPane("Runner", id="tab-runner"):
                yield VerticalScroll(ScraperForm(id="form"))
            with TabPane("Logs", id="tab-logs"):
                yield RichLog(id="log", markup=True, wrap=True, highlight=True)
            with TabPane("Result", id="tab-result"):
                yield ResultViewer(id="viewer")
        yield Static("ready", id="status")
        yield Footer()

    # --- helpers callable from the worker thread via call_from_thread ---

    def log_line(self, text: str) -> None:
        self.query_one("#log", RichLog).write(text)

    def set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)
        self.sub_title = text

    def show_result(self, result: Any) -> None:
        self.query_one("#viewer", ResultViewer).load(result)
        self.query_one(TabbedContent).active = "tab-result"

    # --- actions ---

    def action_run(self) -> None:
        self.query_one("#form", ScraperForm).submit()

    def action_clear_log(self) -> None:
        self.query_one("#log", RichLog).clear()

    def action_save(self) -> None:
        try:
            path = self.query_one("#viewer", ResultViewer).save()
        except ValueError as exc:
            self.notify(str(exc), severity="warning")
            return
        self.notify(f"saved {path}")
        self.log_line(f"[green]saved[/] {path}")

    # --- worker ---

    def on_scraper_form_submitted(self, event: ScraperForm.Submitted) -> None:
        self.query_one(TabbedContent).active = "tab-logs"
        self.query_one("#form", ScraperForm).set_busy(True)
        self.run_scrape(event.request)

    def run_scrape(self, request: RunRequest) -> None:
        self.run_worker(
            lambda: self._scrape(request),
            thread=True,
            exclusive=True,
            group="scrape",
            name="scrape",
        )

    def _scrape(self, req: RunRequest) -> None:
        """Blocking pipeline; runs in a worker thread."""
        call = self.call_from_thread
        try:
            call(self.set_status, f"fetching {req.url}")
            call(self.log_line, f"[cyan]fetch[/] {req.url} render={req.render}")
            res = fetch(req.url, render=req.render)
            call(self.log_line, f"[cyan]engine[/] {res.engine} status={res.status} chars={len(res.html)}")

            if req.mode == "direct":
                markdown = to_markdown(res.html, max_chars=MAX_CHARS)
                ratio = reduction_ratio(res.html, markdown)
                call(self.log_line, f"[cyan]clean[/] markdown={len(markdown)} reduction={ratio:.1%}")
                call(self.set_status, f"{res.engine} | reduction {ratio:.1%} | asking LLM")
                reply = ai_client.complete(
                    mode_direct.SYSTEM, mode_direct.build_prompt(markdown, req.prompt)
                )
                result: Any = {
                    "url": req.url,
                    "engine": res.engine,
                    "reduction": round(ratio, 3),
                    "data": ai_client.extract_json(reply),
                }
                done = f"{res.engine} | reduction {ratio:.1%} | done"
            else:
                fields = [f.strip() for f in req.prompt.replace("\n", ",").split(",") if f.strip()]
                reduced = clean_html(res.html)[:30000]
                ratio = reduction_ratio(res.html, reduced)
                call(self.log_line, f"[cyan]clean[/] html={len(reduced)} reduction={ratio:.1%}")
                call(self.set_status, f"{res.engine} | generating selectors for {len(fields)} fields")
                user = (
                    f"Target fields: {', '.join(fields)}\n\n"
                    f"Sample page URL: {req.url}\n\nReduced HTML:\n---\n{reduced}\n---"
                )
                config = ai_client.extract_json(
                    ai_client.complete(mode_selector.SYSTEM, user)
                )
                if not isinstance(config.get("fields"), dict) or not config["fields"]:
                    raise ValueError(f"LLM returned no usable fields: {config!r}")
                config["sample_url"] = req.url
                call(self.log_line, "[cyan]apply[/] running generated config against the page")
                result = {"config": config, "preview": mode_selector.apply_config(res.html, config)}
                done = f"{res.engine} | {len(config['fields'])} selectors | done"

            call(self.log_line, "[green]ok[/] result ready (Ctrl+S to save)")
            call(self.set_status, done)
            call(self.show_result, result)
        except Exception as exc:
            call(self.log_line, f"[red]error[/] {type(exc).__name__}: {exc}")
            call(self.set_status, f"error: {type(exc).__name__}")
        finally:
            call(self.query_one("#form", ScraperForm).set_busy, False)


def run() -> None:
    ScraperApp().run()


if __name__ == "__main__":
    run()
