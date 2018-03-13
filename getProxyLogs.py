#!/usr/bin/python

import os
import sys
import argparse

parser = argparse.ArgumentParser(description="Get all URLs with username and password combinations.")
parser.add_argument("folder", metavar="FOLDER", help='folder to search in')

args = parser.parse_args()

files = os.listdir(args.folder)
combinations = set()
count = 1

for fi in files:
	with open(sys.argv[1] + fi) as f:
		content = f.readlines()
	for line in content:
		if ("http://" in line or "https://" in line) and "password=" in line and "<" not in line and ">" not in line and "[" not in line and "]" not in line and "#EXT" not in line and " " not in line:
			combinations.add(line.strip())

for comb in combinations:
	print str(count) + ".) " + comb
	count += 1
