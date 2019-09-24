######
# If you do not want to post results on Twitter remove the lines marked with TWITTER
######

import time
import tweepy
import os
import httplib2
import classes.utility
import json

tools = classes.utility.ScavUtility()
iterator = 1

#Twitter API credentials
consumer_key = ""  # TWITTER
consumer_secret = ""  # TWITTER
access_key = ""  # TWITTER
access_secret = ""  # TWITTER

#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)  # TWITTER
auth.set_access_token(access_key, access_secret)  # TWITTER
api = tweepy.API(auth)  # TWITTER

print("[#] Using API to gather pastes.")

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
	http = httplib2.Http()
	try:
		status, response = http.request("https://scrape.pastebin.com/api_scraping.php")
		result =  json.loads(response.decode('utf-8'))
		print("[#] Waiting...")
		time.sleep(90)

		for apiPaste in result:
			print("[*] Crawling " + apiPaste["key"])
			binStatus, binResponse = http.request(apiPaste["scrape_url"])
			try:
				foundPasswords = 0

				file_ = open("data/raw_pastes/" + apiPaste["key"], "wb")
				file_.write(binResponse)
				file_.close()

				emailPattern = os.popen("grep -l -E -o \"\\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z0-9.-]+\\b\" data/raw_pastes/" + apiPaste["key"]).read()
				emailPattern = emailPattern.split("\n")
				for file in emailPattern:
					if file != "":
						with open("data/raw_pastes/" + apiPaste["key"]) as f:
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

				curPasteMySQLi = os.popen("grep mysqli_connect\( data/raw_pastes/" + apiPaste["key"]).read()
				curPasteRSA = os.popen("grep 'BEGIN RSA PRIVATE KEY' data/raw_pastes/" + apiPaste["key"]).read()
				curPasteWP = os.popen("grep 'The name of the database for WordPress' data/raw_pastes/" + apiPaste["key"]).read()

				# search for onion links
				containsOnion = 0
				containsDocument = 0
				with open("data/raw_pastes/" + apiPaste["key"]) as f:
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
					os.system("cp data/raw_pastes/" + apiPaste["key"] + " data/rsa_leaks/.")
				elif curPasteWP != "":
					print("Found Wordpress configuration file. Posting on Twitter...")
					api.update_status()  # TWITTER
					tools.statisticsaddpoint()
					os.system("cp data/raw_pastes/" + apiPaste["key"] + " data/wordpress_leaks/.")
				elif curPasteMySQLi != "":
					print("Found MySQL connect string. Posting on Twitter...")
					api.update_status()  # TWITTER
					tools.statisticsaddpoint()
					os.system("cp data/raw_pastes/" + apiPaste["key"] + " data/mysql_leaks/.")
				elif containsOnion == 1:
					if containsDocument == 1:
						print("Found .onion link to a document. Posting on Twitter...")
						api.update_status()  # TWITTER
						tools.statisticsaddpoint()
						os.system("cp data/raw_pastes/" + apiPaste["key"] + " data/onion_docs/.")
					else:
						print("Found .onion link. Posting on Twitter...")
						api.update_status()  # TWITTER
						tools.statisticsaddpoint()
						os.system("cp data/raw_pastes/" + apiPaste["key"] + " data/onion/.")

				time.sleep(1)
			except Exception as e:
				print(e)
				continue

		print("++++++++++")
		print("")
	except Exception as e:
		print(e)
		continue
