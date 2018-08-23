from __future__ import with_statement
import os
import re
import fnmatch
#import sys
#import subprocess

src = r"c:\temp\Templates"
#src = r"C:\Users\twalder\Documents\Testing\TemplateResults"

patts = ["analyze*.py", "parse*.py", "processor*.py", "fit*.py", "update_cal*.py", "Propo*.py",
         "*analyze*.py", "resync*.py", "slow_display.py", "noiseReduction.py"]
regex1 = re.compile('print(?!\s*>>)(?!\S)')

for base, dirs, files in os.walk(src):
    for fname in files:
        for patt in patts:
            if fnmatch.fnmatch(fname, patt):
                print os.path.join(base, fname)
                output = []

                with file(os.path.join(base, fname), 'r') as fp:
                    for line in fp:
                        where = regex1.search(line)
                        if where:
                            output.append(regex1.sub('pass###', line))
                        else:
                            output.append(line)

                with file(os.path.join(base, fname), 'w') as fp:
                    fp.write("".join(output))
                break