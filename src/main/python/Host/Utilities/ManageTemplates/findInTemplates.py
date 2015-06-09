from __future__ import with_statement
import os
import re
import fnmatch
#import sys
#import subprocess

#src = r"C:\Users\twalder\Documents\Testing\TemplateResults"
src = r"c:\temp\Templates"

patts = ["*.py"]


regex1 = re.compile('print(?!\s*>>)(?!\S)')

# same as above but ignores leading whitespace so does not pick up words with 'print' embedded
# such as 'imprint'
regex2 = re.compile('^\s*print(?!\s*>>)(?!\S)')

cFound = 0
cFoundFalsePositive = 0
cFoundNonWhitespace = 0

for base, dirs, files in os.walk(src):
    for fname in files:
        for patt in patts:
            if fnmatch.fnmatch(fname, patt):
                with file(os.path.join(base, fname), 'r') as fp:
                    fSearchPrinted = False
                    linenum = 0

                    for line in fp:
                        where = regex1.search(line)
                        where2 = regex2.search(line)
                        linenum += 1

                        # Print full path of file searched only if there was a hit
                        # and haven't printed it out yet
                        if where or where2:
                            if not fSearchPrinted:
                                fSearchPrinted = True
                                print ""
                                print "Searching '%s'" % os.path.join(base, fname)

                        if where2 and not where:
                            print "  FALSE POSITIVE! Could mean trouble..."
                            cFoundFalsePositive += 1
                        elif not where2 and where:
                            print "  NON-WHITESPACE before search text! most likely a comment..."
                            cFoundNonWhitespace += 1

                        if where or where2:
                            #print "  %s: Line %d: %s" % (fname, linenum, line)
                            print "  Line %d: %s" % (linenum, line)
                            cFound += 1
                break

print ""
print ""
print "Found %d matches in all, including leading non-whitespace" % cFound
print "Found %d with leading non-whitespace" % cFoundNonWhitespace
print "Found %d false positives" % cFoundFalsePositive
print ""