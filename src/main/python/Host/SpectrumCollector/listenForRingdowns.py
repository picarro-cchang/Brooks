from Host.autogen import interface
from Host.Common import Listener
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RDRESULTS
import Queue

def Log(msg):
    print msg

rdQueue = Queue.Queue()
listener = Listener.Listener(rdQueue, BROADCAST_PORT_RD_RECALC, interface.ProcessedRingdownEntryType,
                                            retry = True,
                                            name = "Spectrum collector listener",logFunc = Log)
while True:
    print rdQueue.get()
