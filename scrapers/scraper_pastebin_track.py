#!/usr/bin/python
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Pastebin user track scraper — follows users listed in configs/users.txt."""
import shutil
import time
from bs4 import BeautifulSoup, SoupStrainer
import requests
from classes.utility import (
    PASTE_ID_RE, ScavUtility, DatabaseTracker, banner, divider, log, panel, sanitize_filename, short, setup_signals,
)

running = setup_signals()
tools = ScavUtility()
session = requests.session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"})
searchTerms = tools.loadSearchTerms()
tracked = DatabaseTracker("logs/tracker.db", table="crawled", legacy_log="logs/alreadytrackedpastes.log")

banner(["s-pastebin-track", "user track - follows configs/users.txt targets",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

iterator = 1
while running[0]:
    with open("configs/users.txt", "r") as f:
        relevantUsers = [line.strip() for line in f if line.strip()]

    divider("track round " + str(iterator))
    iterator += 1

    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/pastebin")

    if not relevantUsers:
        log("WARN", "no tracked users in configs/users.txt - add one target per line")
        log("INFO", "sleeping 3h before the next round")
        remaining = 10800
        while remaining > 0 and running[0]:
            time.sleep(min(5, remaining))
            remaining -= 5
        continue

    log("INFO", "tracking " + str(len(relevantUsers)) + " user(s): " + ", ".join(relevantUsers))

    for user in relevantUsers:
        if not running[0]:
            break
        try:
            log("INFO", "checking user '" + user + "'")
            response = session.get("https://pastebin.com/u/" + user)
            response = response.text

            existsCounter = 0
            newcounter = 0
            hitcounter = 0
            for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
                paste_id = PASTE_ID_RE.match(link["href"]) if link.has_attr('href') else None
                if not paste_id:
                    continue
                paste_id = paste_id.group(1)
                if tracked.has(paste_id):
                    existsCounter += 1
                    continue

                log("INFO", "crawling " + paste_id)
                try:
                    curPaste = session.get("https://pastebin.com/raw/" + paste_id)
                    pastecontent = curPaste.content.decode('utf-8', errors='replace')

                    matches = tools.analyze_content(pastecontent.splitlines(), searchTerms)

                    pastepath = "data/raw_pastes/pastebin/" + paste_id
                    f = open(pastepath, "wb")
                    f.write(curPaste.content)
                    f.close()
                    newcounter += 1

                    for category, value, _ in matches:
                        log("OK", category + " detected - " + short(value))

                    passwords = [m for m in matches if m[2] == "passwords"]
                    sensitive = [m for m in matches if m[2] == "sensitive"]
                    if passwords:
                        hitcounter += 1
                        log("OK", "credentials saved to data/files_with_passwords/pastebin/ (" + paste_id + ")")
                        shutil.copy2(pastepath, "data/files_with_passwords/pastebin/.")
                    elif sensitive:
                        hitcounter += 1
                        label = sanitize_filename(sensitive[0][1])
                        log("OK", "sensitive data saved to data/otherSensitivePastes/pastebin/ (" + paste_id + ")")
                        shutil.copy2(pastepath, "data/otherSensitivePastes/pastebin/" + label + "_" + paste_id)
                    tracked.add(paste_id)

                    log("INFO", "sleeping 20s till the next paste")
                    time.sleep(20)
                except Exception as e:
                    log("ERROR", paste_id + " failed: " + str(e))
                    continue

            if existsCounter:
                log("WARN", "skipped " + str(existsCounter) + " already-crawled pastes for user '" + user + "'")
            panel("user '" + user + "'",
               "crawled " + str(newcounter) + " new paste(s), " + str(hitcounter) + " hit(s)",
               "sleeping 10min before the next user check")
            time.sleep(600)
        except Exception as e:
            log("ERROR", "user '" + user + "' failed: " + str(e))

    if running[0]:
        log("INFO", "sleeping 3h before the next round")
        remaining = 10800
        while remaining > 0 and running[0]:
            time.sleep(min(5, remaining))
            remaining -= 5