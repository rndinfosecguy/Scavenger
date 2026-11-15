#!/usr/bin/python
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Pastecode.io scraper — polls https://pastecode.io/archive for new snippets."""
import re
from bs4 import BeautifulSoup, SoupStrainer
from classes.utility import run_scraper

PASTECODE_RE = re.compile(r'^/s/([A-Za-z0-9]{8})(?:\?.*)?$')

def fetch_raw(pid, session):
    resp = session.get("https://pastecode.io/s/" + pid, timeout=10)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, 'html.parser', parse_only=SoupStrainer('pre'))
    pre = soup.find('pre')
    return pre.get_text() if pre else None

run_scraper(
    "pastecode", "s-pastecode",
    "https://pastecode.io/archive", PASTECODE_RE, fetch_raw,
    dedup_table="tried_pastecode",
    item_sleep=(3, 6),
    pass_sleep=180,
    backoff_max=900,
)