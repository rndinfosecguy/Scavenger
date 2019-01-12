#!/usr/bin/python

import argparse
import os
import classes.utility
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt

tools = classes.utility.ScavUtility()

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
parser.add_argument("-1", "--pasteORG", help="Activate Paste.org module", action="store_true")
parser.add_argument("-ps", "--pStatistic", help="Show a simple statistic.", action="store_true")
args = parser.parse_args()

if args.pastebinCOM:
    print "Pastebin.com: starting crawler in new tmux session..."
    os.system("tmux new -d -s pastebincomCrawler './P_bot.py scrape'")
if args.pasteORG:
    print "Paste.org: starting crawler in new tmux session..."
    os.system("tmux new -d -s pasteorgCrawler './pasteorg.py'")
if args.pStatistic:
    print "Generating a simple statistic..."
    statisticvalues = tools.statisticscountpoints()
    linelist = []
    xlabellist = []
    xlabellistText = []
    for value in statisticvalues:
        print str(value[0]) + ": " + str(value[1]) + " breaches"
        linelist.append(value[1])
        xlabellist.append(value[0])
        day = datetime.utcfromtimestamp(value[0]).strftime('%Y-%m-%d')
        day = datetime.strptime(day, '%Y-%m-%d').date()
        day += timedelta(days=1)
        xlabellistText.append(day)
    print "Generating image..."

    plt.xticks(xlabellist, xlabellistText)
    plt.plot(xlabellist, linelist)
    plt.grid(True)
    plt.title("DETECTED LEAKS PER DAY")
    plt.ylabel("NUMBER OF LEAKS")
    plt.show()
