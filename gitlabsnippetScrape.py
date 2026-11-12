import gc
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
searchTerms = tools.loadSearchTerms()

tracked = DatabaseTracker("logs/tracker.db", table="tried_gitlab")
GITLAB_SNIPPET_RE = re.compile(r'^/[-]/snippets/(\d+)$')

backoff = 5

banner(["gitlabSnippetScrape", "polls https://gitlab.com/explore/snippets for latest public snippets",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

while True:
    session = requests.session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
    divider("gitlab pass")
    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/gitlab")

    try:
        response = session.get("https://gitlab.com/explore/snippets", timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a'))
        del response
        time.sleep(random.randint(5, 10))

        newcounter = 0
        hitcounter = 0
        seen = set()

        for link in soup:
            href = link.get('href')
            if not href:
                continue
            m = GITLAB_SNIPPET_RE.match(href)
            if not m:
                continue
            snippet_id = m.group(1)
            if snippet_id in seen:
                continue
            seen.add(snippet_id)

            if tracked.has(snippet_id) or os.path.exists("data/raw_pastes/gitlab/" + snippet_id):
                continue

            log("INFO", "crawling gitlab snippet " + snippet_id)
            try:
                raw = session.get("https://gitlab.com/-/snippets/" + snippet_id + "/raw",
                                  timeout=10)
                if raw.status_code != 200:
                    log("WARN", "gitlab snippet " + snippet_id + " returned " + str(raw.status_code) + " — skipping")
                    tracked.add(snippet_id)
                    del raw
                    continue

                # GitLab returns tar.gz for multi-file snippets — skip those
                content_type = raw.headers.get("Content-Type", "")
                if "x-gzip" in content_type or "tar" in content_type or "octet-stream" in content_type:
                    log("WARN", "gitlab snippet " + snippet_id + " is multi-file (tar.gz) — skipping")
                    tracked.add(snippet_id)
                    del raw
                    continue

                content = raw.text
                del raw
                pastepath = "data/raw_pastes/gitlab/" + snippet_id
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
                    log("OK", "credentials saved to data/files_with_passwords/gitlab/ (" + snippet_id + ")")
                    shutil.copy2(pastepath, "data/files_with_passwords/gitlab/.")
                elif sensitive:
                    hitcounter += 1
                    label = sanitize_filename(sensitive[0][1])
                    log("OK", "sensitive data saved to data/otherSensitivePastes/gitlab/ (" + snippet_id + ")")
                    shutil.copy2(pastepath, "data/otherSensitivePastes/gitlab/" + label + "_" + snippet_id)
                tracked.add(snippet_id)
                del matches

                time.sleep(random.randint(15, 30))
            except Exception as e:
                log("ERROR", "gitlab snippet " + snippet_id + " failed: " + str(e))
                time.sleep(30)
                continue

        del soup
        del session
        gc.collect()
        divider()
        log("OK", "pass complete — crawled " + str(newcounter) + " new snippet(s), found " + str(hitcounter) + " hit(s)")
        backoff = 5
        log("INFO", "sleeping 240s before the next pass")
        time.sleep(240)

    except requests.exceptions.RequestException as e:
        log("ERROR", "explore page failed: " + str(e))
        log("WARN", "backing off " + str(backoff) + "s")
        del session
        gc.collect()
        time.sleep(backoff)
        backoff = min(backoff * 2, 1800)
        continue