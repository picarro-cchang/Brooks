import sys
import time

if len(sys.argv) > 1:
    delay = float(sys.argv[1])
for i in range(10000):
    print "This is line %d" % i
    time.sleep(delay)
