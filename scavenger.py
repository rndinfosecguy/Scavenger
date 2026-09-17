import argparse
import os
import sys

from classes.utility import log, panel

panel("Scavenger 2.0",
      "pastebin credential-leak crawler",
      "",
      "  -0  archive scrape module",
      "  -1  user track module",
      "  -2  edit search terms",
      "  -3  edit tracked users",
      "",
      "python3 scavenger.py -0 -1  (combine flags)",
      width=52)

parser = argparse.ArgumentParser(description="control script",
                                 epilog="example usage: python3 " + sys.argv[0] + " -0 -1")
parser.add_argument("-0", "--pbincom",
                    help="Activate pastebin.com archive scraping module",
                    action="store_true")
parser.add_argument("-1", "--pbincomTrack",
                    help="Activate pastebin.com user track module",
                    action="store_true")
parser.add_argument("-2", "--editsearch",
                     help="Edit search terms file for additional search terms (email:password combinations will always be searched)",
                     action="store_true")
parser.add_argument("-3", "--editusers", help="Edit user file of the pastebin.com user track module",
                    action="store_true")
args = parser.parse_args()

if args.pbincom:
    log("OK", "starting archive crawler in detached tmux session `pastebincomArchive`")
    os.system("tmux new -d -s pastebincomArchive 'python3 pbincomArchiveScrape.py'")

if args.pbincomTrack:
    log("OK", "starting user-track crawler in detached tmux session `pastebincomTrack`")
    os.system("tmux new -d -s pastebincomTrack 'python3 pbincomTrackUser.py'")

if args.editsearch:
    if not (args.pbincomTrack or args.pbincom or args.editusers):
        os.system("vi configs/searchterms.txt")
        log("WARN", "search terms changed - restart the affected module")
    else:
        log("ERROR", "-2/--editsearch cannot be used with other arguments")

if args.editusers:
    if not (args.pbincomTrack or args.pbincom or args.editsearch):
        os.system("vi configs/users.txt")
        log("WARN", "tracked users changed - restart the affected module")
    else:
        log("ERROR", "-3/--editusers cannot be used with other arguments")