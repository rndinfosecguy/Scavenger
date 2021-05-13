import argparse
import os
from colorama import Fore, Style
import sys

descr = Fore.YELLOW + """
  _________
 /   _____/ ____ _____ ___  __ ____   ____    ____   ___________
 \_____  \_/ ___\\\\__  \\\\  \/ // __ \ /    \  / ___\_/ __ \_  __ \\
 /        \  \___ / __ \\\\   /\  ___/|   |  \/ /_/  >  ___/|  | \/
/_______  /\___  >____  /\_/  \___  >___|  /\___  / \___  >__|
        \/     \/     \/          \/     \//_____/      \/       Reworked
""" + Style.RESET_ALL
print(descr)
parser = argparse.ArgumentParser(description="control script",
                                 epilog="example usage: python3 " + sys.argv[0] + " -0 -1")
parser.add_argument("-0", "--pbincom",
                    help="Activate " + Fore.GREEN + "pastebin.com  archive  scraping " + Style.RESET_ALL + "module",
                    action="store_true")
parser.add_argument("-1", "--pbincomTrack",
                    help="Activate " + Fore.GREEN + "pastebin.com user track " + Style.RESET_ALL + "module",
                    action="store_true")
parser.add_argument("-2", "--sensitivedata", help="Search a specific folder for sensitive data. This might be useful "
                                                  "if you want to analyze some pastes which were not collected by the "
                                                  "bot.", action="store_true")
parser.add_argument("-3", "--editsearch",
                    help="Edit search terms file for additional search terms (email:password combinations will always be searched)",
                    action="store_true")
parser.add_argument("-4", "--editusers", help="Edit user file of the pastebin.com user track module",
                    action="store_true")
args = parser.parse_args()

if args.pbincom:
    print(
        Fore.GREEN + "[+] pastebin.com archive scraper: starting crawler in new tmux session named " + Fore.YELLOW +
        "pastebincomArchive" + Fore.GREEN + "..." + Style.RESET_ALL)
    os.system("tmux new -d -s pastebincomArchive 'python3 pbincomArchiveScrape.py'")

if args.pbincomTrack:
    print(
        Fore.GREEN + "[+] pastebin.com user track module: starting crawler in new tmux session named " + Fore.YELLOW
        + "pastebincomTrack" + Fore.GREEN + "..." + Style.RESET_ALL)
    os.system("tmux new -d -s pastebincomTrack 'python3 pbincomTrackUser.py'")

if args.editsearch:
    if not args.pbincomTrack and not args.pbincom and not args.editusers:
        os.system("vi configs/searchterms.txt")
        print("[#] If you changed anything, do not forget to restart the affected module!")
    else:
        print(Fore.RED + "[-] -3/--editsearch cannot be used with other arguments" + Style.RESET_ALL)

if args.editusers:
    if not args.pbincomTrack and not args.pbincom and not args.editsearch:
        os.system("vi configs/users.txt")
        print("[#] If you changed anything, do not forget to restart the affected module!")
    else:
        print(Fore.RED + "[-] -4/--editusers cannot be used with other arguments" + Style.RESET_ALL)

if args.sensitivedata:
    print(Fore.BLUE + "[*] Insert full path of the folder you want scan: ")
    folder = input()
    print(Style.RESET_ALL)
    os.system("python3 findSensitiveData.py " + folder)

print()
