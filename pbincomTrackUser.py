import shutil
from bs4 import BeautifulSoup, SoupStrainer
import requests
import time
import classes.utility
from classes.utility import PASTE_ID_RE, banner, DatabaseTracker, divider, log, panel, sanitize_filename, short

tools = classes.utility.ScavUtility()
session = requests.session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"}
searchTerms = tools.loadSearchTerms()

tracked = DatabaseTracker("logs/trackedpastes.db", legacy_log="logs/alreadytrackedpastes.log")

banner(["pastebincomTrack", "user track - follows configs/users.txt targets",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

iterator = 1
while True:
    with open("configs/users.txt", "r") as f:
        relevantUsers = [line.strip() for line in f if line.strip()]

    divider("track round " + str(iterator))
    iterator += 1

    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes/pastebin")

    if not relevantUsers:
        log("WARN", "no tracked users in configs/users.txt - add one target per line")
        log("INFO", "sleeping 3h before the next round")
        time.sleep(10800)
        continue

    log("INFO", "tracking " + str(len(relevantUsers)) + " user(s): " + ", ".join(relevantUsers))

    for user in relevantUsers:
        try:
            log("INFO", "checking user '" + user + "'")
            response = session.get("https://pastebin.com/u/" + user, headers=headers)
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
                curPaste = session.get("https://pastebin.com/raw/" + paste_id, headers=headers)
                pastecontent = curPaste.content.decode('utf-8', errors='replace')

                matches = tools.analyze_content(pastecontent.splitlines(), searchTerms)

                pastepath = "data/raw_pastes/pastebin/" + paste_id
                f = open(pastepath, "wb")
                f.write(curPaste.content)
                f.close()
                tracked.add(paste_id)
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

                log("INFO", "sleeping 20s till the next paste")
                time.sleep(20)

            if existsCounter:
                log("WARN", "skipped " + str(existsCounter) + " already-crawled pastes for user '" + user + "'")
            panel("user '" + user + "'",
               "crawled " + str(newcounter) + " new paste(s), " + str(hitcounter) + " hit(s)",
               "sleeping 10min before the next user check")
            time.sleep(600)
        except Exception as e:
            log("ERROR", "user '" + user + "' failed: " + str(e))

    log("INFO", "sleeping 3h before the next round")
    time.sleep(10800)