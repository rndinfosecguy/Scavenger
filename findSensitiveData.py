import datetime
import os
import sys
from os import listdir
from os.path import isfile, join
import classes.utility
from colorama import Fore, Style, init as coloramainit

raw_paste_folder = sys.argv[1]
rawfiles = [f for f in listdir(raw_paste_folder) if isfile(join(raw_paste_folder, f))]
count = 0
gCount = 0
tools = classes.utility.ScavUtility()
searchTerms = tools.loadSearchTerms()
coloramainit() # Needed to fix win10/11 terminal colors

print(Fore.YELLOW + str(datetime.datetime.now()) + ": [+] Fetched files from " + raw_paste_folder + Style.RESET_ALL)

for file in rawfiles:
    f = open(raw_paste_folder + "/" + file)
    curFileContent = f.readlines()
    f.close()

    foundPassword = 0
    foundSensitiveData = 0
    sensitiveValue = ""

    for line in curFileContent:
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
        print(Fore.GREEN + str(
            datetime.datetime.now()) + ": [+] Found credentials. Saving to data/files_with_passwords/" +
              Style.RESET_ALL)
        os.system("cp " + raw_paste_folder + "/" + file + " data/files_with_passwords/.")
        f = open("logs/findSensitiveData_credentials.log", "a")
        f.write(raw_paste_folder + "/" + file + "\n")
        f.close()
    elif foundSensitiveData == 1:
        print(Fore.GREEN + str(datetime.datetime.now()) + ": [+] Found other sensitive data. Saving to "
                                                          "data/otherSensitivePastes/" + Style.RESET_ALL)
        os.system("cp " + raw_paste_folder + "/" + file + " data/otherSensitivePastes/.")
        f = open("logs/findSensitiveData_othersensitivedata.log", "a")
        f.write(raw_paste_folder + "/" + file + " - matched keyword: " + sensitiveValue + "\n")
        f.close()

    if count == 1000:
        count = 0
        print(
            Fore.YELLOW + str(datetime.datetime.now()) + "[+] Proccessed " + str(gCount) + " pastes." + Style.RESET_ALL)
    count += 1
    gCount += 1
