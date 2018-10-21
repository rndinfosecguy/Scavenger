#!/usr/bin/python

import time
import os

class ScavUtility:
    def __init__(self):
        pass

    def testifreadytoarchive(self, directory):
        pastecount = len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])
        if pastecount > 48000:
            return 1
        else:
            return 0

    def archivepastes(self, dir, site):
        archivefilename = str(time.time()) + ".zip"
        os.system("zip -r " + site + "_" + archivefilename + " " + dir)
        os.system("mv " + site + "_" + archivefilename + " archive/.")
        os.system("rm " + dir + "/*")

    def getthejuicythings(self, pastefolder, site):
        emailPattern = os.popen("find " + pastefolder + " -type f -print | xargs grep -l -E -o \"\\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z0-9.-]+\\b:\"").read()
        emailPattern = emailPattern.split("\n")
        print emailPattern
        for file in emailPattern:
            if file != "":
                fname = file.split("/")
                fname = fname[len(fname)-1]
                os.system("cp " + file + " data/files_with_passwords/" + fname + "_" + site)

