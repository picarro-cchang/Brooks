# InputListener.py
#
# Takes DataLogger inputs and logs them to a file.

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

        self.Listener = Listener.Listener(None, BROADCAST_PORT_DATA_MANAGER, StringPickler.ArbitraryObject, self._DataListener, retry = True,
                                              name = "Data Logger data listener",logFunc = Log)

        self.alarmListener = Listener.Listener(None, STATUS_PORT_ALARM_SYSTEM, STREAM_Status, self._AlarmListener, retry = True,
                                              name = "Data Logger alarm status listener",logFunc = Log)

        self.instStatusListener = Listener.Listener(None, STATUS_PORT_INST_MANAGER, STREAM_Status, self._InstListener, retry = True,
                                              name = "Data Logger instrument status listener",logFunc = Log)

    def _DataListener(self, data):
        print "DataManager: ", data

    def _AlarmListener(self, data):
        print "AlarmSystem: ", data

    def _InstListener(self, data):
        print "InstrManager: ", data
