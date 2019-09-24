import os
import sys
import argparse

parser = argparse.ArgumentParser(description="Search all raw pastes for a specific string.")
parser.add_argument("string", metavar="STRING", help='item to search for')

args = parser.parse_args()

result = os.popen("find data/raw_pastes -type f -print | xargs grep -E \"" + args.string + "\"").read()
print(result)
