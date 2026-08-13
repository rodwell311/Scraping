# PRD: AI-Powered Universal Web Scraper (AI-Scraper)

**Versi:** 0.1 (draft)  
**Tanggal:** 13 Agustus 2026  
**Type:** cli & api  

---

## 1. Overview
Tool web scraping universal berbasis Python yang terintegrasi dengan OpenAI-compatible LLM API (seperti 9Router lokal, OpenRouter, atau OpenAI). Tool ini menggabungkan teknik fetching cepat (`curl_cffi` dengan fallback `Playwright`), DOM cleaner (konversi HTML ke Markdown bersih), serta 2 mode AI scraping: **Auto-Selector Generator** (untuk bulk scraping seperti novel/katalog) dan **Direct Zero-Schema Extraction** (untuk ekstraksi data arbitrer via LLM).

## 2. Goals
- Ekstraksi data dari website manapun cukup dengan memberikan URL dan deskripsi data yang diinginkan.
- Mode Hybrid: AI hanya dipakai 1x untuk generate CSS selector pada bulk scraping (hemat token & super cepat).
- Support OpenAI-Compatible API (konfigurasi via `OPENAI_BASE_URL` dan `OPENAI_API_KEY`).
- Menyediakan CLI interface yang pipeable dan REST API (FastAPI) untuk penggunaan terintegrasi.
- Waktu reduksi DOM HTML -> Markdown mampu memotong token > 80%.

## 3. Non-Goals (Out of Scope v1)
- UI Dashboard kompleks (hanya CLI & Swagger UI FastAPI).
- Paid Captcha Solving Integration (2Captcha/CapSolver) — cukup stealth browser fallback.
- Distributed worker cluster (Celery/Redis) — Cukup async Python task queue.

## 4. User Persona
**User Utama:** Developer / Data Scientist / Self-Host Enthusiast.  
**Kebutuhan:** Membutuhkan data dari berbagai website tanpa harus menulis CSS Selector manual satu per satu, hemat token AI, dan bisa dijalankan via CLI maupun API.

## 5. MVP Features
| # | Fitur | Description | Priority |
|---|---|---|---|
| F-01 | Dual Fetcher | `curl_cffi` (fast/anti-TLS block) + fallback `Playwright` jika butuh JS render | Must |
| F-02 | DOM Cleaner | Bersihkan tag non-konten (script, style, nav, footer) -> Convert HTML ke Markdown | Must |
| F-03 | OpenAI API Client | Provider-agnostic OpenAI client (`BASE_URL` & `API_KEY` configurable) | Must |
| F-04 | Mode 1: Auto-Selector | AI membuat CSS Selector config JSON dari 1 halaman -> dipakai bulk scrape | Must |
| F-05 | Mode 2: Direct AI Scrape | HTML -> Markdown -> Send to LLM dengan target JSON schema / prompt | Must |
| F-06 | CLI Interface | Command line tool (`python -m src.cli` / `ai-scrape`) | Must |
| F-07 | REST API | FastAPI endpoints (`POST /api/scrape`, `POST /api/generate-config`) | Should |

## 6. Future (Post-MVP)
- Self-healing selector (otomatis panggil AI jika CSS selector lama gagal/broken).
- Support Playwright stealth plugin tingkat lanjut.

## 7. User Flows

### Flow 1: Direct AI Extract (CLI/API)
```
Input: URL + Prompt/Schema (e.g., "ambil judul dan harga produk")
  ├── Fetcher: Get HTML via curl_cffi (or Playwright fallback)
  ├── Cleaner: Clean HTML -> Markdown
  ├── LLM Call: Send Markdown + Prompt -> Return JSON
  └── Output: JSON Result
```

### Flow 2: Bulk Auto-Selector Scrape (Novel/Catalog)
```
Input: Sample URL + Data Target
  ├── Fetcher: Get HTML sample
  ├── LLM Call: Generate CSS Selector JSON config
  ├── Save Config: Simpan selector ke database/JSON
  └── Scraper Engine: Fetch N halaman berikutnya pakai CSS Selector tanpa panggil LLM lagi
```

## 8. Tech Stack
| Layer | Pilihan | Alasan |
|---|---|---|
| Core Language | Python 3.12 | Ekosistem scraping & AI paling kuat |
| Fetcher | `curl_cffi`, `playwright` | High-speed TLS impersonation + fallback browser |
| DOM Parsing & Cleaning | `beautifulsoup4`, `html2text`, `selectolax` | Parsing cepat & pemotongan token HTML |
| AI Integration | `openai` SDK | Standardized OpenAI-compatible API client |
| API Framework | `fastapi`, `uvicorn` | Lightweight & auto-generated OpenAPI docs |
| Data Schema | `pydantic` | Validasi & penentuan schema output |

## 9. Open Questions
1. Apakah `curl_cffi` selalu tersedia di environment Linux tanpa headless GUI? (Ya, pure C-bindings).
2. Bagaimana cara mengani rate limit dari OpenAI/9Router jika bulk extraction? (Handled via retry exponential backoff).

## 10. Success Metrics
- Reduksi token > 80% dibanding mengirim raw HTML.
- Kecepatan ekstraksi mode Auto-Selector < 500ms per halaman (setelah config terbentuk).

---

# Fitur Tree: AI-Powered Universal Web Scraper

```
                  [AI Web Scraper]
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
 [Fetcher & DOM]    [AI Engines]     [Interfaces]
  ├── curl_cffi      ├── Mode 1:        ├── CLI Tool
  ├── Playwright         Auto-Selector  └── FastAPI REST
  └── DOM Cleaner    └── Mode 2:                Endpoints
                         Direct Extract
```

---

# Task List: AI-Powered Universal Web Scraper

Total tasks: 9. Urutan eksekusi = urutan di list (dependency-ordered).

## Setup
- [ ] **TASK-01**: Init folder project `~/projek/coba/ai-scraper`, venv Python, file `.env.example`, `requirements.txt` (`curl_cffi`, `playwright`, `beautifulsoup4`, `html2text`, `openai`, `fastapi`, `uvicorn`, `pydantic`), dan `pyproject.toml` (15 min)
- [ ] **TASK-02**: Implementasi modul `src/fetcher.py` (curl_cffi dengan fallback ke Playwright) (20 min)

## Core Scraping & DOM Pipeline
- [ ] **TASK-03**: Implementasi modul `src/cleaner.py` (DOM reduction: remove noise tag -> convert to Markdown) (20 min)
- [ ] **TASK-04**: Implementasi modul `src/ai_client.py` (Client OpenAI-compatible dengan support custom `BASE_URL` & `API_KEY`) (15 min)

## AI Scraping Modes
- [ ] **TASK-05**: Implementasi `src/mode_direct.py` (Direct AI extraction dari Markdown -> Structured JSON) (25 min)
- [ ] **TASK-06**: Implementasi `src/mode_selector.py` (AI Selector Generator & CSS-based Scraper Engine) (25 min)

## Interfaces & Polish
- [ ] **TASK-07**: Buat CLI interface `src/cli.py` (Argparse/Click CLI untuk command line execution) (20 min)
- [ ] **TASK-08**: Buat REST API FastAPI `app/main.py` (`POST /api/extract`, `POST /api/generate-selector`) (20 min)
- [ ] **TASK-09**: Verification & smoke test `tests/smoke.py` (Smoke test untuk fetcher, cleaner, AI mode, dan API) (15 min)
