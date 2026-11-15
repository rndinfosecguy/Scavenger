#!/usr/bin/python
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""GitLab snippet scraper — polls https://gitlab.com/explore/snippets for new snippets."""
import gc
import re
from classes.utility import run_scraper

GITLAB_RE = re.compile(r'^/[-]/snippets/(\d+)$')

def fetch_raw(pid, session):
    resp = session.get("https://gitlab.com/-/snippets/" + pid + "/raw", timeout=10)
    if resp.status_code != 200:
        return None
    # Skip multi-file snippets (returned as tar.gz)
    content_type = resp.headers.get("Content-Type", "")
    if "x-gzip" in content_type or "tar" in content_type or "octet-stream" in content_type:
        return None
    return resp.text

run_scraper(
    "gitlab", "s-gitlab",
    "https://gitlab.com/explore/snippets", GITLAB_RE, fetch_raw,
    dedup_table="tried_gitlab",
    item_sleep=(15, 30),
    pass_sleep=240,
    backoff_max=1800,
    per_pass_session=True,
)