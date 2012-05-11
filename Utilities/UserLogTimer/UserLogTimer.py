"""
File Name: UserLogTimer.py
Purpose: Custom software to restrat all the user logs at exact hours

File History:
    2012-05-10 alex  Created
    
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""

APP_NAME = "UserLogTimer"
APP_DESCRIPTION = "UserLogTimer"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "UserLogTimer.ini"

SLOW_INTERVAL_S = 60
FAST_INTERVAL_S = 1

import wx
import sys
import os
import time
import threading
from Host.Common import CmdFIFO
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SingleInstance import SingleInstance
from Host.Common.SharedTypes import RPC_PORT_DATALOGGER, RPC_PORT_ARCHIVER
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

class DataLoggerInterface(object):
    """Interface to the data logger and archiver RPC"""
    def __init__(self):
        self.archiverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER, ClientName = APP_NAME)
        self.dataLoggerRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER, ClientName = APP_NAME)
        self.exception = None
        self.rpcInProgress = False
        self.userLogDict = {}
        self.privateLogDict = {}

    def getDataLoggerInfo(self):
        """Get data logger info by making a non-blocking RPC call to the data logger"""
        if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = threading.Thread(target=self._getDataLoggerInfo)
        th.setDaemon(True)
        th.start()
        return True

    def _getDataLoggerInfo(self):
        userLogDict = {}
        privateLogDict = {}
        try:
            stat,userLogs = self.dataLoggerRpc.DATALOGGER_getUserLogsRpc()
            stat,privateLogs = self.dataLoggerRpc.DATALOGGER_getPrivateLogsRpc()
            for i in userLogs:
                en = self.dataLoggerRpc.DATALOGGER_logEnabledRpc(i)
                if en:
                    fname = self.dataLoggerRpc.DATALOGGER_getFilenameRpc(i)
                    live, fname = self.archiverRpc.GetLiveArchiveFileName(i,fname)
                    userLogDict[i] = (True,live,fname)                    
                else:
                    userLogDict[i] = (False,False,'')
            for i in privateLogs:
                en = self.dataLoggerRpc.DATALOGGER_logEnabledRpc(i)
                if en:
                    fname = self.dataLoggerRpc.DATALOGGER_getFilenameRpc(i)
                    live, fname = self.archiverRpc.GetLiveArchiveFileName(i,fname)
                    privateLogDict[i] = (True,live,fname)                    
                else:
                    privateLogDict[i] = (False,False,'')
        except Exception,e:
            self.exception = e
        self.rpcInProgress = False
        self.userLogDict = userLogDict
        self.privateLogDict = privateLogDict

    def startUserLogs(self,userLogList,restart=False):
        """Start a list of user logs by making a non-blocking RPC call to the alarm system"""
        while self.rpcInProgress: time.sleep(0.5)
        # if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = threading.Thread(target=self._startUserLogs,args=(userLogList,restart))
        th.setDaemon(True)
        th.start()
        return True

    def _startUserLogs(self,userLogList,restart):
        try:
            for i in userLogList:
                self.dataLoggerRpc.DATALOGGER_startLogRpc(i,restart)
        except Exception,e:
            self.exception = e
        # Refresh info with changes made
        self._getDataLoggerInfo()
        self.rpcInProgress = False
        
class UserLogTimer(object):
    def __init__(self):
        self.dataLogger = DataLoggerInterface()
        self.dataLogger.getDataLoggerInfo()
        self.interval = FAST_INTERVAL_S
        self.lastHr = None
        
    def run(self):
        while True:
            if not self.lastHr:
                self.lastHr = time.localtime()[3]
            else:
                currentHr, currentMin = time.localtime()[3:5]
                print time.strftime("Current Time: %Y-%m-%d %H:%M:%S",time.localtime())
                if currentHr != self.lastHr:
                    userLogs = self.dataLogger.userLogDict.keys()
                    self.dataLogger.startUserLogs(userLogs, restart=True)
                    print "Restarted: %s" % userLogs
                    self.lastHr = currentHr
                    self.interval = SLOW_INTERVAL_S
                else:
                    if currentMin > 58:
                        self.interval = FAST_INTERVAL_S
                    else:
                        self.interval = SLOW_INTERVAL_S
            time.sleep(self.interval)
            
if __name__ == "__main__":
    Log("%s started." % APP_NAME, Level = 0)
    app = SingleInstance("UserLogTimer")
    if app.alreadyrunning():
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "UserLogTimer")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        app = UserLogTimer()
        app.run()