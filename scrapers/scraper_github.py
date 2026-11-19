#!/usr/bin/python
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""GitHub gist scraper — polls https://gist.github.com/discover for new gists."""
import gc
import os
import random
import re
import shutil
import time

import requests
from bs4 import BeautifulSoup, SoupStrainer

from classes.utility import (
    DatabaseTracker, ScavUtility, banner, divider, log, sanitize_filename, short, setup_signals, mark_crawled,
)

running = setup_signals()
tools = ScavUtility()
session = requests.session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
searchTerms = tools.loadSearchTerms()

tracked = DatabaseTracker("logs/tracker.db", table="crawled")
GIST_LINK_RE = re.compile(r'^/([^/]+)/([a-f0-9]{32})$')

backoff = 5

banner(["s-github", "polls https://gist.github.com/discover for latest gists",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

while running[0]:
    session = requests.session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
    divider("gist pass")
    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/github")

    try:
        response = session.get("https://gist.github.com/discover", timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a'))
        del response
        time.sleep(random.randint(5, 10))

        newcounter = 0
        hitcounter = 0

        for link in soup:
            if not running[0]:
                break
            href = link.get('href')
            if not href:
                continue
            m = GIST_LINK_RE.match(href)
            if not m:
                continue
            user = m.group(1)
            gist_id = m.group(2)

            if tracked.has(gist_id):
                continue

            log("INFO", "crawling gist " + gist_id)
            try:
                raw = session.get("https://gist.github.com/" + user + "/" + gist_id + "/raw",
                                  timeout=10)
                if raw.status_code != 200:
                    log("WARN", "gist " + gist_id + " returned " + str(raw.status_code) + " — skipping")
                    tracked.add(gist_id)
                    del raw
                    continue

                content = raw.text
                del raw
                pastepath = "data/raw_pastes/github/" + gist_id
                with open(pastepath, "w") as f:
                    f.write(content)
                newcounter += 1

                matches = tools.analyze_content(content.splitlines(), searchTerms)
                del content
                for category, value, _ in matches:
                    log("OK", category + " detected - " + short(value))

                passwords = [m for m in matches if m[2] == "passwords"]
                sensitive = [m for m in matches if m[2] == "sensitive"]
                if passwords:
                    hitcounter += 1
                    log("OK", "credentials saved to data/files_with_passwords/github/ (" + gist_id + ")")
                    shutil.copy2(pastepath, "data/files_with_passwords/github/.")
                elif sensitive:
                    hitcounter += 1
                    cat, val, _ = sensitive[0]
                    if cat == "keyword":
                        label = sanitize_filename("keyword_" + val)
                    else:
                        label = sanitize_filename(cat)
                    log("OK", "sensitive data saved to data/otherSensitivePastes/github/ (" + gist_id + ")")
                    shutil.copy2(pastepath, "data/otherSensitivePastes/github/" + label + "_" + gist_id)
                tracked.add(gist_id)
                del matches

                time.sleep(random.randint(15, 30))
            except Exception as e:
                log("ERROR", "gist " + gist_id + " failed: " + str(e))
                time.sleep(30)
                continue

        del soup
        del session
        gc.collect()
        divider()
        log("OK", "pass complete — crawled " + str(newcounter) + " new gist(s), found " + str(hitcounter) + " hit(s)")
        mark_crawled("github")
        backoff = 5
        log("INFO", "sleeping 240s before the next pass")
        time.sleep(240)

    except requests.exceptions.RequestException as e:
        log("ERROR", "discover page failed: " + str(e))
        log("WARN", "backing off " + str(backoff) + "s")
        del session
        gc.collect()
        time.sleep(backoff)
        backoff = min(backoff * 2, 1800)
        continue