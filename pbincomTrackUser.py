import os
import datetime
from bs4 import BeautifulSoup, SoupStrainer
import requests
import time
import classes.utility
from colorama import Fore, Style

tools = classes.utility.ScavUtility()
session = requests.session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"}
searchTerms = tools.loadSearchTerms()

iterator = 1
while True:
    print(str(datetime.datetime.now()) + ": [#] Archiving pastes...")
    print()
    tools.archivepastes("data/raw_pastes")

    print(str(datetime.datetime.now()) + ": [#] " + str(iterator) + ". iterator")
    # read all relevant users
    with open("configs/users.txt", "r") as f:
        relevantUsers = f.readlines()

    # go through users and store paste IDs
    for user in relevantUsers:
        try:
            user = user.strip()
            print(str(datetime.datetime.now()) + ": [#] Getting pastes for user " + Fore.GREEN + user + Style.RESET_ALL)
            response = session.get("https://pastebin.com/u/" + user, headers=headers)
            response = response.text

            skipcount = 0
            existsCounter = 0
            for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
                if "HTML" not in link and "html" not in link:
                    if link.has_attr('href'):
                        if len(link["href"]) == 9 and link["href"][0] == "/" and link["href"] != "/messages" and \
                                link["href"] != "/settings" and link["href"] != "/scraping" and "/u/" not in link[
                                "href"]:
                            if skipcount <= 7:
                                skipcount += 1
                                continue
                            # check if paste already scraped
                            crawled = os.popen(
                                'grep -l ' + link['href'].replace("/", "") + ' logs/alreadytrackedpastes.log').read()
                            crawled = crawled.strip()
                            if crawled != '':
                                existsCounter += 1
                                continue

                            # get paste and store it
                            print(Fore.YELLOW + str(datetime.datetime.now()) + ": [*] Crawling " + link[
                                "href"] + Style.RESET_ALL)
                            curPaste = session.get("https://pastebin.com/raw" + link['href'], headers=headers)
                            curPaste = curPaste.text
                            f = open("data/raw_pastes" + link["href"], "w")
                            f.write(str(curPaste))
                            f.close()
                            os.system("echo " + link["href"].replace("/", "") + " >> logs/alreadytrackedpastes.log")

                            # get the juicy stuff
                            foundPassword = 0
                            foundSensitiveData = 0

                            f = open("data/raw_pastes" + link["href"], "r")
                            fiContent = f.readlines()
                            f.close()

                            for line in fiContent:
                                line = line.strip()
                                if "@" in line and ":" in line:
                                    line = line.split(":")
                                    if len(line) == 2:
                                        line[0] = line[0].strip()
                                        line[1] = line[1].strip()
                                        if "@" in line[0]:
                                            if tools.check(line[0]) == 1:
                                                password = line[1].split(" ")[0]
                                                password = password.split("|")[0]
                                                if password == "" or len(password) < 4 or len(password) > 40:
                                                    continue
                                                else:
                                                    foundPassword = 1
                                            else:
                                                continue
                                        else:
                                            continue
                                    else:
                                        continue

                                for searchItem in searchTerms:
                                    if searchItem in line:
                                        foundSensitiveData = 1
                                        sensitiveValue = searchItem

                            if foundPassword == 1:
                                print(Fore.GREEN + str(datetime.datetime.now()) + ": [+] Found credentials. Saving to "
                                                                                  "data/files_with_passwords/" +
                                      Style.RESET_ALL)
                                os.system("cp data/raw_pastes" + link["href"] + " data/files_with_passwords/.")
                            elif foundSensitiveData == 1:
                                print(Fore.GREEN + str(
                                    datetime.datetime.now()) + ": [+] Found other sensitive data. Saving to "
                                                               "data/otherSensitivePastes/" + Style.RESET_ALL)
                                os.system("cp data/raw_pastes" + link[
                                    "href"] + " data/otherSensitivePastes/" + sensitiveValue + "_" + link[
                                              "href"].replace("/", ""))

                            print(str(datetime.datetime.now()) + ": [#] Waiting 20s till next paste scrape...")
                            time.sleep(20)
            print(Fore.RED + str(datetime.datetime.now()) + ": [-] Skipped " + str(
                existsCounter) + " pastes (reason: already crawled)" + Style.RESET_ALL)
            print(str(datetime.datetime.now()) + ": [#] Waiting 10 minutes till next user check... ")
            print()
            time.sleep(600)
        except Exception as e:
            print(Fore.RED + str(e) + Style.RESET_ALL)

    iterator += 1
    print(str(datetime.datetime.now()) + ": [#] Waiting 3 hours till next iteration...")
    print()
    time.sleep(10800)
