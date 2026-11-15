#!/usr/bin/python
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Pastebin archive scraper — polls https://pastebin.com/archive for new pastes."""
import re
from classes.utility import PASTE_ID_RE, run_scraper

UA = "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"

def fetch_raw(pid, session):
    session.headers.update({"User-Agent": UA})
    resp = session.get("https://pastebin.com/raw/" + pid, timeout=10)
    if resp.status_code != 200:
        return None
    return resp.content.decode("utf-8", errors="replace")

run_scraper(
    "pastebin", "s-pastebin-archive",
    "https://pastebin.com/archive", PASTE_ID_RE, fetch_raw,
    source_dir="pastebin",
    dedup_table="crawled",
    item_sleep=(5, 10),
    pass_sleep=300,
)