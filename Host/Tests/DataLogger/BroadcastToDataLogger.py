# BroadcastToDataLogger.py
#

import time
import cPickle
from Queue import Queue

from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, \
                                    STATUS_PORT_ALARM_SYSTEM, STATUS_PORT_INST_MANAGER
#from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.MeasData import MeasData
from Host.Common.AppStatus import STREAM_Status
from Host.Common.InstErrors import *
from Host.Common.parsePeriphIntrfConfig import parsePeriphIntrfConfig
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log

APP_NAME = "BroadcastToDataLogger"

EventManagerProxy_Init(APP_NAME)


class BroadcastToDataLogger(object):
    def __init__(self, filename, delay):
        self.DataBroadcaster = Broadcaster(BROADCAST_PORT_DATA_MANAGER, APP_NAME, logFunc=Log)
        self.AlarmBroadcaster = Broadcaster(STATUS_PORT_ALARM_SYSTEM, APP_NAME, logFunc=Log)
        self.InstrBroadcaster = Broadcaster(STATUS_PORT_INST_MANAGER, APP_NAME, logFunc=Log)
        self.filename = filename
        self.delay = delay
        
    def playback(self):
        with open(self.filename, "rb") as f:
            while True:
                try:
                    app, data = cPickle.load(f)
                    if app == "DataMgr":
                        self.DataBroadcaster.send(StringPickler.PackArbitraryObject(data))
                    elif app == "AlarmSys":
                        self.AlarmBroadcaster.send(StringPickler.ObjAsString(data))
                    elif app == "InstrMgr":
                        self.InstrBroadcaster.send(StringPickler.ObjAsString(data))
                except IOError:
                    break

if __name__ == "__main__":
    bl = BroadcastToDataLogger("C:/temp/CFIDS2085_20140409.dat", 1)
    bl.playback()

