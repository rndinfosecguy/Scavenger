import random
import time
import os
import shutil
import requests
from bs4 import BeautifulSoup, SoupStrainer
import classes.utility
from classes.utility import PASTE_ID_RE, banner, divider, log, panel, sanitize_filename, short

iterator = 1
tools = classes.utility.ScavUtility()
session = requests.session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"}
searchTerms = tools.loadSearchTerms()


def getjuicystuff(tmpresponse):
    existscounter = 0
    newcounter = 0
    hitcounter = 0
    for link in BeautifulSoup(tmpresponse, 'html.parser', parse_only=SoupStrainer('a')):
        paste_id = PASTE_ID_RE.match(link["href"]) if link.has_attr('href') else None
        if not paste_id:
            continue
        paste_id = paste_id.group(1)
        pastepath = "data/raw_pastes/" + paste_id
        if os.path.exists(pastepath):
            existscounter += 1
            continue
        log("INFO", "crawling " + paste_id)
        try:
            binresponse = session.get("https://pastebin.com/raw/" + paste_id, headers=headers, timeout=5)
            pastecontent = binresponse.content.decode('utf-8', errors='replace')

            matches = tools.analyze_content(pastecontent.splitlines(), searchTerms)

            file_ = open(pastepath, "wb")
            file_.write(binresponse.content)
            file_.close()
            newcounter += 1

            for category, value, _ in matches:
                log("OK", category + " detected - " + short(value))

            passwords = [m for m in matches if m[2] == "passwords"]
            sensitive = [m for m in matches if m[2] == "sensitive"]
            if passwords:
                hitcounter += 1
                log("OK", "credentials saved to data/files_with_passwords/ (" + paste_id + ")")
                shutil.copy2(pastepath, "data/files_with_passwords/.")
            elif sensitive:
                hitcounter += 1
                label = sanitize_filename(sensitive[0][1])
                log("OK", "sensitive data saved to data/otherSensitivePastes/ (" + paste_id + ")")
                shutil.copy2(pastepath, "data/otherSensitivePastes/" + label + "_" + paste_id)

            time.sleep(random.randint(5, 10))
        except Exception as eErr:
            log("ERROR", "crawl failed for " + paste_id + ": " + str(eErr))
            continue
    if existscounter:
        log("WARN", "skipped " + str(existscounter) + " already-crawled pastes")
    return (newcounter, hitcounter)


banner(["pastebincomArchive", "archive scrape - polls https://pastebin.com/archive",
        str(len(searchTerms)) + " search terms loaded · email:password detection always on"])

while 1:
    divider("archive pass " + str(iterator))
    log("INFO", "archiving raw_pastes if the fetch threshold is reached")
    tools.archivepastes("data/raw_pastes")
    iterator += 1
    try:
        response = session.get("https://pastebin.com/archive", headers=headers, timeout=5)
        response = response.text
        time.sleep(5)
        new, hits = getjuicystuff(response)
        panel("pass " + str(iterator - 1),
               "crawled " + str(new) + " new paste(s), found " + str(hits) + " hit(s)",
               "sleeping 300s before the next pass")
        time.sleep(300)
    except Exception as e:
        log("ERROR", "critical error - retrying in 300s: " + str(e))
        time.sleep(300)
        continue