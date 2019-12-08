import argparse
import os
import classes.utility
from datetime import datetime
from datetime import timedelta
#import matplotlib.pyplot as plt

tools = classes.utility.ScavUtility()

descr = """
  _________                                                      
 /   _____/ ____ _____ ___  __ ____   ____    ____   ___________ 
 \_____  \_/ ___\\\\__  \\\\  \/ // __ \ /    \  / ___\_/ __ \_  __ \\
 /        \  \___ / __ \\\\   /\  ___/|   |  \/ /_/  >  ___/|  | \/
/_______  /\___  >____  /\_/  \___  >___|  /\___  / \___  >__|   
        \/     \/     \/          \/     \//_____/      \/       
"""
print(descr)
parser = argparse.ArgumentParser(description="Control software for the different modules of this paste crawler.")
parser.add_argument("-0", "--pastebinCOMapi", help="Activate Pastebin.com module (using API)", action="store_true")
parser.add_argument("-1", "--pastebinCOMtor", help="Activate Pastebin.com module (standard scraping using TOR to avoid IP blocking)", action="store_true")
parser.add_argument("-2", "--pasteORG", help="Activate Paste.org module", action="store_true")
#parser.add_argument("-ps", "--pStatistic", help="Show a simple statistic.", action="store_true")
args = parser.parse_args()

if args.pastebinCOMapi:
    print("Pastebin.com (API mode): starting crawler in new tmux session...")
    os.system("tmux new -d -s pastebincomCrawlerAPI 'python3 P_bot.py'")
if args.pastebinCOMtor:
    print("Pastebin.com (Scraping mode): starting crawler in new tmux session...")
    os.system("tmux new -d -s pastebincomCrawlerTOR 'python3 P_bot_TOR.py'")
if args.pasteORG:
    print("Paste.org: starting crawler in new tmux session...")
    os.system("tmux new -d -s pasteorgCrawler 'python3 pasteorg.py'")
#if args.pStatistic:
#    print("Generating a simple statistic...")
#    statisticvalues = tools.statisticscountpoints()
#    #linelist = []
#    #xlabellist = []
#    #xlabellistText = []
#    for value in statisticvalues:
#        print(str(value[0]) + ": " + str(value[1]) + " breaches")
#        #linelist.append(value[1])
#        #xlabellist.append(value[0])
#        day = datetime.utcfromtimestamp(value[0]).strftime('%Y-%m-%d')
#        day = datetime.strptime(day, '%Y-%m-%d').date()
#        day += timedelta(days=1)
#        #xlabellistText.append(day)
#    #print("Generating image...")

#    #plt.xticks(xlabellist, xlabellistText)
#    #plt.bar(xlabellist, linelist, width=86000, align="center")
#    #plt.grid(True)
#    #plt.title("DETECTED LEAKS PER DAY")
#    #plt.ylabel("NUMBER OF LEAKS")
#    #plt.show()
