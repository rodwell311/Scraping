"""Viewer widget: collapsible JSON tree + syntax-highlighted raw JSON + save to file."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode

OUTPUT_DIR = Path("output")


def _label(key: str | int, value: object) -> str:
    if isinstance(value, dict):
        return f"{key} {{{len(value)}}}"
    if isinstance(value, list):
        return f"{key} [{len(value)}]"
    return f"{key}: {value!r}"


def _populate(node: TreeNode, value: object) -> None:
    """Recursively mirror a JSON value into tree nodes."""
    items: list[tuple[str | int, object]]
    if isinstance(value, dict):
        items = list(value.items())
    elif isinstance(value, list):
        items = list(enumerate(value))
    else:
        return
    for key, child in items:
        if isinstance(child, (dict, list)):
            branch = node.add(_label(key, child))
            _populate(branch, child)
        else:
            node.add_leaf(_label(key, child))


class ResultViewer(Horizontal):
    """Shows the last result as a tree and as raw JSON. Nothing until load() is called."""

    DEFAULT_CSS = """
    ResultViewer { height: 1fr; }
    ResultViewer #tree { width: 45%; border-right: solid $panel; }
    ResultViewer #raw-scroll { width: 1fr; padding: 0 1; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.result: object | None = None

    def compose(self) -> ComposeResult:
        yield Tree("result", id="tree")
        yield VerticalScroll(Static(id="raw"), id="raw-scroll")

    def load(self, result: object) -> None:
        """Replace the displayed result."""
        self.result = result
        text = json.dumps(result, indent=2, ensure_ascii=False)

        tree = self.query_one("#tree", Tree)
        tree.reset("result")
        _populate(tree.root, result)
        tree.root.expand_all()

        self.query_one("#raw", Static).update(
            Syntax(text, "json", theme="ansi_dark", word_wrap=True)
        )

    def save(self, path: Path | None = None, *, directory: Path = OUTPUT_DIR) -> Path:
        """Write the current result to JSON. Raises ValueError when there is nothing to save."""
        if self.result is None:
            raise ValueError("no result to save")
        if path is None:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"scrape-{stamp}.json"
        path.write_text(
            json.dumps(self.result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return path
