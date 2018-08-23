import time
from threading import Thread
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import  RPC_PORT_DATALOGGER,  RPC_PORT_ARCHIVER


class DataLoggerInterface(object):
    """Interface to the data logger and archiver RPC"""
    def __init__(self,config, clientName = "No client defined"):
        self.config = config
        self.loadConfig()
        self.archiverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER, ClientName = clientName)
        self.dataLoggerRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER, ClientName = clientName)
        self.exception = None
        self.rpcInProgress = False
        self.userLogDict = {}
        self.privateLogDict = {}

    def getDataLoggerInfo(self):
        """Get data logger info by making a non-blocking RPC call to the data logger"""
        if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._getDataLoggerInfo)
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
        th = Thread(target=self._startUserLogs,args=(userLogList,restart))
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

    def stopUserLogs(self,userLogList):
        """Stop a list of user logs by making a non-blocking RPC call to the alarm system"""
        while self.rpcInProgress: time.sleep(0.5)
        # if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._stopUserLogs,args=(userLogList,))
        th.setDaemon(True)
        th.start()
        return True

    def _stopUserLogs(self,userLogList):
        try:
            for i in userLogList:
                self.dataLoggerRpc.DATALOGGER_stopLogRpc(i)
        except Exception,e:
            self.exception = e
        # Refresh info with changes made
        self._getDataLoggerInfo()
        self.rpcInProgress = False

    def loadConfig(self):
        pass