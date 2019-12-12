######
# If you do not want to post results on Twitter remove the lines marked with TWITTER
######

import time
import tweepy
import os
import classes.utility
import requests
from bs4 import BeautifulSoup, SoupStrainer

tools = classes.utility.ScavUtility()
iterator = 1
session = requests.session()
session.proxies = {}
session.proxies["http"] = "socks5h://localhost:9050"
session.proxies["https"] = "socks5h://localhost:9050"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"}

#Twitter API credentials
consumer_key = ""  # TWITTER
consumer_secret = ""  # TWITTER
access_key = ""  # TWITTER
access_secret = ""  # TWITTER

#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)  # TWITTER
auth.set_access_token(access_key, access_secret)  # TWITTER
api = tweepy.API(auth)  # TWITTER

print("[#] Using website scraping to gather pastes. (TOR cycles to avoid IP blocking)")

# loading notification targets
with open("notification_targets.txt") as f:
	notificationtargets = f.readlines()
print("[#] Loaded " + str(len(notificationtargets)) + " notification targets.")

while 1:
	# test if ready to archive
	archivepath = "data/raw_pastes"
	archiveit = tools.testifreadytoarchive(archivepath)
	if archiveit == 1:
		print("[*] Get all the pastes with credentials...")
		tools.getthejuicythings(archivepath, "pastebincom")
		print("[*] Archiving old Paste.org pastes...")
		tools.archivepastes(archivepath, "pastebincom")

	print(str(iterator) + ". iterator:")
	iterator += 1
	try:
		response = session.get("https://pastebin.com/archive", headers=headers)
		response = response.text
		print("[#] Waiting...")
		time.sleep(90)

		for link in BeautifulSoup(response, parse_only=SoupStrainer('a'), features="lxml"):
			if "HTML" not in link:
				if link.has_attr('href'):
					if len(link["href"]) == 9 and link["href"][0] == "/" and link["href"] != "/messages" and link["href"] != "/settings" and link["href"] != "/scraping":
						print("[*] Crawling " + link["href"])
						# I implemented a little fix which currently avoids that your IP gets blocked when simply scraping the website without using the API
						binResponse = session.get("https://pastebin.com/raw" + link["href"], headers=headers)
						binResponse = binResponse.text
						try:
							foundPasswords = 0

							file_ = open("data/raw_pastes" + link["href"], "wb")
							file_.write(binResponse.encode('utf-8').strip())
							file_.close()

							emailPattern = os.popen("grep -l -E -o \"\\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z0-9.-]+\\b\" data/raw_pastes" + link["href"]).read()
							emailPattern = emailPattern.split("\n")
							for file in emailPattern:
								if file != "":
									with open("data/raw_pastes" + link["href"]) as f:
										pasteContent = f.readlines()
									skip = 0
									for line in pasteContent:
										curLine = line.strip()
										if (":" in curLine or ";" in curLine or "," in curLine) and "://" not in curLine and len(curLine) <=100 and "android:" not in curLine and "#EXTINF" not in curLine:
											tools.checknotificationtargets(notificationtargets, curLine, apiPaste["key"])
										else:
											skip = 1
									if skip == 0:
										foundPasswords = 1

							curPasteMySQLi = os.popen("grep mysqli_connect\( data/raw_pastes" + link["href"]).read()
							curPasteRSA = os.popen("grep 'BEGIN RSA PRIVATE KEY' data/raw_pastes" + link["href"]).read()
							curPasteWP = os.popen("grep 'The name of the database for WordPress' data/raw_pastes" + link["href"]).read()

							# search for onion links
							containsOnion = 0
							containsDocument = 0
							with open("data/raw_pastes" + link["href"]) as f:
								onionContent = f.readlines()
							for line in onionContent:
								if ".onion" in line and len(line) <= 150:
									containsOnion = 1
									if ".pdf" in line or ".doc" in line or ".docx" in line or ".xls" in line or ".xlsx" in line:
										containsDocument = 1

							if foundPasswords == 1:
								foundPasswords = 0
								print("Found credentials. Posting on Twitter...")
								api.update_status()  # TWITTER
								tools.statisticsaddpoint()
							elif curPasteRSA != "":
								print("Found RSA key. Posting on Twitter...")
								api.update_status()  # TWITTER
								tools.statisticsaddpoint()
								os.system("cp data/raw_pastes" + link["href"] + " data/rsa_leaks/.")
							elif curPasteWP != "":
								print("Found Wordpress configuration file. Posting on Twitter...")
								api.update_status()  # TWITTER
								tools.statisticsaddpoint()
								os.system("cp data/raw_pastes" + link["href"] + " data/wordpress_leaks/.")
							elif curPasteMySQLi != "":
								print("Found MySQL connect string. Posting on Twitter...")
								api.update_status()  # TWITTER
								tools.statisticsaddpoint()
								os.system("cp data/raw_pastes" + link["href"] + " data/mysql_leaks/.")
							elif containsOnion == 1:
								if containsDocument == 1:
									print("Found .onion link to a document. Posting on Twitter...")
									api.update_status()  # TWITTER
									tools.statisticsaddpoint()
									os.system("cp data/raw_pastes" + link["href"] + " data/onion_docs/.")
								else:
									print("Found .onion link. Posting on Twitter...")
									api.update_status()  # TWITTER
									tools.statisticsaddpoint()
									os.system("cp data/raw_pastes" + link["href"] + " data/onion/.")

							time.sleep(1)
						except Exception as e:
							print(e)
							continue

		print("++++++++++")
		print("")
	except Exception as e:
		print(e)
		continue
