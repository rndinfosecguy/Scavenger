#!/usr/bin/python

import datetime
import os
import random
import re
import shutil
import signal
import sqlite3
import time
import zipfile

try:
    from colorama import Fore, Style
except ImportError:
    class _Fore:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
        LIGHTBLACK_EX = LIGHTRED_EX = LIGHTGREEN_EX = LIGHTYELLOW_EX = ""
        LIGHTBLUE_EX = LIGHTMAGENTA_EX = LIGHTCYAN_EX = LIGHTWHITE_EX = ""

    class _Style:
        RESET_ALL = BRIGHT = DIM = NORMAL = ""

    Fore = _Fore()
    Style = _Style()


LOG_LEVELS = {
    "INFO": (Fore.CYAN, "ℹ"),
    "OK": (Fore.GREEN, "✓"),
    "WARN": (Fore.YELLOW, "⚠"),
    "ERROR": (Fore.RED, "✗"),
}


def log(level, message):
    """Print a single colorized, icon-tagged log line."""
    color, icon = LOG_LEVELS[level]
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(Style.DIM + timestamp + Style.RESET_ALL + " " + color + icon + Style.RESET_ALL + " " + message)


def divider(title=""):
    """Print a full-width thin horizontal rule with an optional bright title."""
    width = shutil.get_terminal_size().columns
    if title:
        wrapped = " " + title + " "
        pad = max(0, width - len(wrapped))
        half = pad // 2
        left = Style.DIM + "─" * half + Style.RESET_ALL
        right = Style.DIM + "─" * (pad - half) + Style.RESET_ALL
        print(left + Style.BRIGHT + wrapped + Style.RESET_ALL + right)
    else:
        print(Style.DIM + "─" * width + Style.RESET_ALL)


def banner(lines, width=None):
    """Print a rounded-corner box with centered text lines. Defaults to terminal width."""
    cols = width or shutil.get_terminal_size().columns
    inner = cols - 4
    print(Style.DIM + "╭" + "─" * (cols - 2) + "╮" + Style.RESET_ALL)
    for line in lines:
        clipped = line[:inner]
        left = (inner - len(clipped)) // 2
        right = inner - len(clipped) - left
        print(Style.DIM + "│ " + Style.RESET_ALL + " " * left + Style.BRIGHT + clipped + Style.RESET_ALL + " " * right + Style.DIM + " │" + Style.RESET_ALL)
    print(Style.DIM + "╰" + "─" * (cols - 2) + "╯" + Style.RESET_ALL)


def panel(title, *lines, width=None):
    """Print a rounded-corner box with a title embedded in the top edge. Defaults to terminal width."""
    cols = width or shutil.get_terminal_size().columns
    inner = cols - 4
    head = "╭── " + title + " "
    head_len = len(head)
    pad = cols - head_len - 1
    print(Style.DIM + head + "─" * max(0, pad) + "╮" + Style.RESET_ALL)
    for line in lines:
        clipped = line[:inner]
        print(Style.DIM + "│ " + Style.RESET_ALL + clipped + " " * (inner - len(clipped)) + Style.DIM + " │" + Style.RESET_ALL)
    print(Style.DIM + "╰" + "─" * (cols - 2) + "╯" + Style.RESET_ALL)


PASTE_ID_RE = re.compile(r'^/([A-Za-z0-9]{8})(?:\?.*)?$')

PRECISE_PATTERNS = [
    ("AWS access key", re.compile(r'\b((?:AKIA|ASIA)[0-9A-Z]{16})\b')),
    ("GitHub token", re.compile(r'\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{23,})\b')),
    ("Slack token", re.compile(r'\b(xox[baprs]-[0-9]{10,12}-[0-9A-Za-z-]{10,}-[0-9A-Za-z-]{20,32})\b')),
    ("private key header", re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED |DSA )?PRIVATE KEY-----')),
    ("Google API key", re.compile(r'\b(AIza[0-9A-Za-z_-]{35})\b')),
    ("SQL insert sensitive table", re.compile(
        r'\binsert\s+into\s+'
        r'(users?|passwords?|credentials?|accounts?|admins?|'
        r'customers?|members?|logins?|sessions?|tokens?|keys?|'
        r'employees?|patients?|payments?|billing|credit_cards?|'
        r'bank_accounts?|addresses?|phones?|profiles?|'
        r'auth|wp_users?|subscriptions?|configurations?|secrets?|'
        r'backups?|dumps?|leaks?|employees?|orders?|transactions?|'
        r'contacts?)'
        r'\b', re.IGNORECASE)),
    ("password assignment", re.compile(r'\b(?:passwd|password)\s*[:=]\s*([^\s,:;@]{12,})', re.IGNORECASE)),
    ("API key assignment", re.compile(r'\bapi[_-]?key\s*[:=]\s*([^\s,:;@]{12,})', re.IGNORECASE)),
    ("secret assignment", re.compile(r'\bsecret\s*[:=]\s*([^\s,:;@]{12,})', re.IGNORECASE)),
]


