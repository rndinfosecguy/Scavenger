#!/usr/bin/python

import os
import sys

result = os.popen("find data/raw_pastes -type f -print | xargs grep -E \"" + sys.argv[1] + "\"").read()
print result
