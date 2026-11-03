import os
import random
import re
import shutil
import time

import requests
from bs4 import BeautifulSoup, SoupStrainer

import classes.utility
from classes.utility import DatabaseTracker, banner, divider, log, sanitize_filename, short

tools = classes.utility.ScavUtility()
session = requests.session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
searchTerms = tools.loadSearchTerms()

tracked = DatabaseTracker("logs/tracker.db", table="tried_pastecode")
PASTECODE_LINK_RE = re.compile(r'^/s/([A-Za-z0-9]{8})(?:\?.*)?$')

backoff = 5


def fetch_snippet_content(paste_id):
    """Fetch one pastecode.io snippet page and return its body text, or None.

    Pastecode.io renders snippets server-side; the body lives in a single
    <pre> element (CSS-blurred for anonymous visitors but fully present in
    the DOM). /s/{id}/raw serves HTML, not plain text, so we parse the page.
    Password-protected / encrypted / expired snippets render without a <pre>.
    """
    response = session.get("https://pastecode.io/s/" + paste_id, timeout=10)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('pre'))
    del response
    pre = soup.find('pre')
    if pre is None:
        return None
    return pre.get_text()


banner(["pastecodeScrape", "polls https://pastecode.io/archive for latest public snippets",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

while True:
    divider("pastecode pass")
    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/pastecode")

    try:
        response = session.get("https://pastecode.io/archive", timeout=15)
        time.sleep(random.randint(3, 6))

        newcounter = 0
        hitcounter = 0
        seen = set()

        for link in BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a')):
            href = link.get('href')
            if not href:
                continue
            m = PASTECODE_LINK_RE.match(href)
            if not m:
                continue
            paste_id = m.group(1)
            if paste_id in seen:
                continue
            seen.add(paste_id)

            if tracked.has(paste_id) or os.path.exists("data/raw_pastes/pastecode/" + paste_id):
                continue

            log("INFO", "crawling pastecode " + paste_id)
            try:
                content = fetch_snippet_content(paste_id)
                if content is None:
                    log("WARN", "pastecode " + paste_id + " returned no snippet body — skipping")
                    tracked.add(paste_id)
                    continue

                pastepath = "data/raw_pastes/pastecode/" + paste_id
                with open(pastepath, "w") as f:
                    f.write(content)
                tracked.add(paste_id)
                newcounter += 1

                matches = tools.analyze_content(content.splitlines(), searchTerms)
                for category, value, _ in matches:
                    log("OK", category + " detected - " + short(value))

                passwords = [m for m in matches if m[2] == "passwords"]
                sensitive = [m for m in matches if m[2] == "sensitive"]
                if passwords:
                    hitcounter += 1
                    log("OK", "credentials saved to data/files_with_passwords/pastecode/ (" + paste_id + ")")
                    shutil.copy2(pastepath, "data/files_with_passwords/pastecode/.")
                elif sensitive:
                    hitcounter += 1
                    label = sanitize_filename(sensitive[0][1])
                    log("OK", "sensitive data saved to data/otherSensitivePastes/pastecode/ (" + paste_id + ")")
                    shutil.copy2(pastepath, "data/otherSensitivePastes/pastecode/" + label + "_" + paste_id)

                time.sleep(random.randint(3, 6))
            except Exception as e:
                log("ERROR", "pastecode " + paste_id + " failed: " + str(e))
                time.sleep(10)
                continue

        del response
        divider()
        log("OK", "pass complete — crawled " + str(newcounter) + " new snippet(s), found " + str(hitcounter) + " hit(s)")
        backoff = 5
        log("INFO", "sleeping 180s before the next pass")
        time.sleep(180)

    except requests.exceptions.RequestException as e:
        log("ERROR", "archive page failed: " + str(e))
        log("WARN", "backing off " + str(backoff) + "s")
        time.sleep(backoff)
        backoff = min(backoff * 2, 900)
        continue