import tables
import zmq
from Host.autogen import interface
from Host.Common import SharedTypes

class LossDataTableType(tables.IsDescription):
    time = tables.Int64Col()
    uncorrectedLoss = tables.Float32Col()

class RdResultsListener(object):
    def __init__(self, ipAddr, port):
        self.context = zmq.Context()
        self.listenSock = self.context.socket(zmq.SUB)
        self.listenSock.connect("tcp://%s:%d" % (ipAddr, port))
        self.listenSock.setsockopt(zmq.SUBSCRIBE, "")
        self.saveHandle = None
        self.saveTable = None
        self.saveFname = ''
        self.latestTimestamp = None
    
    def setSaveFile(self, name):
        self.saveFname = name
        self.saveHandle = tables.openFile(self.saveFname, mode='w', title="CRDS Loss Data")
        self.saveTable = self.saveHandle.createTable(self.saveHandle.root, "lossData", LossDataTableType)
        
    def closeSaveFile(self):
        if self.saveTable is not None:
            self.saveTable.flush()
            self.saveTable = None
        if self.saveHandle:
            self.saveHandle.close()
            print "Closing loss file"
            self.saveHandle = None
            self.saveFname = ''
    
    def run(self):
        poller = zmq.Poller()
        poller.register(self.listenSock, zmq.POLLIN)
        try:
            while True:
                socks = dict(poller.poll())
                if socks.get(self.listenSock) == zmq.POLLIN:
                    obj = interface.RingdownEntryType.from_buffer_copy(self.listenSock.recv())
                    self.latestTimestamp = obj.timestamp
                    so = "%s" % SharedTypes.ctypesToDict(obj)
                    if len(so) > 75:
                        so = so[:75] + "..."
                    print so
        finally:  # Get here on keyboard interrupt or other termination
            self.listenSock.close()
            self.context.term()

    def saveAndFetch(self):
        try:
            rc = self.listenSock.recv(zmq.DONTWAIT)
            obj = interface.RingdownEntryType.from_buffer_copy(rc)
            self.latestTimestamp = obj.timestamp
            if self.saveTable is not None:
                row = self.saveTable.row
                row['time'] = obj.timestamp 
                row['uncorrectedLoss'] = obj.uncorrectedAbsorbance
                row.append()
            return obj
        except zmq.ZMQError:
            return None
    
    def getAvailableData(self,deque,maxLength):
         while True:
            obj = self.saveAndFetch()
            if not obj: break
            deque.append((obj.timestamp, obj.uncorrectedAbsorbance))
            while len(deque)>maxLength: deque.popleft()

    def binAvailableData(self,tsOffset,binAverager,streamNum):
         while True:
            obj = self.saveAndFetch()
            if not obj: break
            binAverager.insertData(obj.timestamp-tsOffset, streamNum, obj.uncorrectedAbsorbance)
