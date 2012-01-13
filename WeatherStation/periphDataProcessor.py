from namedtuple import namedtuple
from collections import deque
from threading import Lock
import Queue
import time

SourceTuple = namedtuple('SourceTuple',['ts','valTuple'])

# periphDataProcessor.py is a script for the peripheral data processor

class RawSource(object):
    def __init__(self,queue,maxStore=20):
        self.queue = queue
        self.DataTuple = None
        self.oldData = deque()
        self.maxStore = maxStore
        self.latestTimestamp = None
        
    def getDataTupleType(self,d):
        """Construct a named tuple appropriate for the data in the queue.
        The queue datum d is a tuple consisting of a timestamp and a dictionary"""
        self.DataTuple = namedtuple(self.__class__.__name__+'_tuple',sorted(d[1].keys()))
        
    def getFromQueue(self):
        """Gets a datum from the queue (if available) and adds it to the deque. Length of
        deque is always kept no greater than self.maxStore. Returns True if a point was added 
        to the deque"""
        try:
            d = self.queue.get(block=False)
            if self.DataTuple is None:
                self.getDataTupleType(d)
            self.oldData.append(SourceTuple(d[0],self.DataTuple(**d[1])))
            self.latestTimestamp = d[0]
            if len(self.oldData) > self.maxStore:
                self.oldData.popleft()
            # print self.oldData
            return True
        except Queue.Empty:
            return False
            
    def getOldestTimestamp(self):
        if not self.oldData:
            self.getFromQueue()            
        return self.oldData[0].ts if self.oldData else None
    
    def getData(self,requestTs):
        """Get data at timestamp "requestTs" using linear interpolation. Returns None if data
        are not available."""
        while self.latestTimestamp < requestTs:
            if not self.getFromQueue(): return None
        ts, savedTs = None, None
        valTuple, savedValTuple = None, None
        for (ts, valTuple) in reversed(self.oldData):
            if ts < requestTs:
                alpha = (requestTs-ts)/(savedTs-ts)
                di = tuple([alpha*y+(1-alpha)*y_p for y,y_p in zip(savedValTuple,valTuple)])
                return SourceTuple(requestTs,self.DataTuple(*di))
            else:
                savedTs = ts
                savedValTuple = valTuple
        else:
            return self.oldData[0]


            
class GpsSource(RawSource):
    pass
    
class WsSource(RawSource):
    pass
    
gpsSource = GpsSource(QUEUES[0])
wsSource  = WsSource(QUEUES[1])
            
while True:
    ts1 = gpsSource.getOldestTimestamp()
    if ts1 is not None: break
    time.sleep(0.2)
while True:
    ts2 = wsSource.getOldestTimestamp()
    if ts2 is not None: break
    time.sleep(0.2)
ts = 1000*(1+max(ts1,ts2)//1000)
while True:
    while True:
        d1 = gpsSource.getData(ts)
        if d1 is not None: break
        time.sleep(0.2)
    while True:
        d2 = wsSource.getData(ts)
        if d2 is not None: break
        time.sleep(0.2)
    print d1,d2
    ts += 1000
    time.sleep(0.2)
