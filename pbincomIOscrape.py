import json
import os
import random
import shutil
import string
import time

import requests
import classes.utility
from classes.utility import DatabaseTracker, banner, divider, log, sanitize_filename, short

tools = classes.utility.ScavUtility()
session = requests.session()
searchTerms = tools.loadSearchTerms()

try:
    with open("configs/pastesio.json") as f:
        cfg = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log("ERROR", "configs/pastesio.json missing or invalid")
    raise SystemExit(1)

TIER = cfg.get("tier", "free")
API_KEY = cfg.get("api_key", "")
HEADERS = {}
if API_KEY:
    HEADERS["Authorization"] = "Bearer " + API_KEY

tried = DatabaseTracker("logs/triedpastesio.db")
CHARS = string.ascii_letters + string.digits


def random_id():
    return "".join(random.choices(CHARS, k=8))


def sleep_until_midnight():
    now = time.time()
    midnight = int(now // 86400 + 1) * 86400
    delta = midnight - now + 60
    log("INFO", "daily limit reached — sleeping " + str(int(delta // 60)) + "m until UTC midnight")
    time.sleep(delta)


def handle(response):
    """Process a pastes.io response. Returns True if we should try another ID."""
    if response.status_code == 200:
        data = response.json()
        paste_id = data["success"]["slug"]
        pastepath = "data/raw_pastes/pastesio/" + paste_id
        if os.path.exists(pastepath):
            return True

        content = data["success"]["content"]
        log("OK", "hit — " + paste_id)
        with open(pastepath, "w") as f:
            f.write(content)
        tried.add(paste_id)

        matches = tools.analyze_content(content.splitlines(), searchTerms)
        for category, value, _ in matches:
            log("OK", category + " detected - " + short(value))

        passwords = [m for m in matches if m[2] == "passwords"]
        sensitive = [m for m in matches if m[2] == "sensitive"]
        if passwords:
            log("OK", "credentials saved to data/files_with_passwords/pastesio/ (" + paste_id + ")")
            shutil.copy2(pastepath, "data/files_with_passwords/pastesio/.")
        elif sensitive:
            label = sanitize_filename(sensitive[0][1])
            log("OK", "sensitive data saved to data/otherSensitivePastes/pastesio/ (" + paste_id + ")")
            shutil.copy2(pastepath, "data/otherSensitivePastes/pastesio/" + label + "_" + paste_id)

        return True

    if response.status_code == 404:
        return True

    if response.status_code == 429:
        remaining = int(response.headers.get("RateLimit-Remaining", 0))
        if TIER == "free" or remaining == 0:
            sleep_until_midnight()
            return True
        retry = int(response.headers.get("Retry-After", 60))
        log("WARN", "rate limited — sleeping " + str(retry) + "s")
        time.sleep(retry)
        return True

    log("ERROR", "unexpected status " + str(response.status_code) + " for " + response.url)
    time.sleep(60)
    return True


banner(["pastesioScrape", "random-ID guesser — GET https://pastes.io/api/pastes/{id}",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on",
        "tier: " + TIER + " · key: " + ("set" if API_KEY else "none")])

while True:
    tools.archivepastes("data/raw_pastes/pastesio")
    pid = random_id()
    if tried.has(pid):
        continue

    url = "https://pastes.io/api/pastes/" + pid
    try:
        resp = session.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            log("INFO", "trying " + pid + " — hit")
        elif resp.status_code == 404:
            tried.add(pid)
            log("INFO", "trying " + pid + " — miss")
        handle(resp)
        time.sleep(random.randint(5, 10))
    except Exception as e:
        log("ERROR", "request failed for " + pid + ": " + str(e))
        time.sleep(30)