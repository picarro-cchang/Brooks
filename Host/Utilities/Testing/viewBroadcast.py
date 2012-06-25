import Queue
import time
from cPickle import dumps
from struct import pack
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import RPC_PORT_MEAS_SYSTEM, RPC_PORT_DRIVER, RPC_PORT_DATA_MANAGER, RPC_PORT_FREQ_CONVERTER, RPC_PORT_INSTR_MANAGER
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_MEAS_SYSTEM, BROADCAST_PORT_SENSORSTREAM
from Host.Common.SharedTypes import STATUS_PORT_DATA_MANAGER, STATUS_PORT_INST_MANAGER, ctypesToDict
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.Listener import Listener
from Host.Common.InstErrors import INST_ERROR_DATA_MANAGER
from Host.Common import AppStatus

def Log(msg):
    print msg
    
class DataManagerListeners(object):
    def __init__(self):
        self.measSystemQueue = Queue.Queue(0)
        self.sensorQueue = Queue.Queue(0)
        self.instMgrStatusQueue = Queue.Queue(0)
        self.measSystemListener = None
        self.sensorListener = None
        self.instMgrListener = None
        
    def _MeasDataFilter(self, obj):
        measData = MeasData()
        measData.ImportPickleDict(obj)
        return (1, timestamp.getTimestamp(), measData)
        
    def _SensorFilter(self, obj):
        return (2, timestamp.getTimestamp(), ctypesToDict(obj))
        
    def _InstMgrStatusFilter(self, obj):
        return (3, timestamp.getTimestamp(), ctypesToDict(obj))
        
    def run(self):
        self.measSystemListener = Listener(self.measSystemQueue,
                                         BROADCAST_PORT_MEAS_SYSTEM,
                                         StringPickler.ArbitraryObject,
                                         self._MeasDataFilter,
                                         retry = True,
                                         name = "Data manager sandbox measurement system listener",logFunc = Log)
        self.sensorListener = Listener(self.sensorQueue,
                                         BROADCAST_PORT_SENSORSTREAM,
                                         interface.SensorEntryType,
                                         self._SensorFilter,
                                         retry = True,
                                         name = "Data manager sandbox sensor stream listener",logFunc = Log)
        self.instMgrListener = Listener(self.instMgrStatusQueue,
                                         STATUS_PORT_INST_MANAGER,
                                         AppStatus.STREAM_Status,
                                         self._InstMgrStatusFilter,
                                         retry = True,
                                         name = "Data manager sandbox instrument manager listener",logFunc = Log)
    def stop(self):
        self.measSystemListener.stop()
        self.sensorListener.stop()
        self.instMgrListener.stop()
        
if __name__ == "__main__":
    dm = DataManagerListeners()
    dm.run()
    while True:
        while not dm.measSystemQueue.empty():
            idx,ts,ms = dm.measSystemQueue.get()
            print ms
        while not dm.sensorQueue.empty():
            dm.sensorQueue.get()
        while not dm.instMgrStatusQueue.empty():
            dm.instMgrStatusQueue.get()
        time.sleep(1)