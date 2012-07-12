from collections import deque
import time
import Queue
from Host.Common.namedtuple import namedtuple

SourceTuple = namedtuple('SourceTuple',['ts','valTuple'])

class RawSource(object):
    """RawSource objects are created from a data queue. They expose a getData method
    which is used to request the value of the source at a specified timestamp. Linear
    interpolation is used to calculate the source valTuple at the desired time, unless
    the requested timestamp is in the future of all the data present in the queue, in
    which case None is returned. Up to maxStore previous queue entries are buffered in
    a deque for the interpolation. If the requested timestamp is earlier than all the
    buffered entries, the first entry is returned.
    """
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
                alpha = float(requestTs-ts)/(savedTs-ts)
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

def syncSources(sourceList,msOffsetList,msInterval,sleepTime=0.01):
    """Use linear interpolation to synchronize a collection of decendents of RawSource (in 
    sourceList) to a grid of times which are multiples of msInterval. A per-source offset is 
    specified in offsetList to compensate for timestamp differences. Each source either returns None
    or a SourceTuple (which is a millisecond timestamp together with a valTuple) when 
    its getData method is called.
    
    This is a generator which yields a timestamp and a list of valTuples from each source.
    A StopIteration is thrown if the DONE() function returns True."""
    
    # First determine when to start synchronized timestamps
    oldestTs = []
    for s in sourceList:
        while True:
            ts = s.getOldestTimestamp()
            if ts is not None:
                oldestTs.append(ts)
                break
            time.sleep(sleepTime)
            
    oldestAvailableFromAll = max([ts-offset for ts,offset in zip(oldestTs,msOffsetList)])
    # Round to the grid of times which are multiples of msInterval
    ts = msInterval*(1+oldestAvailableFromAll//msInterval)
    
    # Get all the valTuples at the specified timestamp
    while True:
        valTuples = []
        for s,offset in zip(sourceList,msOffsetList):
            while True:
                d = s.getData(ts+offset)
                # if DONE(): return
                if d is not None:
                    valTuples.append(d.valTuple)
                    break
                time.sleep(sleepTime)
        yield ts, valTuples
        ts += msInterval
    
def main():
    gpsSource = GpsSource(SENSORLIST[0])
    wsSource  = WsSource(SENSORLIST[1])
    msOffsets = [0,0]  # ms offsets for GPS and sonic anemometer
    syncDataSource = syncSources([gpsSource,wsSource],msOffsets,1000)
    for ts,[gps,ws] in syncDataSource:
        WRITEOUTPUT(ts,[ws.WS_SPEED,ws.WS_COS_DIR,ws.WS_SIN_DIR,gps.GPS_ABS_LAT,gps.GPS_ABS_LONG])

main()
