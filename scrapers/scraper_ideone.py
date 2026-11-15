#!/usr/bin/python
"""Ideone.com scraper — polls https://ideone.com/recent for new snippets."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from classes.utility import run_scraper

IDEONE_RE = re.compile(r'^/([A-Za-z0-9]{6})$')

def fetch_raw(pid, session):
    resp = session.get("https://ideone.com/plain/" + pid, timeout=10)
    if resp.status_code != 200:
        return None
    return resp.text

run_scraper(
    "ideone", "s-ideone",
    "https://ideone.com/recent", IDEONE_RE, fetch_raw,
    dedup_table="tried_ideone",
    item_sleep=(5, 10),
    pass_sleep=180,
    backoff_max=900,
)