import Queue
import time
from cPickle import dumps
from struct import pack
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_SPECTRUM_COLLECTOR
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common.InstErrors import INST_ERROR_DATA_MANAGER
from Host.Common import AppStatus

def Log(msg):
    print msg
    
class SpectrumCollectorOutput(object):
    def __init__(self):
        self.spectQueue = Queue.Queue(0)
        
    def listen(self):
        self.spectListener = Listener(self.spectQueue,
                                      BROADCAST_PORT_SPECTRUM_COLLECTOR,
                                      StringPickler.ArbitraryObject,
                                      retry = True,
                                      name = "Spectrum Collector Output Listener")
    def run(self):
        while True:
            while not self.spectQueue.empty():
                output = self.spectQueue.get()
                timevect = output["rdData"]["timestamp"]
                now = timestamp.getTimestamp()
                print "Spectrum Collector Output: %s - %s" % (0.001*(now-timevect.max()),
                0.001*(now-timevect.min()),)
            time.sleep(0.05)
            
if __name__ == "__main__":
    f = SpectrumCollectorOutput()
    f.listen()
    f.run()
    