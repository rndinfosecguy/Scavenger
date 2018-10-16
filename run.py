#!/usr/bin/python

import argparse
import os

descr = """
  _________                                                      
 /   _____/ ____ _____ ___  __ ____   ____    ____   ___________ 
 \_____  \_/ ___\\\\__  \\\\  \/ // __ \ /    \  / ___\_/ __ \_  __ \\
 /        \  \___ / __ \\\\   /\  ___/|   |  \/ /_/  >  ___/|  | \/
/_______  /\___  >____  /\_/  \___  >___|  /\___  / \___  >__|   
        \/     \/     \/          \/     \//_____/      \/       
"""
print descr
parser = argparse.ArgumentParser(description="Control software for the different modules of this paste crawler.")
parser.add_argument("-0", "--pastebinCOM", help="Activate Pastebin.com module", action="store_true")
parser.add_argument("-1", "--pasteORG", help="Activate Paste.org module (not yet implemented)", action="store_true")
args = parser.parse_args()

if args.pastebinCOM:
    print "Pastebin.com: starting crawler in new tmux session..."
    os.system("tmux new -d -s pastebinCrawler 'P_bot.py'")
if args.pasteORG:
    print "Paste.org: not yet implemented."
