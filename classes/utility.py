#!/usr/bin/python

import time
import re
import os


class ScavUtility:
    def __init__(self):
        pass

    def check(self, email):
        regex = '^(?=.{1,64}@)[A-Za-z0-9_-]+(\\.[A-Za-z0-9_-]+)*@[^-][A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$'
        if (re.search(regex, email)):
            return 1
        else:
            return 0

    def loadSearchTerms(self):
        searchterms = set()
        f = open("configs/searchterms.txt", "r")
        tmpcontent = f.readlines()
        f.close()

        for tmpline in tmpcontent:
            tmpline = tmpline.strip()
            searchterms.add(tmpline)
        return searchterms

    def archivepastes(self, directory):
        pastecount = len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])
        if pastecount > 48000:
            archivefilename = str(time.time()) + ".zip"
            os.system("zip -r pastebin_" + archivefilename + " " + directory)
            os.system("mv pastebin_" + archivefilename + " archive/.")
            os.system("rm " + directory + "/*")
