import Host.Common.Listener as Listener
import Host.Common.StringPickler as StringPickler
import time
import sys
from Host.autogen.interface import RingdownEntryType

def MyFilter(Obj):
    print "Angle = %s, Loss = %s" % (Obj.wlmAngle,Obj.uncorrectedAbsorbance)

try:
    listenPort = int(sys.argv[1])
except IndexError:
    listenPort = 40030

l = Listener.Listener(None, listenPort, RingdownEntryType, MyFilter, retry = True)

print "Listening on port %d..." % listenPort

while 1:
    time.sleep(1)
    pass