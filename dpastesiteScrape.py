import os
import random
import re
import shutil
import time

import requests
import urllib3
from bs4 import BeautifulSoup, SoupStrainer

import classes.utility
from classes.utility import DatabaseTracker, banner, divider, log, sanitize_filename, short

tools = classes.utility.ScavUtility()
session = requests.session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
searchTerms = tools.loadSearchTerms()

tracked = DatabaseTracker("logs/tracker.db", table="crawled")
DPASTE_ID_RE = re.compile(r'^/([A-Za-z0-9]{9})$')

backoff = 5

banner(["dpasteScrape", "polls https://dpaste.com/public/ for latest pastes",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

while True:
    divider("dpaste pass")
    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/dpaste")

    try:
        response = session.get("https://dpaste.com/public/", timeout=15)
        time.sleep(random.randint(3, 6))

        newcounter = 0
        hitcounter = 0

        for link in BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a')):
            href = link.get('href')
            if not href:
                continue
            m = DPASTE_ID_RE.match(href)
            if not m:
                continue
            paste_id = m.group(1)

            if tracked.has(paste_id) or os.path.exists("data/raw_pastes/dpaste/" + paste_id):
                continue

            log("INFO", "crawling dpaste " + paste_id)
            try:
                raw = session.get("https://dpaste.com/" + paste_id + ".txt", timeout=10)
                if raw.status_code != 200:
                    log("WARN", "dpaste " + paste_id + " returned " + str(raw.status_code) + " — skipping")
                    tracked.add(paste_id)
                    continue

                content = raw.text
                pastepath = "data/raw_pastes/dpaste/" + paste_id
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
                    log("OK", "credentials saved to data/files_with_passwords/dpaste/ (" + paste_id + ")")
                    shutil.copy2(pastepath, "data/files_with_passwords/dpaste/.")
                elif sensitive:
                    hitcounter += 1
                    label = sanitize_filename(sensitive[0][1])
                    log("OK", "sensitive data saved to data/otherSensitivePastes/dpaste/ (" + paste_id + ")")
                    shutil.copy2(pastepath, "data/otherSensitivePastes/dpaste/" + label + "_" + paste_id)

                time.sleep(random.randint(3, 8))
            except Exception as e:
                log("ERROR", "dpaste " + paste_id + " failed: " + str(e))
                time.sleep(10)
                continue

        del response
        divider()
        log("OK", "pass complete — crawled " + str(newcounter) + " new paste(s), found " + str(hitcounter) + " hit(s)")
        backoff = 5
        log("INFO", "sleeping 180s before the next pass")
        time.sleep(180)

    except requests.exceptions.RequestException as e:
        log("ERROR", "public page failed: " + str(e))
        log("WARN", "backing off " + str(backoff) + "s")
        time.sleep(backoff)
        backoff = min(backoff * 2, 900)
        continue