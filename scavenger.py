import argparse
import os
import sys

from classes.utility import log, panel

panel("Scavenger 3.0",
      "multi-source credential-leak crawler",
      "",
      "  -0  pastebin archive scrape module",
      "  -1  pastebin user track module",
      "  -2  pastes.io random-ID scraper",
      "  -3  GitHub gist scraper",
      "  -4  edit search terms",
      "  -5  edit tracked users",
      "  -6  dashboard",
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
parser.add_argument("-2", "--pastesio",
                    help="Activate pastes.io random-ID scraper",
                    action="store_true")
parser.add_argument("-3", "--githubgist",
                    help="Activate GitHub gist scraper",
                    action="store_true")
parser.add_argument("-4", "--editsearch",
                     help="Edit search terms file for additional search terms (email:password combinations will always be searched)",
                     action="store_true")
parser.add_argument("-5", "--editusers", help="Edit user file of the pastebin.com user track module",
                    action="store_true")
parser.add_argument("-6", "--dashboard", help="Start the web dashboard",
                    action="store_true")
args = parser.parse_args()

if args.pbincom:
    log("OK", "starting archive crawler in detached tmux session `pastebincomArchive`")
    os.system("tmux new -d -s pastebincomArchive 'python3 pbincomArchiveScrape.py'")

if args.pbincomTrack:
    log("OK", "starting user-track crawler in detached tmux session `pastebincomTrack`")
    os.system("tmux new -d -s pastebincomTrack 'python3 pbincomTrackUser.py'")

if args.pastesio:
    log("OK", "starting pastes.io scraper in detached tmux session `pastesioScrape`")
    os.system("tmux new -d -s pastesioScrape 'python3 pbincomIOscrape.py'")

if args.githubgist:
    log("OK", "starting GitHub gist scraper in detached tmux session `githubgistScrape`")
    os.system("tmux new -d -s githubgistScrape 'python3 gbingistscrape.py'")

if args.dashboard:
    log("OK", "starting dashboard in detached tmux session `scavengerDashboard`")
    os.system("tmux new -d -s scavengerDashboard 'python3 dashboard.py'")

if args.editsearch:
    if not (args.pbincomTrack or args.pbincom or args.pastesio or args.githubgist or args.dashboard or args.editusers):
        os.system("vi configs/searchterms.txt")
        log("WARN", "search terms changed - restart the affected module")
    else:
        log("ERROR", "-4/--editsearch cannot be used with other arguments")

if args.editusers:
    if not (args.pbincomTrack or args.pbincom or args.pastesio or args.githubgist or args.dashboard or args.editsearch):
        os.system("vi configs/users.txt")
        log("WARN", "tracked users changed - restart the affected module")
    else:
        log("ERROR", "-5/--editusers cannot be used with other arguments")