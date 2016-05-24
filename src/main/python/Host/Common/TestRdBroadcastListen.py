import Host.Common.Listener as Listener
import Host.Common.StringPickler as StringPickler
import time
import sys
from Host.autogen.interface import ProcessedRingdownEntryType

def MyFilter(Obj):
    print "Freq = %s, Loss = %s" % (Obj.frequency,Obj.uncorrectedAbsorbance)

try:
    listenPort = int(sys.argv[1])
except IndexError:
    listenPort = 40031

l = Listener.Listener(None, listenPort, ProcessedRingdownEntryType, MyFilter, retry = True)

print "Listening on port %d..." % listenPort

while 1:
    time.sleep(1)
    pass