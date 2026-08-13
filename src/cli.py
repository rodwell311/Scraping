"""CLI: python -m src.cli <command> ..."""

from __future__ import annotations

import argparse
import json
import sys

from . import mode_direct, mode_selector
from .cleaner import reduction_ratio, to_markdown
from .fetcher import fetch


def _out(obj) -> None:
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ai-scrape", description="AI-Powered Universal Web Scraper")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="Direct AI extraction (Mode 2)")
    e.add_argument("url")
    e.add_argument("-p", "--prompt", required=True, help="what data to extract")
    e.add_argument("-s", "--schema", help="JSON schema string or @file.json")
    e.add_argument("--render", action="store_true", help="force Playwright")
    e.add_argument("--model")
    e.add_argument("--max-chars", type=int, default=40000)

    g = sub.add_parser("gen-selector", help="Generate CSS selector config (Mode 1)")
    g.add_argument("url")
    g.add_argument("-f", "--fields", required=True, help="comma-separated field names")
    g.add_argument("-o", "--save", help="config name to save under configs/")
    g.add_argument("--render", action="store_true")
    g.add_argument("--model")

    s = sub.add_parser("scrape", help="Bulk scrape using a saved config (no LLM)")
    s.add_argument("urls", nargs="+")
    s.add_argument("-c", "--config", required=True, help="config name or path to .json")
    s.add_argument("--render", action="store_true")

    m = sub.add_parser("markdown", help="Fetch + clean only (no LLM)")
    m.add_argument("url")
    m.add_argument("--render", action="store_true")
    m.add_argument("--max-chars", type=int, default=40000)

    sub.add_parser("tui", help="Launch the interactive Textual TUI")

    a = p.parse_args(argv)

    if a.cmd == "tui":
        from .tui.app import run as run_tui

        run_tui()
        return 0

    if a.cmd == "extract":
        schema = None
        if a.schema:
            raw = open(a.schema[1:], encoding="utf-8").read() if a.schema.startswith("@") else a.schema
            schema = json.loads(raw)
        _out(mode_direct.extract(
            a.url, a.prompt, schema=schema, render=a.render,
            max_chars=a.max_chars, model=a.model,
        ))

    elif a.cmd == "gen-selector":
        fields = [f.strip() for f in a.fields.split(",") if f.strip()]
        config = mode_selector.generate_config(a.url, fields, render=a.render, model=a.model)
        if a.save:
            print(f"saved: {mode_selector.save_config(a.save, config)}", file=sys.stderr)
        _out(config)

    elif a.cmd == "scrape":
        if a.config.endswith(".json"):
            config = json.load(open(a.config, encoding="utf-8"))
        else:
            config = mode_selector.load_config(a.config)
        _out(mode_selector.scrape(a.urls, config, render=a.render))

    elif a.cmd == "markdown":
        res = fetch(a.url, render=a.render)
        md = to_markdown(res.html, max_chars=a.max_chars)
        print(f"engine={res.engine} reduction={reduction_ratio(res.html, md):.1%}", file=sys.stderr)
        print(md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