def short(value, limit=30):
    """Truncate a value for console output, appending a horizontal ellipsis."""
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def sanitize_filename(value, limit=24):
    """Turn an arbitrary matched value into a short, safe filename fragment."""
    cleaned = re.sub(r'[^A-Za-z0-9_.-]', '_', value)
    cleaned = cleaned.strip("._")
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rstrip("._")
    return cleaned or "match"


class ScavUtility:
    EMAIL_REGEX = re.compile(
        r'^(?=.{1,64}@)[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*@[^-][A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*(\.[A-Za-z]{2,})$'
    )

    def check(self, email):
        if self.EMAIL_REGEX.search(email):
            return 1
        else:
            return 0

    def loadSearchTerms(self):
        searchterms = set()
        f = open("configs/searchterms.txt", "r")
        tmpcontent = f.readlines()
        f.close()

        for tmpline in tmpcontent:
            tmpline = tmpline.strip()
            if tmpline:
                searchterms.add(tmpline)
        return searchterms

    def analyze_content(self, content, search_terms):
        """Scan paste content for credentials or other sensitive data.

        content: iterable of lines (a str split on newlines works too).
        Returns a list of (category, value, bucket) tuples where bucket is
        "passwords" or "sensitive". Categories cover email:password pairs
        and substring search terms.
        """
        matches = []
        seen = set()

        def add(category, value, bucket):
            key = (category, value)
            if key not in seen:
                seen.add(key)
                matches.append((category, value, bucket))

        for line in content:
            line = line.strip()
            if not line:
                continue

            email_hit = False
            if "@" in line and ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    if left and "@" in left and self.check(left) == 1:
                        password = right.split(" ")[0].split("|")[0]
                        if 4 <= len(password) <= 40 and not password.startswith(("/", "~")):
                            email_hit = True
                            add("email:password", left + ":" + password, "passwords")

            for name, pattern in PRECISE_PATTERNS:
                m = pattern.search(line)
                if m:
                    value = m.group(1) if m.lastindex else m.group(0)
                    add(name, value, "sensitive")

            for search_item in search_terms:
                if search_item in line:
                    add("keyword", search_item, "sensitive")

        return matches

    def archivepastes(self, directory):
        source = os.path.basename(os.path.normpath(directory))
        pastecount = len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])
        if pastecount > 48000:
            archivepath = source + "_" + str(time.time()) + ".zip"
            suffix = 1
            while os.path.exists(archivepath):
                archivepath = source + "_" + str(time.time()) + "_" + str(suffix) + ".zip"
                suffix += 1
            with zipfile.ZipFile(archivepath, "w", zipfile.ZIP_DEFLATED) as archive:
                for name in os.listdir(directory):
                    filepath = os.path.join(directory, name)
                    if os.path.isfile(filepath):
                        archive.write(filepath, filepath)
            shutil.move(archivepath, "archive/")
            for name in os.listdir(directory):
                filepath = os.path.join(directory, name)
                if os.path.isfile(filepath):
                    os.remove(filepath)


class DatabaseTracker:
    """SQLite-backed dedup tracker for paste IDs. Handles migration from legacy flat files."""

    def __init__(self, db_path, table="pastes", legacy_log=None):
        self.table = table
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS " + table + " (id TEXT PRIMARY KEY)")
        if legacy_log and os.path.exists(legacy_log):
            self._migrate(legacy_log)

    def _migrate(self, path):
        with open(path) as f:
            ids = [line.strip() for line in f if line.strip()]
        for pid in ids:
            self.conn.execute("INSERT OR IGNORE INTO " + self.table + " VALUES (?)", (pid,))
        self.conn.commit()
        os.remove(path)
        log("OK", "migrated " + os.path.basename(path) + " → " + os.path.basename(self.conn.execute("PRAGMA database").fetchone()[0]))

    def has(self, paste_id):
        return self.conn.execute("SELECT 1 FROM " + self.table + " WHERE id = ?", (paste_id,)).fetchone() is not None

    def add(self, paste_id):
        self.conn.execute("INSERT OR IGNORE INTO " + self.table + " VALUES (?)", (paste_id,))
        self.conn.commit()


# ---------------------------------------------------------------------------
# Shared helpers for scrapers
# ---------------------------------------------------------------------------

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


def save_paste(source_dir, paste_id, pastepath, content, search_terms):
    """Analyze content and save to appropriate dir. Returns hit count."""
    safe_id = paste_id.replace("/", "--")
    tools = ScavUtility()
    matches = tools.analyze_content(content.splitlines(), search_terms)

    for category, value, _ in matches:
        log("OK", category + " detected - " + short(value))

    passwords = [m for m in matches if m[2] == "passwords"]
    sensitive = [m for m in matches if m[2] == "sensitive"]
    hitcounter = 0
    if passwords:
        hitcounter = 1
        shutil.copy2(pastepath, "data/files_with_passwords/" + source_dir + "/.")
        log("OK", "credentials saved to data/files_with_passwords/" + source_dir + "/ (" + paste_id + ")")
    elif sensitive:
        hitcounter = 1
        cat, val, _ = sensitive[0]
        if cat == "keyword":
            label = sanitize_filename("keyword_" + val)
        else:
            label = sanitize_filename(cat)
        shutil.copy2(pastepath, "data/otherSensitivePastes/" + source_dir + "/" + label + "_" + safe_id)
        log("OK", "sensitive data saved to data/otherSensitivePastes/" + source_dir + "/ (" + paste_id + ")")
    return hitcounter


