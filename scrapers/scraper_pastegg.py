#!/usr/bin/python
"""paste.gg scraper — polls https://api.paste.gg/v1/pastes for new pastes."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import random
import time

import requests
from classes.utility import (
    ScavUtility, DatabaseTracker, banner, divider, log, sanitize_filename, short, save_paste, setup_signals,
)

running = setup_signals()
tools = ScavUtility()
session = requests.session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
searchTerms = tools.loadSearchTerms()

_last_mtime = 0

tracked = DatabaseTracker("logs/tracker.db", table="tried_pastegg")
backoff = 5

banner(["s-pastegg", "polls https://api.paste.gg/v1/pastes for new pastes",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

while running[0]:
    divider("pastegg pass")
    # Auto-reload search terms if file changed on disk
    try:
        mtime = os.path.getmtime("configs/searchterms.txt")
        if mtime != _last_mtime:
            _last_mtime = mtime
            new_terms = tools.loadSearchTerms()
            searchTerms.clear()
            searchTerms.update(new_terms)
            log("OK", "reloaded " + str(len(searchTerms)) + " search terms (file changed)")
    except OSError:
        pass

    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/pastegg")

    try:
        resp = session.get("https://api.paste.gg/v1/pastes?limit=50", timeout=15)
        if resp.status_code != 200:
            log("WARN", "API returned " + str(resp.status_code) + " — retrying later")
            time.sleep(backoff)
            backoff = min(backoff * 2, 900)
            continue

        data = resp.json()
        if data.get("status") != "success" or "result" not in data:
            log("WARN", "unexpected API response — retrying later")
            time.sleep(backoff)
            backoff = min(backoff * 2, 900)
            continue

        newcounter = 0
        hitcounter = 0

        for entry in data["result"]:
            if not running[0]:
                break
            paste_id = entry.get("id", "")
            if not paste_id:
                continue

            if tracked.has(paste_id):
                continue

            log("INFO", "crawling pastegg " + paste_id)
            try:
                # Fetch paste detail to get file IDs
                detail = session.get("https://api.paste.gg/v1/pastes/" + paste_id, timeout=10)
                if detail.status_code != 200:
                    log("WARN", "pastegg " + paste_id + " detail returned " + str(detail.status_code) + " — skipping")
                    tracked.add(paste_id)
                    continue

                detail_data = detail.json()
                if detail_data.get("status") != "success" or "result" not in detail_data:
                    tracked.add(paste_id)
                    continue

                files = detail_data["result"].get("files", [])
                if not files:
                    tracked.add(paste_id)
                    continue

                # Fetch raw content for each file and combine
                content_parts = []
                for file_entry in files:
                    file_id = file_entry.get("id")
                    if not file_id:
                        continue
                    raw_url = "https://paste.gg/p/anonymous/" + paste_id + "/files/" + file_id + "/raw"
                    raw = session.get(raw_url, timeout=10)
                    if raw.status_code == 200:
                        content_parts.append(raw.text)
                    time.sleep(random.randint(1, 3))

                if not content_parts:
                    log("WARN", "pastegg " + paste_id + " — no file content retrieved")
                    tracked.add(paste_id)
                    continue

                content = "\n".join(content_parts)
                del content_parts

                pastepath = "data/raw_pastes/pastegg/" + paste_id
                with open(pastepath, "w") as f:
                    f.write(content)
                tracked.add(paste_id)
                newcounter += 1

                hitcounter += save_paste("pastegg", paste_id, pastepath, content, searchTerms)
                del content

                time.sleep(random.randint(5, 10))
            except Exception as e:
                log("ERROR", "pastegg " + paste_id + " failed: " + str(e))
                time.sleep(10)
                continue

        divider()
        log("OK", "pass complete — crawled " + str(newcounter) + " new, found " + str(hitcounter) + " hit(s)")
        backoff = 5
        log("INFO", "sleeping 180s before the next pass")
        remaining = 180
        while remaining > 0 and running[0]:
            time.sleep(min(5, remaining))
            remaining -= 5

    except requests.exceptions.RequestException as e:
        log("ERROR", "API request failed: " + str(e))
        log("WARN", "backing off " + str(backoff) + "s")
        time.sleep(backoff)
        backoff = min(backoff * 2, 900)
        continue