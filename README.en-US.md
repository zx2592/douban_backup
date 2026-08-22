# Douban Backup

[![v1.54](https://img.shields.io/badge/version-1.54-blue.svg)](https://github.com/zx2592/douban_backup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

A personal data backup tool for Douban — One-click export of all your **movies, books, music, and games** records on Douban, including ratings, reviews, tags, and marking dates, output as beautifully formatted Excel and structured JSON.

> v1.54 removes the defunct account-password login, making Cookie import the only authentication method, and gives single-category backups timestamped filenames so they no longer overwrite earlier backups.

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
| Cookie Import | Copy and paste Cookie from browser | Backing up your own data — **the only supported login method** |
| Public Crawling | `crawl_public.py` to crawl public data | Crawling others' public profiles |

> Douban's login page is protected by a slider CAPTCHA, so automated account-password login is not possible; Cookie import is the only supported method. When a Cookie expires, just run `python import_cookies.py` again.

### Anti-Crawling Strategies

- **Configurable request delay** — use `--delay SECONDS` to adjust the wait between requests and reduce rate-limit risk (default: 2 seconds for authenticated backups, 1 second for public backups)
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

# Adjust the delay between requests (in seconds) to reduce rate-limit risk
python main.py --delay 5

# View historical backups
python main.py list
```

### 4. View Results

Backup files are saved in the `data/backup/` directory:

```
data/backup/
├── douban_backup_20260331_143000.xlsx   # Beautiful Excel report (full backup)
├── douban_backup_20260331_143000.json   # Structured raw data (full backup)
├── douban_movies_20260331_150000.xlsx   # Single-category backup (python main.py movies)
└── douban_movies_20260331_150000.json
```

Every export is timestamped, so repeated backups never overwrite each other; the JSON and Excel from one run share a single timestamp so they are easy to pair up.

### 5. Crawl Public Data (No Login Required)

```bash
# Specify user ID via command-line argument
python crawl_public.py <UserID>

# Public backups support the same delay option
python crawl_public.py <UserID> --delay 5

# Or run directly for interactive input
python crawl_public.py
```

---

## Project Structure

```
├── main.py              # Main program entry point, CLI command dispatch
├── auth.py              # Authentication module (Cookie-based login)
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

### v1.54 — Focused Authentication & Backup File Protection

- **Removed the defunct account-password login** — Douban's login page is protected by a slider CAPTCHA, so the old form-based account-password login could no longer succeed and only misled users; that path is now deleted, Cookie import is the sole authentication method, and a failed login prints clear import instructions
- **Resilient Cookie loading** — A missing, corrupt, or empty Cookie file now produces a clear message instead of raising an exception and aborting the program
- **Single-category backups no longer overwrite history** — Commands like `python main.py movies` previously wrote to a fixed `movies.json`/`movies.xlsx`, overwriting the previous run; they now use `douban_movies_<timestamp>` naming, consistent with full backups
- **One timestamp per backup run** — JSON and Excel no longer read the clock separately, so their filenames can't disagree across a second boundary

### v1.53 — Configurable Request Delay

- **Reduced rate-limit risk** — Authenticated and public backups now accept `--delay SECONDS` to control the wait between requests; their defaults remain 2 seconds and 1 second respectively

### v1.52 — Reliability & CLI Enhancements

- **Resumable backup** — Progress is preserved on request failures, pagination errors, or manual interruption; state is isolated per Douban account and written atomically
- **Pagination completeness protection** — No longer reports false success or clears the checkpoint when the last page cannot be confirmed
- **Response diagnostics** — Clearly distinguishes login expiry, access restrictions, risk control, missing pages, and server errors
- **Backup metadata** — JSON and Excel record app version, backup mode, account, generation time, and selected categories
- **Hardened export** — Prevents external text from being interpreted as formulas in Excel, and tightens Cookie file permissions
- **Richer CLI** — Adds dedicated commands for movies, books, music, and games, plus `verify`, `--only`, `--skip`, `--output`, and `--no-resume`
- **Test coverage** — Adds tests for the four page structures, checkpoint isolation, atomic writes, error retries, and pagination anomalies

### v1.51 — Public Data Short Review Fix

- **Fixed book, music, and game short review export** — `crawl_public.py` now uniformly reads the short review elements from the page, avoiding music short reviews being ignored when sharing an item with the date, and no longer mistaking game descriptions for short reviews.

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
