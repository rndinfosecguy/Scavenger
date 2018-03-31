#!/usr/bin/python

import os
import sys
from os import listdir
from os.path import isfile, join

raw_paste_folder =  sys.argv[1]

rawfiles = [f for f in listdir(raw_paste_folder) if isfile(join(raw_paste_folder, f))]
print "[+] Fetched files from " + raw_paste_folder

count = 0
gCount = 0

for file in rawfiles:
	curPaste = os.popen("grep '\(^\|[^0-9]\)\{1\}\([345]\{1\}[0-9]\{3\}\|6011\)\{1\}[-]\?[0-9]\{4\}[-]\?[0-9]\{2\}[-]\?[0-9]\{2\}-\?[0-9]\{1,4\}\($\|[^0-9]\)\{1\}' " + raw_paste_folder + file).read()
	curPasteMysqli = os.popen("grep mysqli_connect\( " + raw_paste_folder + file).read()
	curPasteRSA = os.popen("grep 'BEGIN RSA PRIVATE KEY' " + raw_paste_folder + file).read()
	curPasteWP = os.popen("grep 'The name of the database for WordPress' " + raw_paste_folder + file).read()

	if curPaste != "" and ("Mastercard" in curPaste or "mastercard" in curPaste or "MASTERCARD" in curPaste or "visa" in curPaste or "Visa" in curPaste or "VISA" in curPaste):
		print "[+] " + file + " seems to contain at least one debitcard number. Writing to file..."
		with open("debitcards.txt", "a") as myfile:
			myfile.write("----------\n")
			myfile.write(file + ":\n")
    			myfile.write(curPaste.strip() + "\n")

	if curPasteMysqli != "":
		print "[+] " + file + " seems to contain a mysqli_connect string. Writing to file..."
                with open("mysqliconnect.txt", "a") as myfile:
			myfile.write("----------\n")
                        myfile.write(file + ":\n")
                        myfile.write(curPasteMysqli.strip() + "\n")

	if curPasteRSA != "":
		print "[+] " + file + " seems to contain a RSA private key. Writing to file..."
                with open("rsa.txt", "a") as myfile:
			myfile.write("----------\n")
                        myfile.write(file + ":\n")
                        myfile.write(curPasteRSA.strip() + "\n")

	if curPasteWP != "":
		print "[+] " + file + " seems to contain a Wordpress config file.. Writing to file..."
                with open("wp.txt", "a") as myfile:
			myfile.write("----------\n")
                        myfile.write(file + ":\n")
                        myfile.write(curPasteWP.strip() + "\n")

	if count == 1000:
		count = 0
		print "[+] Proccessed " + str(gCount) + " pastes."
	count += 1
	gCount += 1
