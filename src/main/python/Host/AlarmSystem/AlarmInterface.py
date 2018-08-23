from threading import Thread
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import  RPC_PORT_ALARM_SYSTEM

class AlarmInterface(object):
    """Interface to the alarm system RPC and status ports"""
    def __init__(self,config, clientName  = "No client defined"):
        self.config = config
        self.loadConfig()
        self.alarmRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ALARM_SYSTEM, ClientName = clientName)

        self.statusWord = 0x0
        self.result = None
        self.exception = None
        self.rpcInProgress = False
        self.alarmData = []

    def getAlarmData(self):
        """Get alarm data by making a non-blocking RPC call to the alarm system"""
        if self.rpcInProgress: return False
        self.result = None
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._getAlarmData)
        th.setDaemon(True)
        th.start()
        return True

    def _getAlarmData(self):
        alarmData = []
        index = 1
        try:
            while True:
                status,name = self.alarmRpc.ALARMSYSTEM_getNameRpc(index)
                if status<0: break
                status,mode = self.alarmRpc.ALARMSYSTEM_getModeRpc(index)
                status,enabled = self.alarmRpc.ALARMSYSTEM_isEnabledRpc(index)
                status,alarm1 = self.alarmRpc.ALARMSYSTEM_getAlarmThresholdRpc(index,1)
                status,alarm2 = self.alarmRpc.ALARMSYSTEM_getAlarmThresholdRpc(index,2)
                status,clear1 = self.alarmRpc.ALARMSYSTEM_getClearThresholdRpc(index,1)
                status,clear2 = self.alarmRpc.ALARMSYSTEM_getClearThresholdRpc(index,2)
                alarmData.append((name,mode,enabled,alarm1,clear1,alarm2,clear2))
                index += 1
            self.result = self.alarmData = alarmData
        except Exception,e:
            self.exception = e
        self.rpcInProgress = False

    def setAlarm(self,index,enable,mode,alarm1,clear1,alarm2=0,clear2=0):
        """Set alarm enable and threshold by making a non-blocking RPC call to the alarm system"""
        if self.rpcInProgress: return False
        self.result = None
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._setAlarm,args=(index,enable,mode,alarm1,clear1,alarm2,clear2))
        th.setDaemon(True)
        th.start()
        return True

    def _setAlarm(self,index,enable,mode,alarm1,clear1,alarm2,clear2):
        try:
            self.alarmRpc.ALARMSYSTEM_setModeRpc(index,mode)
            self.alarmRpc.ALARMSYSTEM_setAlarmThresholdRpc(index,1,alarm1)
            self.alarmRpc.ALARMSYSTEM_setClearThresholdRpc(index,1,clear1)
            self.alarmRpc.ALARMSYSTEM_setAlarmThresholdRpc(index,2,alarm2)
            self.alarmRpc.ALARMSYSTEM_setClearThresholdRpc(index,2,clear2)
            if enable:
                self.alarmRpc.ALARMSYSTEM_enableRpc(index)
            else:
                self.alarmRpc.ALARMSYSTEM_disableRpc(index)
        except Exception,e:
            self.exception = e
        # Refresh alarm data with changes made
        self._getAlarmData()
        self.rpcInProgress = False

    def loadConfig(self):
        pass