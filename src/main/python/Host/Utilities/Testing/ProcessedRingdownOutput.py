import Queue
import time
from cPickle import dumps
from struct import pack
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common.InstErrors import INST_ERROR_DATA_MANAGER
from Host.Common import AppStatus

def Log(msg):
    print msg

class RingdownOutput(object):
    def __init__(self):
        self.rdQueue = Queue.Queue(0)

    def listen(self):
        self.rdListener = Listener(self.rdQueue,
                                    BROADCAST_PORT_RD_RECALC,
                                    interface.ProcessedRingdownEntryType,
                                    retry = True,
                                    name = "Ringdown listener",logFunc = Log)
    def run(self):
        i = 0
        while True:
            while not self.rdQueue.empty():
                output = self.rdQueue.get()
                i += 1
                if i%100 == 0:
                    print "Processed Ringdown Delay: %s" % (0.001*(timestamp.getTimestamp()-output.timestamp),)
            time.sleep(0.1)
if __name__ == "__main__":
    f = RingdownOutput()
    f.listen()
    f.run()