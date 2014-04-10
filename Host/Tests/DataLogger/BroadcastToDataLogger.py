# BroadcastToDataLogger.py
#
# This application broadcasts data from the file collected by InputListener.py
# to emulate a live instrument. Current version makes a single pass through the
# file and exits. To make multiple passes, it will need to change the timestamp
# data to the current time before passing the data long.
#
# The input filename is hard-coded, where "__main__" is handled near the bottom
# of this file. It must match the filename in InputListener.py.
# 
# The Config subfolder contains an example stripped down Supervisor config file.
# Paths are relative so they should work as long as the structure of this
# source code doesn't change.
#
# Run the supervisor from sources using the following command (cd to the Host\Supervisor
# folder containing Supervisor.py):
#   > Supervisor.py -c ..\Tests\DataLogger\Config\Supervisor.ini

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
        self.DataBroadcaster = Broadcaster.Broadcaster(BROADCAST_PORT_DATA_MANAGER, APP_NAME, logFunc=Log)
        self.AlarmBroadcaster = Broadcaster.Broadcaster(STATUS_PORT_ALARM_SYSTEM, APP_NAME, logFunc=Log)
        self.InstrBroadcaster = Broadcaster.Broadcaster(STATUS_PORT_INST_MANAGER, APP_NAME, logFunc=Log)
        self.filename = filename
        self.delay = delay
        
    def playback(self):
        with open(self.filename, "rb") as f:
            while True:
                if self.delay > 0:
                    time.sleep(self.delay)
                try:
                    app, data = cPickle.load(f)
                    print app
                    if app == "DataMgr":
                        self.DataBroadcaster.send(StringPickler.PackArbitraryObject(data))
                    elif app == "AlarmSys":
                        self.AlarmBroadcaster.send(StringPickler.ObjAsString(data))
                    elif app == "InstrMgr":
                        self.InstrBroadcaster.send(StringPickler.ObjAsString(data))
                except EOFError:
                    print "reached EOF"
                    break

if __name__ == "__main__":
    bl = BroadcastToDataLogger("C:/temp/CFIDS2085_20140409.dat", .25)
    bl.playback()

