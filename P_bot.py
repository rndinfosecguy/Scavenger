#!/usr/bin/python

######
# Code needs to be reworked to make use of built classes
######
# If you do not want to post results on Twitter remove the lines marked with TWITTER
######

import time
import tweepy
import os
import httplib2
import sys
import classes.utility
from bs4 import BeautifulSoup, SoupStrainer

tools = classes.utility.ScavUtility()
iterator = 1

# Twitter API credentials
consumer_key = ""  # TWITTER
consumer_secret = ""  # TWITTER
access_key = ""  # TWITTER
access_secret = ""  # TWITTER

# authorize twitter, initialize Tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)  # TWITTER
auth.set_access_token(access_key, access_secret)  # TWITTER
api = tweepy.API(auth)  # TWITTER

if sys.argv[1] == "api":
	print "[#] Using API to gather pastes."
else:
	print "[#] Using website scraping to gather pastes."

while 1:
	# check if enough files are in raw_pastes
	DIR = "data/raw_pastes"
	pasteCount = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
	# if number of pastes > 48.000 save them to the archive and execute filter script
	if pasteCount > 48000:
		print "*** Processing Raw Pastes ***"
		print "[+] Filter for passwords"
		os.system("python filter.py")
		print "[+] Zip raw pastes and copy them to archive"
		archiveFileName = str(time.time()) + ".zip"
		os.system("zip -r " + archiveFileName + " " + DIR)
		os.system("mv " + archiveFileName + " archive/.")
		print "[+] Removing raw pastes"
		os.system("rm " + DIR + "/*")
		
	print str(iterator) + ". iterator:"
	iterator += 1
	http = httplib2.Http()
	try:
		status, response = http.request('http://pastebin.com/archive')
		time.sleep(90)
		print "[#] Waiting..."

		for link in BeautifulSoup(response, parseOnlyThese=SoupStrainer('a')):
			if "HTML" not in link:
				if link.has_attr('href'):
					if len(link['href']) == 9 and link['href'][0] == '/' and link['href'] != '/messages' and link['href'] != '/settings' and link['href'] != '/scraping':
						print "[*] Crawling " + link['href']
						if sys.argv[1] != "api":
							binStatus, binResponse = http.request('http://pastebin.com/raw' + link['href'])
						else:
							# Use Pastebin.com API. Remember to whitelist your IP in your pastebin PRO account
							# This change was implemented because it seems that Pastebin.com recently changed their IP block policy when you simply scrape their site
							scrapingID = link['href'].replace("/", "")
							binStatus, binResponse = http.request('http://scrape.pastebin.com/api_scrape_item.php?i=' + scrapingID)
						try:
							foundPasswords = 0

							file_ = open('data/raw_pastes' + link['href'], 'w')
							file_.write(binResponse)
							file_.close()
						
							emailPattern = os.popen("grep -l -E -o \"\\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z0-9.-]+\\b\" data/raw_pastes/" + link['href']).read()
							emailPattern = emailPattern.split("\n")
							for file in emailPattern:
								if file != "":
									with open("data/raw_pastes/" + link['href']) as f:
										pasteContent = f.readlines()
									skip = 0
									for line in pasteContent:
										curLine = line.strip()
										if (":" in curLine or ";" in curLine or "," in curLine) and "://" not in curLine and len(curLine) <=100 and "android:" not in curLine and "#EXTINF" not in curLine:
											pass
										else:
											skip = 1
									if skip == 0:
										foundPasswords = 1

							curPasteMySQLi = os.popen("grep mysqli_connect\( data/raw_pastes/" + link['href']).read()
							curPasteRSA = os.popen("grep 'BEGIN RSA PRIVATE KEY' data/raw_pastes/" + link['href']).read()
							curPasteWP = os.popen("grep 'The name of the database for WordPress' data/raw_pastes/" + link['href']).read()

							# search for onion links
							containsOnion = 0
							containsDocument = 0
							with open("data/raw_pastes/" + link['href']) as f:
								onionContent = f.readlines()
							for line in onionContent:
								if ".onion" in line and len(line) <= 150:
									containsOnion = 1
									if ".pdf" in line or ".doc" in line or ".docx" in line or ".xls" in line or ".xlsx" in line:
										containsDocument = 1

							if foundPasswords == 1:
								foundPasswords = 0
								print "Found credentials. Posting on Twitter..."
								api.update_status("")  # TWITTER
								tools.statisticsaddpoint()
							elif curPasteRSA != "":
								print "Found RSA key. Posting on Twitter..."
								api.update_status("")  # TWITTER
								tools.statisticsaddpoint()
								os.system("cp data/raw_pastes/" + link['href'] + " data/rsa_leaks/.")
							elif curPasteWP != "":
								print "Found Wordpress configuration file. Posting on Twitter..."
								api.update_status("")  # TWITTER
								tools.statisticsaddpoint()
								os.system("cp data/raw_pastes/" + link['href'] + " data/wordpress_leaks/.")
							elif curPasteMySQLi != "":
								print "Found MySQL connect string. Posting on Twitter..."
								api.update_status("")  # TWITTER
								tools.statisticsaddpoint()
								os.system("cp data/raw_pastes/" + link['href'] + " data/mysql_leaks/.")
							elif containsOnion == 1:
								if containsDocument == 1:
									print "Found .onion link to a document. Posting on Twitter..."
									api.update_status("")  # TWITTER
									tools.statisticsaddpoint()
									os.system("cp data/raw_pastes/" + link['href'] + " data/onion_docs/.")
								else:
									print "Found .onion link. Posting on Twitter..."
									api.update_status("")  # TWITTER
									tools.statisticsaddpoint()
									os.system("cp data/raw_pastes/" + link['href'] + " data/onion/.")

							time.sleep(1)
						except:
							print "[-] File error!"
							continue

		print "++++++++++"
		print ""
	except:
		print "[-] Connection error!"
		continue
