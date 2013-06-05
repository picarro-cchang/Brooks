# This program renames the directories for the report generation utility to conform
#  with the new style naming

from glob import glob
import os
import shutil

# Find the names of the directories which are hashes
hashes = glob(32*"?")
for d in hashes:
	prefix = d[:2]
	try:
		os.mkdir(prefix)
	except:
		pass
	shutil.move(d,prefix)
	print "Moving: %s to %s" % (d, prefix)
