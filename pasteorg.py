#!/usr/bin/python

import httplib2
import time
import classes.utility

http = httplib2.Http(disable_ssl_certificate_validation=True)
tools = classes.utility.ScavUtility()

while True:
    # test if ready to archive
    archivepath = "data/raw_pastes_pasteorg"
    archiveit = tools.testifreadytoarchive(archivepath)
    if archiveit == 1:
        print("[*] Get all the pastes with credentials...")
        tools.getthejuicythings(archivepath, "pasteorg")
        print("[*] Archiving old Paste.org pastes...")
        tools.archivepastes(archivepath, "pasteorg")

    status, response = http.request('https://www.paste.org/p/random/paste', headers={'user-agent': 'Mozilla 4.0'})

    link = status['content-location'].split("paste.org")
    print("[*] Crawling " + link[1])
    pastestatus, pasteresponse = http.request("https://www.paste.org/flat" + link[1], headers={'user-agent': 'Mozilla 4.0'})
    if pastestatus['status'] == "200":
        file_ = open('data/raw_pastes_pasteorg' + link[1], 'w')
        file_.write(str(pasteresponse))
        file_.close()
    else:
       print("[-] Paste not reachable (Status code: " + str(pastestatus['status']) + ").")

    time.sleep(2)
