# ⚡ AI-Powered Universal Web Scraper

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

An intelligent, hybrid web scraping engine designed for maximum efficiency. It combines high-speed TLS impersonation (`curl_cffi`), automatic Playwright headless fallback, HTML token reduction (~70-80% compression), and OpenAI-compatible LLMs (9Router, OpenRouter, OpenAI, Ollama).

---

## 🔥 Key Features

- **🛡️ Dual-Engine Fetcher**: Fast `curl_cffi` (Chrome 124 TLS impersonation) for static & anti-bot bypass, with seamless fallback to `Playwright` for JavaScript-rendered SPA sites.
- **🧹 Token-Optimized DOM Cleaner**: Automatically strips noise tags (`<script>`, `<style>`, `<nav>`, `<footer>`) and converts HTML to clean Markdown before feeding to the LLM, reducing token cost by **70–80%**.
- **🧠 Mode 1: Auto-Selector Generator (Zero-Token Bulk Scrape)**: Asks the LLM **once** to analyze a sample page and generate CSS selectors. Subsequent 1,000s of pages are scraped using pure Python CSS selectors without consuming any extra AI tokens.
- **🎯 Mode 2: Direct AI Extraction**: Send any page + natural language prompt or JSON schema to extract complex, un-structured dynamic data on the fly.
- **🌐 Provider Agnostic**: Works out of the box with any OpenAI-compatible endpoint (`OPENAI_BASE_URL` & `OPENAI_API_KEY`).
- **💻 Triple Interfaces**: Interactive Terminal User Interface (TUI via `textual`), complete CLI tool (`ai-scrape`), and FastAPI REST endpoints with OpenAPI / Swagger UI.

---

## 🏗️ Architecture Flow

```text
               ┌──────────────────────┐
               │     Target URL       │
               └──────────┬───────────┘
                          │
                 [ Fetcher Engine ]
        curl_cffi (Fast) ──► Playwright (Fallback if JS/Empty)
                          │
                 [ DOM Cleaner ]
        Strips Noise Tags ──► Reduces Tokens by ~75% ──► Markdown
                          │
       ┌──────────────────┴──────────────────┐
       ▼                                     ▼
[ Mode 1: Auto-Selector ]            [ Mode 2: Direct Extract ]
• 1x LLM Call → CSS Config           • Markdown + Prompt → LLM
• 1,000+ Pages → Pure CSS            • Returns Validated JSON
  (Zero-Token Cost)
```

---

## 🚀 Quickstart

### 1. Installation

```bash
# Clone repository
git clone git@github.com:rodwell311/Scraping.git
cd Scraping

# Create & activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration

Copy `.env.example` to `.env` and set your OpenAI-compatible credentials (e.g. 9Router, OpenRouter, or OpenAI):

```bash
cp .env.example .env
```

```env
OPENAI_BASE_URL="http://localhost:20128/v1"
OPENAI_API_KEY="sk-your-key-here"
OPENAI_MODEL="gpt-4o-mini"
```

---

## 💻 Usage

### 🖥️ Interactive TUI (Terminal User Interface)

Launch the full-screen interactive TUI dashboard:

```bash
python -m src.cli tui
```

Features included in the TUI:
- **Runner Dashboard**: Input URL, switch between Direct AI & Auto-Selector modes, set natural language prompts.
- **Collapsible JSON Tree Viewer**: View, inspect, and expand extracted JSON data with syntax highlighting.
- **Live Logs Console**: Monitor real-time fetching status (`curl_cffi` vs `Playwright`) and token compression ratio.
- **Shortcuts**: `Ctrl+R` (Run scrape), `Ctrl+S` (Export/Save JSON to `output/`), `Ctrl+L` (Clear log), `Ctrl+Q` (Quit).

---

### 🛠️ CLI Interface

#### Mode 1: Direct AI Extraction
Extract structured JSON from any webpage using natural language:

```bash
python -m src.cli extract "https://news.ycombinator.com" \
  --prompt "Extract top 5 news titles, links, and points"
```

#### Mode 2: Auto-Selector & Zero-Token Scrape

```bash
# Step 1: Generate CSS Selectors via AI (1x LLM Call)
python -m src.cli gen-selector "https://news.ycombinator.com" \
  --fields title,link \
  --output selector_config.json

# Step 2: Bulk Scrape 100s of Pages (0 AI Tokens Used!)
python -m src.cli scrape "https://news.ycombinator.com" \
  --config-file selector_config.json
```

#### Extract Raw Cleaned Markdown
Inspect how the page is cleaned before being sent to the AI:

```bash
python -m src.cli markdown "https://example.com"
```

---

### 🌐 REST API (FastAPI)

Start the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

Access Interactive Swagger Documentation at `http://localhost:8000/docs`.

#### Endpoints:
- `POST /api/extract` — Direct AI extraction (`{ "url": "...", "prompt": "..." }`)
- `POST /api/generate-selector` — Generate CSS selector JSON schema
- `POST /api/scrape` — Fast CSS-based scraping without LLM

---

## 🧪 Testing

Run built-in offline smoke tests to verify all components:

```bash
python tests/smoke.py      # core: cleaner, selector engine, API
python tests/tui_smoke.py  # TUI: headless Textual pilot (no network, no LLM)
```

Expected Output:
```text
PASS test_api
PASS test_cleaner
PASS test_config_roundtrip
PASS test_fetcher_guard
PASS test_json_parsing
PASS test_selector_engine

6/6 passed
```

---

## 📄 License

[MIT](LICENSE) © Rodwell
