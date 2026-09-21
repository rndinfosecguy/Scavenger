#!/usr/bin/python

import datetime
import os
import random
import re
import shutil
import sqlite3
import sys
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


def progress_bar(current, total, hits):
    """Draw a colorized progress bar in place."""
    cols = shutil.get_terminal_size().columns
    bar_width = max(10, cols - 42)
    pct = current / total if total > 0 else 0
    filled = int(bar_width * pct)
    bar = "█" * filled + "░" * (bar_width - filled)
    sys.stdout.write(
        "\r" + Style.DIM + bar + Style.RESET_ALL + " "
        + Fore.CYAN + "{:3.0f}%".format(pct * 100) + Style.RESET_ALL + " "
        + Style.DIM + str(current) + "/" + str(total) + " files · " + str(hits) + " hit(s)" + Style.RESET_ALL + "  ")
    sys.stdout.flush()


PASTE_ID_RE = re.compile(r'^/([A-Za-z0-9]{8})(?:\?.*)?$')

PRECISE_PATTERNS = [
    ("AWS access key", re.compile(r'\b((?:AKIA|ASIA)[0-9A-Z]{16})\b')),
    ("GitHub token", re.compile(r'\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{23,})\b')),
    ("Slack token", re.compile(r'\b(xox[baprs]-[0-9]{10,12}-[0-9A-Za-z-]{10,}-[0-9A-Za-z-]{20,32})\b')),
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

    def __init__(self):
        pass

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
                        if 4 <= len(password) <= 40:
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

    def __init__(self, db_path, legacy_log=None):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS pastes (id TEXT PRIMARY KEY)")
        if legacy_log and os.path.exists(legacy_log):
            self._migrate(legacy_log)

    def _migrate(self, path):
        with open(path) as f:
            ids = [line.strip() for line in f if line.strip()]
        for pid in ids:
            self.conn.execute("INSERT OR IGNORE INTO pastes VALUES (?)", (pid,))
        self.conn.commit()
        os.remove(path)
        log("OK", "migrated " + os.path.basename(path) + " → " + os.path.basename(self.conn.execute("PRAGMA database").fetchone()[0]))

    def has(self, paste_id):
        return self.conn.execute("SELECT 1 FROM pastes WHERE id = ?", (paste_id,)).fetchone() is not None

    def add(self, paste_id):
        self.conn.execute("INSERT OR IGNORE INTO pastes VALUES (?)", (paste_id,))
        self.conn.commit()

    def load_all(self):
        return {row[0] for row in self.conn.execute("SELECT id FROM pastes")}

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM pastes").fetchone()[0]

    def close(self):
        self.conn.close()