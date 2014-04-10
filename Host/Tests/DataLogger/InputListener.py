# InputListener.py
#
# Takes DataLogger inputs and logs them to a file. Filename is hard-coded
# when running as "__main__". It must match the filename in
# BroadcastToDataLogger.py.
#
# Execute this script on a running instrument to capture the data to the file.
#
# Use Ctrl+Break to interrupt the script, as the Queue::get() method is blocking.
# You'll then have a file that can be broadcast to the following apps on a
# workstation without requiring an analyzer. Run BroadcastToDataLogger.py
# to handle broadcasting the data.

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

APP_NAME = "InputListener"

EventManagerProxy_Init(APP_NAME)


class InputListener(object):
    def __init__(self):
        self.q = Queue(0)
        self.Listener = Listener.Listener(self.q, BROADCAST_PORT_DATA_MANAGER, StringPickler.ArbitraryObject, self._DataListener, retry = True,
                                              name = "Data Logger data listener",logFunc = Log)

        self.alarmListener = Listener.Listener(self.q, STATUS_PORT_ALARM_SYSTEM, STREAM_Status, self._AlarmListener, retry = True,
                                              name = "Data Logger alarm status listener",logFunc = Log)

        self.instStatusListener = Listener.Listener(self.q, STATUS_PORT_INST_MANAGER, STREAM_Status, self._InstListener, retry = True,
                                              name = "Data Logger instrument status listener",logFunc = Log)

    def _DataListener(self, data):
        #print "DataManager: ", data
        self.q.put(("DataMgr", data))

    def _AlarmListener(self, data):
        #print "AlarmSystem: ", data
        self.q.put(("AlarmSys", data))

    def _InstListener(self, data):
        #print "InstrManager: ", data
        self.q.put(("InstrMgr", data))
        
if __name__ == "__main__":
    il = InputListener()
    
    with open("C:/temp/CFIDS2085_20140409.dat", "wb") as f:
        #time.sleep(1)
        #app, res = il.q.get()
        #print "%s: %s" % (app, res)
        
        while True:
            res = il.q.get()
            
            cPickle.dump(res, f, -1)
            print res[0]
        
        
        
