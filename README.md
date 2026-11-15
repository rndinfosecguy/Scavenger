# Scavenger - OSINT Bot - 3.0
![image](scavenger_logo.png)

Multi-source OSINT credential-leak crawler for paste sites. Seven scrapers and a web dashboard.

[bot in action](https://twitter.com/leak_scavenger)

> **FOR RESEARCH ONLY.** This tool is intended for researchers and defenders to detect exposed secrets on public paste sites before attackers exploit them. Do not host or distribute breach data.

---

## Scrapers

| Source | Method | Flag |
|--------|--------|------|
| Pastebin archive | polls `https://pastebin.com/archive` for new pastes | `-a` |
| Pastebin user track | follows users from `configs/users.txt` | `-t` |
| Pastes.io | random 8-char ID guesses against the JSON API | `-p` |
| GitHub Gists | polls `https://gist.github.com/discover` for new gists | `-g` |
| Dpaste.com | polls `https://dpaste.com/public/` | `-d` |
| Pastecode.io | polls `https://pastecode.io/archive` | `-c` |
| GitLab snippets | polls `https://gitlab.com/explore/snippets` | `-l` |

Additional: `-D` for the web dashboard, `-e`/`-u` to edit search terms/users.

## Setup

```console
./setup.sh
```

Or manually:

```console
pip install -r requirements.txt
```

Required: Python 3, `tmux`, `vi`, `openssl`. See `setup.sh` for details.

## Usage

Start scrapers via the control script:

```console
python3 scavenger.py -a -t
```

Each flag launches a scraper in a detached tmux session. You can combine multiple flags.

List sessions:
```console
tmux ls
```

Attach to a running scraper:

```console
tmux a -t s-pastebin-archive
```

Detach with `Ctrl+B d`.

Scripts can also be run directly:

```console
python3 scrapers/scraper_pastebin_archive.py
```

## Dashboard

```console
python3 scavenger.py -D
```

HTTPS at `https://127.0.0.1:8080`, auto-refreshes every 30s.

## Config

- `configs/searchterms.txt` — one substring per line. Email:password detection is always on.
- `configs/users.txt` — target usernames for pastebin user track, one per line.
- `configs/pastesio.json` — pastes.io API key (optional) and tier (`"free"` or `"pro"`).

## Files

| File | Purpose |
|------|---------|
| `scavenger.py` | Control script — launches modules via tmux |
| `classes/utility.py` | Shared helpers: detection, database, archive, scraper loop |
| `scraper_*.py` | One per source |
| `dashboard.py` | Web dashboard |
| `setup.sh` | Idempotent setup — creates dirs, installs deps |

## License

[MIT](LICENSE) © rndinfosecguy

## Disclaimer

This software is provided for educational and research purposes only. Users are solely responsible for compliance with applicable laws and terms of service of any data source. Do not use this tool to store or distribute stolen data.
