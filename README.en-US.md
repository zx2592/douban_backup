# Douban Backup

[![v1.8](https://img.shields.io/badge/version-1.8-blue.svg)](https://github.com/zx2592/douban_backup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

A personal data backup tool for Douban — One-click export of all your **movies, books, music, and games** records on Douban, including ratings, reviews, tags, and marking dates, output as beautifully formatted Excel and structured JSON.

> v1.8 adds local cover downloads, long-review backup, CSV / Markdown export, and pip installation as a command-line tool.

---

## Feature Overview

### Data Collection

| Category | Status | Collected Fields |
|----------|--------|------------------|
| Movies | Want to Watch / Watching / Watched | Title, Rating, Review, Tags, Mark Date, Douban Link, Cover |
| Books | Want to Read / Reading / Read | Title, Rating, Review, Author/Publisher Info, Mark Date, Douban Link, Cover |
| Music | Want to Listen / Listening / Listened | Title, Rating, Review, Artist, Description, Douban Link, Cover |
| Games | Want to Play / Playing / Played | Title, Rating, Review, Description, Mark Date, Douban Link, Cover |
| Long Reviews | Film / Book / Music / Game reviews | Title, Subject, Rating, Published At, Body (excerpt or full text), Douban Link |

### Export Formats

| Format | Notes |
|--------|-------|
| JSON | Structured raw data and backup metadata — **always written** |
| Excel | Beautified report: overview sheet, per-category sheets, status groups, stars, clickable links (default) |
| CSV | One file per category, status as its own column and numeric ratings for analysis (`--format csv`) |
| Markdown | Readable document grouped by category and status, good for notes or version control (`--format md`) |

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

- **Incremental backup** — `--incremental` fetches only new and edited entries, cutting request volume dramatically; the single most effective way to avoid rate limits
- **Configurable request delay** — use `--delay SECONDS` to adjust the wait between requests and reduce rate-limit risk (default: 2 seconds for authenticated backups, 1 second for public backups)
- Automatic retry on failure (up to 3 times)
- 30-second request timeout protection
- Browser-level User-Agent spoofing

---

## Quick Start

### 1. Install

Requires Python 3.8+. Either way works:

```bash
# Option 1: install as a command-line tool
pip install .

# Then run it from any directory
douban-backup --help
douban-backup-public <UserID>
douban-import-cookies

# Option 2: run straight from the source tree
pip install -r requirements.txt
python main.py
```

Once installed, cookies and backups live in `~/.douban_backup`; running from a source checkout keeps them in the project's `data/`. Set `DOUBAN_BACKUP_HOME` to put them somewhere else.

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

# Incremental backup: fetch only entries added or edited since the last backup
python main.py --incremental

# Export Excel, CSV and Markdown together
python main.py --format all

# Download covers locally so the backup does not depend on Douban's image CDN
python main.py --download-covers

# Fetch the full text of long reviews (excerpts only by default)
python main.py --full-reviews

# View historical backups
python main.py list
```

### 4. Exit Codes

For use in scripts and scheduled jobs:

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Failure (expired Cookie, interrupted crawl, failed verification, …) |
| 2 | Invalid command-line arguments |

### 5. View Results

Backup files are saved in the `data/backup/` directory:

```
data/backup/
├── douban_backup_20260331_143000.xlsx   # Beautiful Excel report (full backup)
├── douban_backup_20260331_143000.json   # Structured raw data (full backup)
├── douban_movies_20260331_150000.xlsx   # Single-category backup (python main.py movies)
└── douban_movies_20260331_150000.json
```

Every export is timestamped, so repeated backups never overwrite each other; the JSON and Excel from one run share a single timestamp so they are easy to pair up.

### 6. Crawl Public Data (No Login Required)

```bash
# Specify user ID via command-line argument
python crawl_public.py <UserID>

# Public backups support the same delay option
python crawl_public.py <UserID> --delay 5

# Or run directly for interactive input
python crawl_public.py

# Public mode supports incremental backup and checkpoints too
python crawl_public.py <UserID> --incremental
python main.py --public <UserID> --incremental
```

Public mode shares its crawling logic with authenticated backup, so retries, response diagnostics, resumable checkpoints, incremental backup, and the beautified Excel export are all available. Its checkpoint and baseline are stored separately from the authenticated ones — a public profile hides entries marked private, so the two datasets differ and a shared baseline would make incremental comparison draw the wrong conclusion.

### 7. Incremental Backup

For large collections, re-crawling everything each time is slow and invites rate limiting. Incremental mode exploits the fact that Douban collection pages are ordered newest-marked-first: it walks from page one and stops as soon as it meets an entry that is already in the last backup and unchanged.

```bash
# First run: full backup, establishes the baseline
python main.py --incremental

# Every run after that: usually one or two requests
python main.py --incremental
```

The baseline lives in `data/backup/backup_baseline_<account-digest>.json`, isolated per Douban account. **Every backup that completes refreshes the baseline**, with or without `--incremental`, so you can switch between the two modes freely. The exported Excel and JSON always contain the merged full dataset, not just the new entries.

Things worth knowing:

- **Edits are captured** — Entries are compared by a fingerprint of title, rating, review, mark date, and tags, not just by ID. Editing a rating or review pushes the entry back to the top, and the tool re-fetches it and overwrites the old record
- **Deletions are not synced** — An entry you un-marked on Douban no longer appears on the page, but it stays in the baseline. Run a full backup (without `--incremental`) when you want deletions reflected
- **Interruptions don't poison the baseline** — The baseline is left untouched when a backup doesn't finish, so the next incremental run won't stop at the edge of partial data
- **Public mode is supported too** — `--public` now runs on the shared crawling stack, so incremental, checkpoints, and retries all work; its checkpoint and baseline are stored separately from the authenticated ones

### 8. Cover Downloads

Storing only image URLs is not a complete backup — Douban's image CDN checks the Referer, and old URLs break once an entry is delisted or the site changes. `--download-covers` saves covers under `covers/<category>/` in the export directory and records the relative path in the JSON:

```bash
python main.py --download-covers
```

- Already-downloaded files are skipped, so re-running after an interruption is incremental
- A single failure is counted, never raised — it must not take down data already crawled
- Only Douban's own image hosts are fetched, and filenames use the entry ID or a URL digest, never the title

### 9. Long Reviews

Long reviews (film / book / music / game) are backed up by default. The list page carries only an excerpt; the full text requires opening each review page:

```bash
# Default: excerpt only, very cheap
python main.py

# Fetch full text — one extra request per review
python main.py --full-reviews

# Back up long reviews only
python main.py reviews
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
├── cli.py               # Command-line exit codes and export formats
├── covers.py            # Local cover image downloads
├── reviews.py           # Long-review crawling
├── incremental.py       # Incremental backup fingerprinting and baseline store
├── backup_state.py      # Per-account resumable checkpoints
├── pyproject.toml       # Packaging config and console scripts
├── requirements.txt     # Python dependencies
├── .github/workflows/   # CI: multi-version tests and packaging checks
└── data/
    ├── cookies.json     # Login credentials (auto-generated, permission 600)
    ├── user_info.json   # User info cache
    └── backup/          # Export file output directory
```

---

## Changelog

### v1.8 — Cover Downloads, Long Reviews, Multi-Format Export, and Packaging

- **Local cover downloads** — `--download-covers` stores covers under `covers/<category>/` so the backup no longer depends on Douban's image CDN. Existing files are skipped, making re-runs incremental; filenames use the entry ID or a URL digest (titles come from the page and may contain `..`, which would escape the target directory), and only Douban's own image hosts are fetched
- **Long-review backup** — New `reviews` category covering film, book, music, and game reviews. Entries are keyed by the review's own ID (one subject can have several reviews), and the body is stored in `comment` so incremental fingerprinting and export logic apply unchanged. Excerpts by default; `--full-reviews` fetches the complete text
- **CSV and Markdown export** — `--format xlsx,csv,md` or `--format all`. CSV writes one file per category with status as its own column and numeric ratings, using a BOM so Excel on Windows renders Chinese correctly; Markdown groups by category and status and escapes formatting characters in titles
- **pip-installable** — Added `pyproject.toml` providing the `douban-backup`, `douban-backup-public`, and `douban-import-cookies` commands
- **Data directory when installed** — Writing into site-packages gets wiped on upgrade and is sometimes read-only, so an installed copy uses `~/.douban_backup`; a source checkout keeps using the project's `data/`, and `DOUBAN_BACKUP_HOME` overrides both
- **Continuous integration** — GitHub Actions runs the tests and static checks on Python 3.8/3.10/3.12 and verifies that the distribution and console scripts work
- **Added LICENSE** — The README had carried an MIT badge with no license file
- **Dropped the unused pandas dependency** — The heaviest of the four requirements, never imported anywhere

### v1.57 — Rating Parsing and Exit Code Fixes

- **Music ratings no longer dropped** — Only the first entry of the class list was checked, so markup like `class="rating-star rating5-t"`, where the rating class is not first, lost the rating entirely; all classes are now scanned
- **Game ratings no longer written as Chinese text** — Some game entries expose the rating only as `title="力荐"`, which was stored verbatim: Chinese in the JSON, and silently dropped from the Excel export because it isn't a number. It is now converted to 5/4/3/2/1; an unrecognized title yields an empty rating instead of polluting the column
- **CLI returns a non-zero exit code on failure** — Both entry points discarded their return value, so an expired Cookie, an interrupted crawl, or a failed verification all exited 0 and scripts could not tell success from failure. The convention is now: 0 success, 1 failure, 2 invalid arguments
- **Bad arguments no longer raise a traceback** — A misspelled category prints a plain message and exits with code 2
- **Public backup reports success** — `run_public_backup()` now returns `{"ok": ..., "data": ...}`, with `ok` false when the crawl was interrupted or failed

### v1.56 — Public Mode Folded Into the Shared Crawling Stack

- **Two parallel implementations eliminated** — `crawl_public.py` used to carry its own crawling, pagination, parsing, and export logic, duplicating `base.py` plus the four category crawlers; a single Douban layout change meant editing both. It now reuses the same code and shrank from 691 lines to 203
- **Public mode gained the full feature set** — Retries, response diagnostics, resumable checkpoints, and incremental backup all come for free. Previously a failed request abandoned the entire collection, and pagination relied on a "fewer than one page means done" heuristic that truncates early for users browsing with 30-per-page list view
- **Public exports upgraded** — From a single flat sheet to the same beautified report as authenticated backups (metadata sheet, overview sheet, per-category sheets, star ratings, clickable links)
- **State isolation** — Public checkpoints and baselines are stored under a `public:` prefix; a public profile hides entries marked private, so sharing a baseline with authenticated data would make incremental draw the wrong conclusion
- **Behavior change** — Public mode no longer writes a separate JSON file per category; the combined `douban_backup_<timestamp>.json` already holds everything

### v1.55 — Incremental Backup

- **Fetch only what changed** — New `--incremental` flag exploits the newest-first ordering of collection pages and stops paging as soon as it meets an unchanged entry from the last backup; an unchanged collection costs a single request, making this the most effective way to reduce rate-limit risk
- **Edits are detected** — Comparison uses a fingerprint of title, rating, review, date, and tags rather than the entry ID, so an edited rating or review is re-fetched and overwrites the old record instead of being skipped as "already seen"
- **Exports stay complete** — Newly fetched entries are merged with the baseline before export, so Excel and JSON always hold the full dataset
- **Baseline is separate from the checkpoint** — Isolated per account, written atomically, and refreshed only after a backup completes; an interrupted run never poisons it, and an app version bump does not invalidate it
- **Known limitations** — Incremental mode cannot detect deleted collection entries (run a full backup to reflect deletions), and public-data mode does not support it yet

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
