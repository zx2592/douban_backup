# Douban Backup

[![v1.81](https://img.shields.io/badge/version-1.81-blue.svg)](https://github.com/zx2592/douban_backup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

A personal data backup tool for Douban — export your **movies, books, music, games, and long reviews** in one command, including ratings, comments, tags, mark dates, and cover images, as a beautified Excel report, CSV, Markdown, and structured JSON.

> **v1.8** adds local cover downloads, long-review backup, CSV / Markdown export, and pip installation as a command-line tool.

[中文 README](README.md)

---

## Feature Overview

### What Gets Backed Up

| Category | Statuses | Fields |
|----------|----------|--------|
| Movies | Want to Watch / Watching / Watched | Title, Rating, Comment, Tags, Mark Date, Douban Link, Cover |
| Books | Want to Read / Reading / Read | Title, Rating, Comment, Author & Publisher, Mark Date, Douban Link, Cover |
| Music | Want to Listen / Listening / Listened | Title, Rating, Comment, Artist, Description, Douban Link, Cover |
| Games | Want to Play / Playing / Played | Title, Rating, Comment, Description, Mark Date, Douban Link, Cover |
| Long Reviews | Film / Book / Music / Game reviews | Title, Subject, Rating, Published At, Body, Douban Link |

Covers are recorded as URLs by default; `--download-covers` saves the images locally. Long reviews store an excerpt by default; `--full-reviews` fetches the complete text.

### Export Formats

| Format | Notes |
|--------|-------|
| JSON | Structured raw data and backup metadata — **always written** |
| Excel | Beautified report: overview sheet, per-category sheets, status groups, stars, clickable links (default) |
| CSV | One file per category, status as its own column and numeric ratings for analysis (`--format csv`) |
| Markdown | Readable document grouped by category and status, good for notes or version control (`--format md`) |

The Excel report contains an overview sheet (counts per category × status), one sheet per category, colored status group headers, star ratings (★★★★☆), clickable Douban links, zebra striping, and frozen headers.

### Core Capabilities

- **Incremental backup** — fetches only entries added or edited since the last backup; an unchanged collection costs a single request
- **Resumable checkpoints** — progress survives request failures and manual interruption, and is isolated per Douban account
- **Local covers** — download cover images so the backup no longer depends on Douban's image CDN
- **Response diagnostics** — distinguishes expired logins, rate limits, risk control, missing pages, and server errors
- **Pagination integrity** — never reports success or clears the checkpoint when the last page cannot be confirmed
- **Safe exports** — external text can't be executed as a formula in Excel or CSV; the cookie file is chmod'ed to `0600`

### Authentication

| Method | Notes | Use for |
|--------|-------|---------|
| Cookie import | Copy and paste the Cookie from your browser | Backing up your own data — **the only supported login method** |
| No login | Public-data mode | Backing up any user's public profile |

> Douban's login page is protected by a slider CAPTCHA, so automated account-password login is not possible; Cookie import is the only supported method. Just re-import when a Cookie expires.

---

## Quick Start

### 1. Install

Requires Python 3.8+. Either way works:

```bash
# Option 1: install as a command-line tool (recommended)
pip install .

# Then run it from any directory
douban-backup --help
douban-backup-public <UserID>
douban-import-cookies

# Option 2: run straight from the source tree
pip install -r requirements.txt
python main.py
```

Both are functionally identical; the commands map one to one:

| From source | Installed |
|-------------|-----------|
| `python main.py` | `douban-backup` |
| `python crawl_public.py` | `douban-backup-public` |
| `python import_cookies.py` | `douban-import-cookies` |

**Where data lives**: the project's `data/` when running from a source checkout; `~/.douban_backup` once pip-installed (writing into site-packages would be wiped on upgrade). Set `DOUBAN_BACKUP_HOME` to put it elsewhere.

> Examples below use `python main.py`. If you installed with pip, substitute `douban-backup` — the arguments are identical.

### 2. Import Your Cookie

```bash
python import_cookies.py
```

Follow the prompts:

1. Log in to [douban.com](https://www.douban.com) in your browser (Chrome/Edge)
2. Press `F12` to open Developer Tools → `Network` tab
3. Refresh the page and click the first request (`www.douban.com`)
4. Copy everything after `Cookie:` in the Request Headers
5. Paste it into the terminal and press Enter

The tool verifies the Cookie and saves it.

### 3. Run a Backup

```bash
# Back up everything (movies + books + music + games + long reviews)
python main.py

# Check the login state and that each category page is reachable
python main.py verify

# List previous backups
python main.py list
```

Back up a single category:

```bash
python main.py movies
python main.py books
python main.py music
python main.py games
python main.py reviews
```

Common combinations:

```bash
# Pick or exclude categories
python main.py --only movies,books
python main.py --skip music,games

# Incremental + every format + covers (recommended for routine backups)
python main.py --incremental --format all --download-covers

# Slow down to reduce rate-limit risk
python main.py --delay 5

# Export somewhere else
python main.py --output D:\douban-backup
```

### 4. Results

Written to `data/backup/` by default:

```
data/backup/
├── douban_backup_20260331_143000.json          # Structured data and metadata
├── douban_backup_20260331_143000.xlsx          # Beautified Excel report
├── douban_backup_20260331_143000.md            # Markdown document (--format md)
├── douban_backup_20260331_143000_movies.csv    # CSV, one per category (--format csv)
├── douban_backup_20260331_143000_reviews.csv
├── douban_movies_20260331_150000.xlsx          # Single-category backup
├── covers/                                      # Cover images (--download-covers)
│   ├── movies/1292052.jpg
│   └── books/1084336.jpg
├── backup_state_<account-digest>.json           # Checkpoint for unfinished work
└── backup_baseline_<account-digest>.json        # Incremental backup baseline
```

Every export is timestamped, so repeated backups never overwrite each other; all formats from one run share a single timestamp so they are easy to pair up.

The JSON uses a consistent top-level shape:

```json
{
  "metadata": {
    "app_version": "1.8",
    "backup_mode": "authenticated",
    "generated_at": "2026-08-06T20:00:00-07:00",
    "selected_categories": ["movies", "books"]
  },
  "data": {}
}
```

---

## Command-Line Reference

| Argument | Description |
|----------|-------------|
| `verify` | Check the login state and category page reachability |
| `list` | List existing backup files |
| `movies` / `books` / `music` / `games` / `reviews` | Back up a single category |
| `--only a,b` | Back up only these categories |
| `--skip a,b` | Skip these categories |
| `--incremental` | Fetch only entries added or edited since the last backup |
| `--format FORMATS` | `xlsx` (default), `csv`, `md`, or `all`; JSON is always written |
| `--download-covers` | Save cover images under `covers/` |
| `--full-reviews` | Fetch full review text (one extra request per review) |
| `--delay SECONDS` | Wait between requests (default 2s authenticated, 1s public) |
| `--output DIR` | Export directory, defaults to `data/backup` |
| `--no-resume` | Disable resumable checkpoints |
| `--public USER_ID` | Public-data mode for the given user's profile |

### Exit Codes

For use in scripts and scheduled jobs:

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Failure (expired Cookie, interrupted crawl, failed verification, …) |
| 2 | Invalid command-line arguments |

---

## Advanced Usage

### Incremental Backup

For large collections, re-crawling everything each time is slow and invites rate limiting. Incremental mode exploits the fact that Douban collection pages are ordered newest-marked-first: it walks from page one and stops as soon as it meets an entry that is already in the last backup and unchanged.

```bash
# First run: full backup, establishes the baseline
python main.py --incremental

# Every run after that: usually one or two requests
python main.py --incremental
```

The baseline lives in `backup_baseline_<account-digest>.json`, isolated per account. **Every backup that completes refreshes the baseline**, with or without `--incremental`, so you can switch between modes freely. Exports always contain the merged full dataset, not just the new entries.

Things worth knowing:

- **Edits are captured** — entries are compared by a fingerprint of title, rating, comment, mark date, and tags, not just by ID. Editing a rating or comment pushes the entry back to the top, and it is re-fetched and overwrites the old record
- **Deletions are not synced** — an entry you un-marked no longer appears on the page, but stays in the baseline. Run a full backup when you want deletions reflected
- **Interruptions don't poison the baseline** — it is left untouched when a backup doesn't finish, so the next run won't stop at the edge of partial data
- **Public mode is supported too** — with its checkpoint and baseline stored separately

### Cover Downloads

Storing only image URLs is not a complete backup — Douban's image CDN checks the Referer, and old URLs break once an entry is delisted or the site changes. `--download-covers` saves covers under `covers/<category>/` and records the relative path in the JSON:

```bash
python main.py --download-covers
```

- Already-downloaded files are skipped, so re-running after an interruption is incremental
- A single failure is counted, never raised — it must not take down data already crawled
- Only Douban's own image hosts are fetched; filenames use the entry ID or a URL digest, never the title

Covers come from the image CDN, which is more tolerant than the main site, so they default to a 0.5s interval instead of 2s.

### Long Reviews

Long reviews (film / book / music / game) are backed up by default. The list page carries only an excerpt; the full text requires opening each review page:

```bash
# Default: excerpt only, very cheap (review lists are usually a few pages)
python main.py

# Fetch full text — one extra request per review
python main.py --full-reviews

# Back up long reviews only
python main.py reviews
```

Long reviews get their own Excel sheet, and their body is rendered as its own block in Markdown.

### Public-Data Mode (No Login)

```bash
# Standalone script
python crawl_public.py <UserID>
python crawl_public.py <UserID> --incremental --format all

# Or run it bare for an interactive prompt
python crawl_public.py

# Through the unified entry point
python main.py --public <UserID>
python main.py --public <UserID> --only movies,books --output D:\douban-backup
```

Public mode shares its crawling logic with authenticated backup, so retries, response diagnostics, resumable checkpoints, incremental backup, cover downloads, and every export format all work.

Its checkpoint and baseline are stored separately from the authenticated ones — a public profile hides entries marked private, so the two datasets differ and a shared baseline would make incremental comparison draw the wrong conclusion.

### Reducing Rate-Limit Risk

Most to least effective:

1. **Use incremental backup** — `--incremental` cuts request volume by an order of magnitude; this is by far the biggest lever
2. **Slow down** — `--delay 5` lengthens the gap between requests
3. Automatic retries (up to 3), a 30-second timeout, and a browser-level User-Agent are built in

---

## Project Structure

```
├── main.py              # Main entry point, CLI dispatch
├── crawl_public.py      # Public-data backup entry point
├── import_cookies.py    # Browser Cookie import tool
├── auth.py              # Authentication (Cookie-based login)
├── config.py            # Global config (timeouts, delays, data dir, categories)
├── cli.py               # Exit-code translation and export-format parsing
├── base.py              # Crawler base class (requests, retries, pagination, incremental stop)
├── movies.py            # Movie crawling
├── books.py             # Book crawling
├── music.py             # Music crawling
├── games.py             # Game crawling
├── reviews.py           # Long-review crawling
├── comments.py          # "My comment" extraction (markup differs per category)
├── covers.py            # Local cover image downloads
├── storage.py           # Exports (JSON / beautified Excel / CSV / Markdown)
├── incremental.py       # Incremental fingerprinting and baseline store
├── backup_state.py      # Per-account resumable checkpoints
├── backup_metadata.py   # Version, mode, and timestamp metadata
├── diagnostics.py       # Login, rate-limit, and page-error diagnostics
├── excel_safety.py      # Spreadsheet formula-injection protection
├── file_security.py     # Cookie file permissions
├── pyproject.toml       # Packaging config and console scripts
├── requirements.txt     # Python dependencies
├── .github/workflows/   # CI: multi-version tests and packaging checks
├── tests/               # Offline parsing and workflow tests
└── data/
    ├── cookies.json     # Credentials (auto-generated, mode 600)
    ├── user_info.json   # Cached user info
    └── backup/          # Exports, covers, checkpoints, and baselines
```

---

## Changelog

### v1.81 — Music / Game Comment Backup Fix

**Fixed**

- **Music and game comments are no longer always empty** — Douban marks up the user's comment differently per category: movies use `<span class="comment">` and books use `<p class="comment">`, but music puts the comment in the last **unclassed** `<li>` of the entry's info list, and games put it in a trailing **unclassed** `<p>`. All four parsers only looked for `.comment`, so movies and books worked while music and games backed up every field except "my comment"
- **Game titles are no longer overwritten by the rating wording** — for entries whose rating is only given as `title="力荐"`, the rating conversion reused the `title` variable that held the entry title, so game names in the backup became "力荐 / 推荐 / 还行"

**Improved**

- **Comment extraction lives in one place** — new `comments.py`, shared by all four parsers: `.comment` first (so it still works if Douban adds the class to music and games), then a search through text-only `li` / `p` nodes that skips titles, descriptions, dates, ratings, and tags already parsed into other fields, so a date or description is never written as a comment. Entries without a comment stay empty

### v1.8 — Cover Downloads, Long Reviews, Multi-Format Export, and Packaging

**New**

- **Local cover downloads** — `--download-covers` stores covers under `covers/<category>/` so the backup no longer depends on Douban's image CDN. Existing files are skipped, making re-runs incremental; filenames use the entry ID or a URL digest (titles come from the page and may contain `..`, which would escape the target directory), and only Douban's own image hosts are fetched
- **Long-review backup** — new `reviews` category covering film, book, music, and game reviews. Entries are keyed by the review's own ID (one subject can have several reviews); excerpts by default, `--full-reviews` fetches the complete text
- **CSV and Markdown export** — `--format xlsx,csv,md` or `--format all`. CSV writes one file per category with status as its own column and numeric ratings, using a BOM so Excel on Windows renders Chinese correctly; Markdown groups by category and status
- **Incremental backup** — `--incremental` fetches only entries added or edited since the last backup. Comparison uses a fingerprint of title, rating, comment, date, and tags rather than the entry ID, so edited entries are re-fetched and overwrite the old record. Exports remain the merged full dataset
- **pip-installable** — added `pyproject.toml` providing the `douban-backup`, `douban-backup-public`, and `douban-import-cookies` commands

**Improved**

- **Public mode folded into the shared crawling stack** — `crawl_public.py` used to carry its own crawling, pagination, parsing, and export logic, duplicating the main path; a single Douban layout change meant editing both. It now reuses the same code (691 lines down to 203) and gains retries, response diagnostics, resumable checkpoints, incremental backup, and the beautified Excel export
- **Data directory when installed** — writing into site-packages gets wiped on upgrade and is sometimes read-only, so an installed copy uses `~/.douban_backup`; a source checkout keeps using the project's `data/`, and `DOUBAN_BACKUP_HOME` overrides both
- **Non-zero exit code on failure** — an expired Cookie, an interrupted crawl, or a failed verification all used to exit 0, so scripts could not tell success from failure. The convention is now 0 success, 1 failure, 2 invalid arguments; bad arguments no longer raise a traceback
- **Continuous integration** — GitHub Actions runs the tests and static checks on Python 3.8/3.10/3.12 and verifies that the distribution and console scripts work
- **Added LICENSE** — the README had carried an MIT badge with no license file
- **Dropped the unused pandas dependency** — the heaviest of the four requirements, never imported anywhere

**Fixed**

- **Removed the defunct account-password login** — Douban's login page is protected by a slider CAPTCHA, so the old form-based login could no longer succeed and only misled users into trying a dead end when a Cookie expired. Cookie import is now the sole method, and a missing or corrupt Cookie file produces a clear message instead of an exception
- **Single-category backups no longer overwrite history** — `python main.py movies` previously wrote a fixed `movies.xlsx`, overwriting the previous run; it is now timestamped like full backups
- **One timestamp per backup run** — export formats no longer read the clock separately, so their filenames can't disagree across a second boundary
- **Music ratings no longer dropped** — only the first entry of the class list was checked, so markup where the rating class is not first lost the rating entirely
- **Game ratings no longer written as Chinese text** — some entries expose the rating only as `title="力荐"`, which was stored verbatim: Chinese in the JSON, and silently dropped from Excel because it isn't a number. It is now converted to 5/4/3/2/1

### v1.53 — Configurable Request Delay

- **Reduced rate-limit risk** — authenticated and public backups accept `--delay SECONDS`; defaults are 2 seconds and 1 second respectively

### v1.52 — Reliability & CLI Enhancements

- **Resumable backup** — progress is preserved on request failures, pagination errors, or manual interruption; state is isolated per account and written atomically
- **Pagination completeness protection** — no longer reports false success or clears the checkpoint when the last page cannot be confirmed
- **Response diagnostics** — clearly distinguishes login expiry, access restrictions, risk control, missing pages, and server errors
- **Backup metadata** — JSON and Excel record app version, backup mode, account, generation time, and selected categories
- **Hardened export** — prevents external text from being interpreted as formulas in Excel, and tightens Cookie file permissions
- **CLI improvements** — per-category shortcuts plus `verify`, `--only`, `--skip`, `--output`, and `--no-resume`
- **Test coverage** — page structures, checkpoint isolation, atomic writes, error retries, and pagination anomalies

### v1.51 — Public Data Short Review Fix

- **Fixed short review export** — public and authenticated modes now read movie, book, music, and game short reviews precisely, no longer skipping a music review that shares a node with the date, nor mistaking a game description for a review

### v1.5 — Security Hardening

- **Removed command-line password passing** — no more passwords in shell history or process lists
- **Hidden password input** — interactive input uses `getpass`
- **Cookie file permissions** — `cookies.json` is chmod'ed to `0o600` after writing
- **Normalized exception handling** — bare `except:` replaced with `except Exception:`, no longer swallowing `KeyboardInterrupt`
- **Fixed rating parsing** — movie/book rating class extraction iterates safely instead of indexing
- **Removed hardcoded user ID** — `crawl_public.py` takes it from the command line or a prompt

### v1.2 — Beautified Excel Export

- Overview sheet summarizing counts per category and status
- Separate sheet per category with colored status group headers
- Star rating symbols (★★★★☆)
- Clickable Douban links
- Zebra striping, frozen headers, auto column widths

### v1.0 — Initial Release

- Backup for movies, books, music, and games
- Cookie import authentication
- JSON export
- Automatic pagination and retries

---

## Notes

- This tool is for personal data backup and learning only; please don't use it commercially
- Keep the request rate reasonable; `--incremental` is recommended for routine backups
- `cookies.json` holds your login credentials — keep it safe and never commit it to a public repository
- Incremental backup does not sync collections you deleted on Douban; run a full backup when you want those cleared
