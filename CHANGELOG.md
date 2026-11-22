# Changelog

## 3.3.0 — 2026-11-22

### Added
- **Mobile-responsive dashboard** — the dashboard now adapts to small screens (≤480px). Source table scrolls horizontally with proportionally scaled columns. Stat cards switch to 2-column layout. Top-detected bars use fixed widths for consistent alignment. Logo, padding, and font sizes scale down. No layout changes on desktop.

## 3.2.0 — 2026-11-20

### Added
- **Recent detections feed on the dashboard** — shows the last 10 detected pastes with timestamp, source, and detection type. Updates live via the `/api/stats` endpoint without page refresh. Includes `collect_recent()` and corresponding CSS/JS.

## 3.1.3 — 2026-11-19

### Fixed
- **Dashboard page truncated in browser** — `Content-Length` was calculated using character count instead of byte count. Multi-byte Unicode characters (box-drawing, emoji) caused the reported length to be shorter than the actual page, making browsers stop reading before the closing HTML tags and JavaScript. The page now reports correct byte-length headers.

## 3.1.2 — 2026-11-19

### Fixed
- **Status column alignment** — status dots now align vertically across all source rows. Time text (`3m ago`, `1h 15m ago`) is right-aligned with a fixed minimum width so the dots don't shift when time strings differ in length.

## 3.1.1 — 2026-11-19

### Fixed
- **Label cleanup in standalone scrapers** — `scraper_github.py`, `scraper_pastebin_track.py`, and `scraper_pastesio.py` still used the old value-based label (`sanitize_filename(sensitive[0][1])`) instead of the category name. This caused filenames like `before_content_{id}` instead of `secret_assignment_{id}`. Now all 9 scrapers consistently use the detection category name as the filename prefix.

## 3.1.0 — 2026-11-18

### Search terms
- **Auto-reload** — scrapers now detect changes to `configs/searchterms.txt` on each pass and reload automatically. No more restart needed after editing. (`-e` shows "will be picked up automatically on the next pass".)
- **Validation** — editing via `-e` now warns if a term is too short (≤3 chars) or overlaps with a built-in precise pattern.

### Dashboard
- **Last-crawled timestamps** — each source row shows when it last completed a pass (`· 3m`, `· 1h 15m`, `· never`)
- **Online/offline by timestamp** — a source is considered offline if no crawl happened in the last hour, regardless of tmux sessions. The old tmux-based check (which could show orphaned sessions as "online") is replaced entirely.
- **Graceful shutdown** — `Ctrl+C` now exits cleanly with a shutdown message.
- **Fixed SSL handshake hang** — replaced `serve_forever()` with an interruptible `handle_request()` loop. Stuck TLS connections no longer block the server.

### Other
- **Semantic versioning** — added `VERSION` file and `CHANGELOG.md`.
- **Version badge in README** with link to changelog.

## 3.0.0 — 2026-11-18

### Major changes
- **Complete rework of the control script** — switched from cryptic numbered flags (`-0`..`-9`) to mnemonic letter flags (`-a`, `-t`, `-g`, etc.). The help panel is now auto-generated from a data-driven module registry.
- **Data-driven module system** — adding a new scraper is a single line in the `SCRAPERS` list. Argument parsing, panel display, and tmux dispatch are all generated automatically.
- **`os.system()` replaced with `subprocess.run()`** throughout the control script.
- **Shared scraper loop** — 6 of 9 scrapers now use the new `run_scraper()` helper from `classes/utility.py`, centralizing the common infinite-loop pattern (archive, fetch listing, parse links, analyze, save, sleep).
- **Consistent naming** — scraper files renamed to `scraper_<source>.py` and moved to a `scrapers/` subdirectory. tmux sessions renamed to `s-<source>`.
- **Web dashboard overhaul** — new dark hacker aesthetic with JetBrains Mono font, CRT scan-line overlay, terminal-style source table with scraper status column, archive count estimates, and top-detected-types section.
- **Search term auto-reload** — scrapers now detect file changes to `configs/searchterms.txt` on each pass and reload automatically. No more restart required after editing search terms.
- **Search term validation** — editing via `-e` now warns about terms that are too short or overlap with built-in precise patterns.
- **Graceful shutdown** — all scrapers respond instantly to `Ctrl+C`/`SIGTERM` via `KeyboardInterrupt` in signal handlers.
- **paste.gg scraper** added (`-s`/`--pastegg`).
- **Ideone.com scraper** added (`-i`/`--ideone`).
- **Dashboard fixes** — fixed path traversal vulnerability, added socket timeout for stuck TLS handshakes, replaced `serve_forever()` with interruptible `handle_request()` loop.
- **False positive reduction** — password/API key/secret assignment minimum length raised from 6 to 12 characters. Added precise regex patterns for Google API keys and SQL inserts targeting sensitive tables.
- **Label cleanup** — sensitive file labels now use detection category names instead of raw matched values.
- **Tweetbot fixes** — dpaste 9-char ID truncation fixed. GitLab regex anchor fixed. GitHub moved to lowest priority in the source tuple.
- **Logo integration** — `scavenger_logo.png` with transparent background. Dashboard header shows the logo.

### File structure changes
- `scavenger.py` — rewritten (data-driven registry, mnemonic flags, subprocess)
- `classes/utility.py` — added `run_scraper()`, `save_paste()`, `setup_signals()`
- `scrapers/` — new directory containing all 9 scraper files
- `scrapers/scraper_ideone.py` — new (ideone.com)
- `scrapers/scraper_pastegg.py` — new (paste.gg)
- `dashboard.py` — overhauled UI, fixed security issues
- `AGENTS.md` — rewritten
- `README.md` — rewritten
- Deleted: `pbincomArchiveScrape.py`, `pbincomTrackUser.py`, `pbincomIOscrape.py`, `gbingistscrape.py`, `dpastesiteScrape.py`, `pastecodeScrape.py`, `gitlabsnippetScrape.py`