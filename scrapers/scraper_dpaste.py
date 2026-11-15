#!/usr/bin/python
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Dpaste.com scraper — polls https://dpaste.com/public/ for new pastes."""
import re
from classes.utility import run_scraper

DPASTE_RE = re.compile(r'^/([A-Za-z0-9]{9})$')

def fetch_raw(pid, session):
    resp = session.get("https://dpaste.com/" + pid + ".txt", timeout=10)
    if resp.status_code != 200:
        return None
    return resp.text

run_scraper(
    "dpaste", "s-dpaste",
    "https://dpaste.com/public/", DPASTE_RE, fetch_raw,
    dedup_table="crawled",
    item_sleep=(3, 8),
    pass_sleep=180,
    backoff_max=900,
    verify=False,
)