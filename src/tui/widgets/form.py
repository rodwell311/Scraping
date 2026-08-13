"""Form widget: URL, prompt/fields, mode select, run button."""

from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Checkbox, Input, Label, Select, TextArea

MODES = [("Direct extraction (LLM -> JSON)", "direct"), ("Generate CSS selector config", "selector")]


@dataclass
class RunRequest:
    """Validated form payload handed to the app worker."""

    url: str
    mode: str
    prompt: str
    render: bool


class ScraperForm(Vertical):
    """Input panel. Posts ScraperForm.Submitted with a RunRequest."""

    DEFAULT_CSS = """
    ScraperForm { padding: 1 2; height: auto; }
    ScraperForm Label { margin-top: 1; }
    ScraperForm #prompt { height: 6; }
    ScraperForm #actions { height: auto; margin-top: 1; }
    ScraperForm #run { margin-right: 2; }
    ScraperForm #error { color: $error; height: auto; }
    """

    class Submitted(Message):
        def __init__(self, request: RunRequest) -> None:
            super().__init__()
            self.request = request

    def compose(self) -> ComposeResult:
        yield Label("URL")
        yield Input(placeholder="https://example.com", id="url")
        yield Label("Mode")
        yield Select(MODES, value="direct", allow_blank=False, id="mode")
        yield Label("Prompt (direct) / comma-separated fields (selector)")
        yield TextArea(id="prompt")
        yield Horizontal(
            Button("Run", variant="primary", id="run"),
            Checkbox("Force Playwright render", id="render"),
            id="actions",
        )
        yield Label("", id="error")

    def on_mount(self) -> None:
        self.query_one("#url", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            event.stop()
            self.submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.submit()

    def submit(self) -> None:
        """Validate and post Submitted, or show an inline error."""
        url = self.query_one("#url", Input).value.strip()
        prompt = self.query_one("#prompt", TextArea).text.strip()
        mode = str(self.query_one("#mode", Select).value)
        error = self.query_one("#error", Label)

        if not url.startswith(("http://", "https://")):
            error.update("URL must start with http:// or https://")
            return
        if not prompt:
            what = "a prompt" if mode == "direct" else "at least one field name"
            error.update(f"Enter {what}.")
            return

        error.update("")
        self.post_message(
            self.Submitted(
                RunRequest(
                    url=url,
                    mode=mode,
                    prompt=prompt,
                    render=self.query_one("#render", Checkbox).value,
                )
            )
        )

    def set_busy(self, busy: bool) -> None:
        self.query_one("#run", Button).disabled = busy