def setup_signals():
    """Set up SIGINT/SIGTERM handlers so the scraper exits gracefully. Returns a running flag list."""
    flag = [True]
    def handler(sig, frame):
        flag[0] = False
        log("WARN", "shutting down...")
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    return flag


def run_scraper(
    source_name,
    session_name,
    archive_url,
    link_re,
    fetch_raw,
    *,
    source_dir=None,
    dedup_table="crawled",
    item_sleep=(5, 10),
    pass_sleep=300,
    backoff_max=900,
    per_pass_session=False,
    verify=True,
):
    """Run an infinite-loop scraper with the standard pattern.

    Parameters
    ----------
    source_name : str          — short source identifier ("pastebin", "github", …)
    session_name : str         — tmux session name for the banner
    archive_url : str          — URL to poll for new links
    link_re : compiled regex   — extracts paste ID from <a href> (group 1)
    fetch_raw : callable(str)  — takes paste_id, returns content string or None
    source_dir : str | None    — override subdirectory under data/raw_pastes/…
    dedup_table : str          — name of the SQLite table to use
    item_sleep : (int, int)    — (min, max) seconds between items
    pass_sleep : int           — seconds between passes
    backoff_max : int          — max exponential backoff seconds
    per_pass_session : bool    — fresh requests.session() each pass?
    verify : bool              — verify TLS certificates? (set False for broken certs like dpaste)
    """
    running = setup_signals()
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    tools = ScavUtility()
    search_terms = tools.loadSearchTerms()
    tracked = DatabaseTracker("logs/tracker.db", table=dedup_table)
    sdir = source_dir or source_name
    backoff = 5

    import requests
    ua = {"User-Agent": DEFAULT_UA}

    banner([session_name, "polls " + archive_url,
            str(len(search_terms)) + " search terms loaded · email:password detection always on"])

    def make_session():
        s = requests.session()
        s.headers.update(ua)
        s.verify = verify
        return s

    session = make_session()

    while running[0]:
        if per_pass_session:
            session = make_session()

        divider(session_name + " pass")
        log("INFO", "archiving raw_pastes if the fetch threshold is reached")
        tools.archivepastes("data/raw_pastes/" + sdir)

        try:
            resp = session.get(archive_url, timeout=15)
            if resp.status_code != 200:
                log("WARN", archive_url + " returned " + str(resp.status_code) + " — retrying later")
                if per_pass_session:
                    del session
                time.sleep(backoff)
                backoff = min(backoff * 2, backoff_max)
                continue

            from bs4 import BeautifulSoup, SoupStrainer
            soup = BeautifulSoup(resp.text, 'html.parser', parse_only=SoupStrainer('a'))
            time.sleep(random.randint(3, 6))

            newcounter = 0
            hitcounter = 0
            seen = set()

            for link in soup:
                if not running[0]:
                    break
                href = link.get('href')
                if not href:
                    continue
                m = link_re.match(href)
                if not m:
                    continue
                pid = m.group(1)
                safe_pid = pid.replace("/", "--")
                if pid in seen:
                    continue
                seen.add(pid)

                if tracked.has(pid) or os.path.exists("data/raw_pastes/" + sdir + "/" + safe_pid):
                    continue

                log("INFO", "crawling " + source_name + " " + pid)
                try:
                    content = fetch_raw(pid, session)
                    if content is None:
                        log("WARN", source_name + " " + pid + " returned no content — skipping")
                        tracked.add(pid)
                        continue

                    pastepath = "data/raw_pastes/" + sdir + "/" + safe_pid
                    with open(pastepath, "w") as f:
                        f.write(content)
                    tracked.add(pid)
                    newcounter += 1

                    hitcounter += save_paste(sdir, pid, pastepath, content, search_terms)

                    time.sleep(random.randint(*item_sleep))
                except Exception as e:
                    log("ERROR", source_name + " " + pid + " failed: " + str(e))
                    time.sleep(10)
                    continue

            if per_pass_session and running[0]:
                del session

            divider()
            log("OK", "pass complete — crawled " + str(newcounter) + " new, found " + str(hitcounter) + " hit(s)")
            backoff = 5

            if running[0]:
                log("INFO", "sleeping " + str(pass_sleep) + "s before the next pass")
                remaining = pass_sleep
                while remaining > 0 and running[0]:
                    time.sleep(min(5, remaining))
                    remaining -= 5

        except requests.exceptions.RequestException as e:
            log("ERROR", "request failed: " + str(e))
            log("WARN", "backing off " + str(backoff) + "s")
            if per_pass_session:
                del session
            time.sleep(backoff)
            backoff = min(backoff * 2, backoff_max)
            continue