from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_SENSORSTREAM, BROADCAST_PORT_FITTER_BASE, RPC_PORT_DATA_MANAGER
from Host.Common.SharedTypes import STATUS_PORT_DATA_MANAGER, STATUS_PORT_INST_MANAGER, ctypesToDict, dictToCtypes
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common import AppStatus, StringPickler, timestamp
from Queue import Queue
import cPickle
import sys
import time

def Log(text):
    print "Log: %s" % text

class DriveDataManager(object):
    def __init__(self):
        self.sensorCast = Broadcaster(
            port=BROADCAST_PORT_SENSORSTREAM,
            name="Sensor Broadcaster",logFunc=Log)

        self.fitterCastList = []
        for fitterIndex in range(interface.MAX_FITTERS):
            self.fitterCastList.append(Broadcaster(
            port=BROADCAST_PORT_FITTER_BASE+fitterIndex,
            name="Fitter Broadcaster",logFunc=Log))

        self.statusCast = Broadcaster(
            port=STATUS_PORT_INST_MANAGER,
            name="Status Broadcaster",logFunc=Log)

        self.dataManager =  CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER,
                                         "DriveDataManager",
                                         IsDontCareConnection = False)

def waitUntil(ts,offset):
    tsNow = timestamp.getTimestamp()
    if offset is None:
        offset = tsNow - ts
    if tsNow < ts + offset:
        time.sleep(0.001*(ts+offset-tsNow))
    return offset

if __name__ == "__main__":
    if len(sys.argv)<2:
        print "Usage: %s filename"
    else:
        filename = sys.argv[1]
        fp = open(filename,"rb")
        ddm = DriveDataManager()
        ddm.dataManager.StartInstMgrListener()
        modeName = 'CFADS_mode'
        ddm.dataManager.Mode_Set(modeName)
        assert ddm.dataManager.Mode_Get() == modeName
        ddm.dataManager.Enable()
        offset = None
        while True:
            try:
                s,o = cPickle.load(fp)
                if s == 'S':
                    ts = o['timestamp']
                    offset = waitUntil(ts,offset)
                    c = interface.SensorEntryType()
                    dictToCtypes(o,c)
                    #ddm.sensorCast.send(StringPickler.ObjAsString(c))
                elif s.startswith("F"):
                    fitterIndex = int(s[1:])
                    ts = o[0]
                    offset = waitUntil(ts,offset)
                    ddm.fitterCastList[fitterIndex].send(StringPickler.PackArbitraryObject(o))
                elif s == 'I':
                    c = AppStatus.STREAM_Status()
                    dictToCtypes(o,c)
                    ddm.statusCast.send(StringPickler.ObjAsString(c))
            except:
                raise
        fp.close() 
