#!/usr/bin/python

import os

emailPattern = os.popen("find data/raw_pastes -type f -print | xargs grep -l -E -o \"\\b[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z0-9.-]+\\b:\"").read()
emailPattern = emailPattern.split("\n")
for file in emailPattern:
	if file != "":
		os.system("cp " + file + " data/files_with_passwords/.")
