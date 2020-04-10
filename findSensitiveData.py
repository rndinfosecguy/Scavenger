import os
import sys
from os import listdir
from os.path import isfile, join

raw_paste_folder =  sys.argv[1]

rawfiles = [f for f in listdir(raw_paste_folder) if isfile(join(raw_paste_folder, f))]
print("[+] Fetched files from " + raw_paste_folder)

count = 0
gCount = 0

for file in rawfiles:
	curPaste = os.popen("grep '\(^\|[^0-9]\)\{1\}\([345]\{1\}[0-9]\{3\}\|6011\)\{1\}[-]\?[0-9]\{4\}[-]\?[0-9]\{2\}[-]\?[0-9]\{2\}-\?[0-9]\{1,4\}\($\|[^0-9]\)\{1\}' " + raw_paste_folder + file).read()
	curPasteMysqli = os.popen("grep -i mysqli_connect\( " + raw_paste_folder + file).read()
	curPasteRSA = os.popen("grep -i 'BEGIN RSA PRIVATE KEY' " + raw_paste_folder + file).read()
	curPasteWP = os.popen("grep -i 'The name of the database for WordPress' " + raw_paste_folder + file).read()
	curPastePasswords = os.popen("grep -l -E -o \"\\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z0-9.-]+\\b:\" " + raw_paste_folder + file).read()

	if curPaste != "" and ("Mastercard" in curPaste or "mastercard" in curPaste or "MASTERCARD" in curPaste or "visa" in curPaste or "Visa" in curPaste or "VISA" in curPaste):
		print("[+] " + file + " seems to contain at least one debitcard number. Writing to file...")
		with open("data/sensitive_scan_results/debitcards.txt", "a") as myfile:
			myfile.write("----------\n")
			myfile.write(file + ":\n")
			myfile.write(curPaste.strip() + "\n")

	if curPasteMysqli != "":
		print("[+] " + file + " seems to contain a mysqli_connect string. Writing to file...")
		with open("data/sensitive_scan_results/mysqliconnect.txt", "a") as myfile:
			myfile.write("----------\n")
			myfile.write(file + ":\n")
			myfile.write(curPasteMysqli.strip() + "\n")

	if curPasteRSA != "":
		print("[+] " + file + " seems to contain a RSA private key. Writing to file...")
		with open("data/sensitive_scan_results/rsa.txt", "a") as myfile:
			myfile.write("----------\n")
			myfile.write(file + ":\n")
			myfile.write(curPasteRSA.strip() + "\n")

	if curPasteWP != "":
		print("[+] " + file + " seems to contain a Wordpress config file. Writing to file...")
		with open("data/sensitive_scan_results/wp.txt", "a") as myfile:
			myfile.write("----------\n")
			myfile.write(file + ":\n")
			myfile.write(curPasteWP.strip() + "\n")

	if curPastePasswords != "":
		print("[+] " + file + " seems to contain credentials. Writing to file...")
		with open("data/sensitive_scan_results/pws.txt", "a") as myfile:
			myfile.write("----------\n")
			myfile.write(file + ":\n")
			myfile.write(curPastePasswords.strip() + "\n")

	if count == 1000:
		count = 0
		print("[+] Proccessed " + str(gCount) + " pastes.")
	count += 1
	gCount += 1

print("")
print("[+] Detected information stored under data/sensitive_scan_results")
