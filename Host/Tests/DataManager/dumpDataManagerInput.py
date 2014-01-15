from Host.autogen import interface
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_SENSORSTREAM, BROADCAST_PORT_FITTER_BASE
from Host.Common.SharedTypes import STATUS_PORT_DATA_MANAGER, STATUS_PORT_INST_MANAGER, ctypesToDict
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common import AppStatus, StringPickler
from Queue import Queue
import cPickle
import sys
import time

def Log(text):
    print "Log: %s" % text
    

class DummyDataManager(object):
    def __init__(self):
        self.sensorQueue = Queue(0)
        self.SensorListener = Listener(self.sensorQueue,
                                     BROADCAST_PORT_SENSORSTREAM,
                                     interface.SensorEntryType,
                                     None,
                                     retry = True,
                                     name = "Data manager sensor stream listener",logFunc = Log)
        self.fitterListener = []
        self.fitterListenerQueue = []
        
        for fitterIndex in range(interface.MAX_FITTERS):
            q = Queue(0)
            self.fitterListenerQueue.append(q)
            self.fitterListener.append(Listener(q,
                                     BROADCAST_PORT_FITTER_BASE+fitterIndex,
                                     StringPickler.ArbitraryObject,
                                     None,
                                     retry = True,
                                     name = "Data manager fitter %d listener" % fitterIndex,logFunc = Log))
        self.lastFitAnalyzed = 0
        self.instMgrStatusQueue = Queue(0)
        self.InstMgrStatusListener = Listener(self.instMgrStatusQueue,
                                              STATUS_PORT_INST_MANAGER,
                                              AppStatus.STREAM_Status,
                                              None,
                                              retry = True,
                                              name = "Data manager Instrument Manager listener",logFunc = Log)

if __name__ == "__main__":
    if len(sys.argv)<2:
        print "Usage: %s duration_in_sec"
    else:
        duration = float(sys.argv[1])
        fp = open("dmInput.pic","wb",0)
        dm = DummyDataManager()
        start = time.time()
        while time.time() < start+duration:
            if not dm.sensorQueue.empty():
                cPickle.dump(("S",ctypesToDict(dm.sensorQueue.get())),fp,-1)
            for fitterIndex in range(interface.MAX_FITTERS):
                if not dm.fitterListenerQueue[fitterIndex].empty():
                    cPickle.dump(("F%d" % fitterIndex,dm.fitterListenerQueue[fitterIndex].get()),fp,-1)
            if not dm.instMgrStatusQueue.empty():
                cPickle.dump(("I",ctypesToDict(dm.instMgrStatusQueue.get())),fp,-1)
            time.sleep(0.001)