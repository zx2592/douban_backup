# Douban Backup

[![v1.5](https://img.shields.io/badge/version-1.5-blue.svg)](https://github.com/zx2592/douban_backup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

A personal data backup tool for Douban — One-click export of all your **movies, books, music, and games** records on Douban, including ratings, reviews, tags, and marking dates, output as beautifully formatted Excel and structured JSON.

---

## Feature Overview

### Data Collection

| Category | Status | Collected Fields |
|----------|--------|------------------|
| Movies | Want to Watch / Watching / Watched | Title, Rating, Review, Tags, Mark Date, Douban Link, Cover |
| Books | Want to Read / Reading / Read | Title, Rating, Review, Author/Publisher Info, Mark Date, Douban Link, Cover |
| Music | Want to Listen / Listening / Listened | Title, Rating, Review, Artist, Description, Douban Link, Cover |
| Games | Want to Play / Playing / Played | Title, Rating, Review, Description, Mark Date, Douban Link, Cover |

### Excel Export

- **Overview Page** — Summary table of item counts per category × status at a glance
- **Category Pages** — Separate sheets for Movies, Books, Music, and Games
- **Status Grouping** — Watched/Watching/Want to Watch separated by green/blue/orange header rows
- **Star Rating Display** — Numeric ratings automatically converted to ★★★★☆ for intuitive display
- **Clickable Links** — Douban entry links clickable for direct navigation
- **Zebra Striping** — Alternating row colors for easy reading
- **Frozen Headers** — Table headers remain visible during scrolling

### Authentication Methods

| Method | Description | Recommended Scenarios |
|--------|-------------|----------------------|
| Cookie Import | Copy and paste Cookie from browser | **Preferred**, secure and convenient, bypasses CAPTCHA |
| Account Password | Interactive input, password not echoed | Fallback when Cookie expires |
| Public Crawling | `crawl_public.py` to crawl public data | Crawling others' public profiles |

### Anti-Crawling Strategies

- 2-second smart request delay
- Automatic retry on failure (up to 3 times)
- 30-second request timeout protection
- Browser-level User-Agent spoofing

---

## Quick Start

### 1. Install Dependencies

Requires Python 3.8+

```bash
pip install -r requirements.txt
```

### 2. Import Cookie (Recommended)

Douban login has slider/CAPTCHA protection; it's recommended to authenticate via browser Cookie:

```bash
python import_cookies.py
```

Follow the prompts:

1. Log in to [douban.com](https://www.douban.com) in your browser (Chrome/Edge)
2. Press `F12` to open Developer Tools → `Network` tab
3. Refresh the page and click the first request (`www.douban.com`)
4. Copy the entire content after `Cookie:` in Request Headers
5. Paste into the terminal and press Enter

The tool will automatically verify Cookie validity and save it.

### 3. Start Backup

```bash
# Back up all categories (Movies + Books + Music + Games)
python main.py

# Back up only Movies
python main.py movies

# Back up only Books
python main.py books

# View historical backups
python main.py list
```

### 4. View Results

Backup files are saved in the `data/backup/` directory:

```
data/backup/
├── douban_backup_20260331_143000.xlsx   # Beautiful Excel report
└── douban_backup_20260331_143000.json   # Structured raw data
```

### 5. Crawl Public Data (No Login Required)

```bash
# Specify user ID via command-line argument
python crawl_public.py <UserID>

# Or run directly for interactive input
python crawl_public.py
```

---

## Project Structure

```
├── main.py              # Main program entry point, CLI command dispatch
├── auth.py              # Authentication module (Cookie / Account Password)
├── import_cookies.py    # Browser Cookie import tool
├── config.py            # Global configuration (timeout, delay, backup targets)
├── base.py              # Spider base class (request, retry, pagination)
├── movies.py            # Movie data scraping
├── books.py             # Book data scraping
├── music.py             # Music data scraping
├── games.py             # Game data scraping
├── crawl_public.py      # Public data scraping without login (standalone script)
├── storage.py           # Data storage (JSON + beautified Excel export)
├── requirements.txt     # Python dependencies
└── data/
    ├── cookies.json     # Login credentials (auto-generated, permission 600)
    ├── user_info.json   # User info cache
    └── backup/          # Export file output directory
```

---

## Changelog

### v1.5 — Security Hardening

- **Removed command-line password passing** — No longer supports passing account passwords via CLI arguments, preventing password leaks in shell history and process lists
- **Password input hidden** — Interactive password input now uses `getpass`, with no echo on input
- **Cookie file permission control** — Automatically sets `0o600` permission on `cookies.json` after writing, readable/writable only by owner
- **Standardized exception handling** — All bare `except:` replaced with `except Exception:` to avoid swallowing critical exceptions like `KeyboardInterrupt`
- **Fixed rating parsing** — Rating class extraction in Movies/Books changed from index access to safe iteration, eliminating out-of-bounds risk
- **Removed hardcoded user ID** — `crawl_public.py` now accepts user ID via command-line arguments or interactive input, no longer leaking target user identity

### v1.2 — Beautiful Excel Export

- Added overview sheet summarizing item counts across categories and statuses
- Separate sheets for each category with color-coded header rows grouped by status
- Star rating symbols display (★★★★☆)
- Clickable Douban links
- Alternating row colors, frozen headers, auto-adjusted column widths

### v1.0 — Initial Version

- Support backup of four categories: Movies, Books, Music, and Games
- Cookie import authentication
- JSON format export
- Automatic pagination crawling with retry mechanism

---

## Notes

- This tool is for personal data backup and learning purposes only; do not use for commercial purposes
- Control the running frequency reasonably to avoid putting pressure on Douban servers
- `cookies.json` contains login credentials; please keep it secure and do not upload to public repositories
