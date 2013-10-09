import os
import re
import fnmatch
import sys
import subprocess

src = r"c:\temp\Templates"
patts = ["*.py"]
regex1 = re.compile('print(?!\s*>>)(?!\S)')

for base, dirs, files in os.walk(src):
    for fname in files:
        for patt in patts:
            if fnmatch.fnmatch(fname,patt):
                with file(os.path.join(base, fname),'r') as fp:
                    for line in fp:
                        where = regex1.search(line)
                        if where:
                            print "%s: %s" % (fname,line)
                break
