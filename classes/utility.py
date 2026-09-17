#!/usr/bin/python

import datetime
import os
import re
import shutil
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

USERNAME_PASS_RE = re.compile(r'(?:^|[^A-Za-z0-9._-])([A-Za-z0-9][A-Za-z0-9._-]{2,31}):([^\s,:;@|()"\'\\]+)')
USERNAME_STOPLIST = {
    "localhost", "host", "hostname", "host_name", "port", "server", "database", "db",
    "schema", "scheme", "protocol", "proto", "charset", "encoding", "language", "lang",
    "name", "title", "note", "value", "text", "body", "subject", "from", "to", "cc",
    "bcc", "version", "type", "path", "url", "uri", "href", "ref", "user", "username",
    "login", "email", "password", "passwd", "pwd", "key", "token", "secret", "apikey",
    "api_key", "created", "updated", "date", "time",
    "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "rip",
    "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15",
    "eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp",
    "cs", "ds", "es", "fs", "gs", "ss", "phys", "mem", "virt",
}
ALL_HEX_TOKEN_RE = re.compile(r"^[0-9a-fA-F]{9,}$")
ALL_DIGIT_TOKEN_RE = re.compile(r"^[0-9]{7,}$")


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
        "passwords" or "sensitive". Categories cover email:password pairs,
        username:password pairs, and substring search terms.
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

            if ":" in line and not email_hit:
                m = USERNAME_PASS_RE.search(line)
                if m:
                    username = m.group(1)
                    token = m.group(2)
                    if (username.lower() not in USERNAME_STOPLIST
                            and re.search(r"[A-Za-z]", username)
                            and token[0].isalnum()
                            and not m.string[m.end():m.end() + 1] == "("
                            and not token.startswith("//")
                            and not ALL_HEX_TOKEN_RE.fullmatch(token)
                            and not ALL_DIGIT_TOKEN_RE.fullmatch(token)
                            and not (username.isupper() and token.isupper() and token.isalpha())
                            and 4 <= len(token) <= 40):
                        add("username:password", username + ":" + token, "passwords")

            for search_item in search_terms:
                if search_item in line:
                    add("keyword", search_item, "sensitive")

        return matches

    def archivepastes(self, directory):
        pastecount = len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])
        if pastecount > 48000:
            archivepath = "pastebin_" + str(time.time()) + ".zip"
            suffix = 1
            while os.path.exists(archivepath):
                archivepath = "pastebin_" + str(time.time()) + "_" + str(suffix) + ".zip"
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