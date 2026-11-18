# Changelog

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