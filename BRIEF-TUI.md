# PRD: AI Web Scraper TUI (Textual Terminal User Interface)

**Versi:** 0.2 (TUI Extension)  
**Tanggal:** 13 Agustus 2026  
**Type:** tui-app  

---

## 1. Overview
Penambahan antarmuka Terminal User Interface (TUI) interaktif untuk `ai-scraper` berbasis framework **Textual** (Python). TUI ini memungkinkan user memasukkan URL, memilih mode scraping (Direct AI vs Auto-Selector), mengatur prompt/schema, melihat live log fetching & reduction ratio, serta mereview hasil ekstraksi data JSON dalam bentuk tabel/tree interaktif langsung dari terminal tanpa harus mengetik command CLI panjang.

## 2. Goals
- Menyediakan TUI dashboard modern berbasis Textual yang responsif di terminal.
- Memfasilitasi interaksi 2 mode: Direct Extraction & Auto-Selector Generator.
- Menampilkan live status fetching (curl_cffi vs Playwright fallback), token reduction %, dan spinner saat AI memproses.
- Fitur ekspor/save hasil JSON ke file lokal dari TUI.
- Mempertahankan backward compatibility terhadap CLI (`src/cli.py`) dan API (`app/main.py`).

## 3. Non-Goals (Out of Scope v1 TUI)
- Custom WebGL/Canvas rendering di terminal.
- Multi-window desktop GUI (Tkinter/PyQt).

## 4. User Persona
**User Utama:** Developer / Sysadmin / User Terminal yang ingin scrape data interaktif tanpa membuka browser atau mengetik argumen CLI panjang.

## 5. MVP Features (TUI)
| # | Fitur | Description | Priority |
|---|---|---|---|
| F-01 | Main Layout Tabs | Split/Tab view: Scraper Runner, Live Logs, JSON Result Viewer, History/Config | Must |
| F-02 | Form Input Panel | Input field: URL, Prompt/Schema text, Select Mode (Direct / Selector) | Must |
| F-03 | Live Log & Status Bar | Logger real-time saat fetcher bekerja + info engine yang dipakai & compression ratio | Must |
| F-04 | JSON Tree / Rich Table | Viewer data hasil ekstraksi JSON dengan collapsible tree & syntax highlighting | Must |
| F-05 | Export / Save Button | Keybinding / Tombol (`Ctrl+S` / `Save`) untuk simpan hasil ke file JSON | Should |

## 6. Tech Stack (TUI Addition)
| Layer | Pilihan | Alasan |
|---|---|---|
| TUI Framework | `textual` (Python) | Framework TUI paling modern, reactive, widget-based, support mouse & keyboard |
| Formatting & Trees | `rich` | Render JSON, markdown, table, dan syntax highlight di terminal |

---

# Fitur Tree: AI Web Scraper TUI

```
                     [AI Scraper TUI]
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
[Runner Screen]      [Viewer Screen]      [Config & Logs]
 ├── URL Input        ├── JSON Tree        ├── Log Console
 ├── Mode Selector    ├── Raw Text         └── Engine Status Bar
 └── Run Button       └── Export Options
```

---

# Task List: AI Web Scraper TUI

Total tasks: 6. Urutan eksekusi = urutan di list (dependency-ordered).

## Setup
- [ ] **TASK-01**: Tambahkan dependensi `textual` dan `rich` ke `requirements.txt` & `pyproject.toml` (5 min)

## Core TUI App
- [ ] **TASK-02**: Buat modul `src/tui/app.py` (Textual App dasar dengan Header, Footer, & Tabbed Content) (20 min)
- [ ] **TASK-03**: Buat widget form `src/tui/widgets/form.py` (URL Input, Prompt Input, Mode Dropdown, Run Button) (20 min)
- [ ] **TASK-04**: Buat widget viewer `src/tui/widgets/viewer.py` (JSON Tree view + Rich syntax highlight & Save to file) (20 min)
- [ ] **TASK-05**: Integrasikan backend scraper (`fetcher`, `cleaner`, `mode_direct`, `mode_selector`) dengan async worker Textual di `src/tui/app.py` (25 min)

## Entry Point & Verification
- [ ] **TASK-06**: Tambahkan command `tui` pada `src/cli.py` (menjalankan TUI via `python -m src.cli tui` / `ai-scrape tui`) dan tes kelayakan TUI (15 min)
