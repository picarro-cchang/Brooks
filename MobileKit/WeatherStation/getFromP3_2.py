# Fetching data from P3

import urllib2
import urllib

try:
    import simplejson as json
except:
    import json

from collections import deque
from Host.Common.namedtuple import namedtuple
import calendar
import datetime
import time
import traceback
import math
import threading
import Queue

NOT_A_NUMBER = 1e1000/1e1000

DataTuple = namedtuple("DataTuple",["etm","latestEtm","data"])

class P3_Accessor(object):
    """Generators used to access data stored as collections in the P3 MongoDB. These yield tuples
    consisting of the epoch time and a document from the collection which lie within a certain range
    of times, startEtm through endEtm. If the endEtm argument is omitted, the generator does not 
    terminate, but yields None if there are no documents yet available from the collection"""
    
    def __init__(self,anz):
        self.csp = "https://dev.picarro.com/node"
        self.svc = "gdu"
        self.ticket = "abcdefg"
        self.v_rsc = "1.0/AnzLog"
        self.analyzerName = anz
        #self.discardList = ["EPOCH_TIME", "LOGTYPE", "FILENAME_nint", "_id", "SERVER_HASH", "row"]
        self.discardList = ["LOGTYPE", "FILENAME_nint", "_id", "SERVER_HASH", "row"]
        
    def _genCore(self,url,params):
        """Generator which yields Datatuples from the specified P3 server url, passing in the
        parameters as the dictionary "params". Documents are fetched in non-decreasing order of
        epoch times, lying between params["startEtm"] and params["endEtm"], and the generator raises 
        StopIteration after all matching documents are yielded. 
        However, if params does not contain "endEtm", this indicates we are accessing a continually 
        updating live archive, and the generator will yield None while no more matching documents 
        are present.
        
        Data from MongoDB are fetched from the server in blocks of up to params["limit"] documents
        at a time. The log type is specified as params["logtype"] and returned documents are filtered
        to exclude those which contain LOGTYPE keys which do not match this specification.
        
        When documents are returned, any keys which lie in self.discardList are removed.
        
        We detect when there are no (more) data on the server when it raises a 404 error.
        """
        lastRow = None
        while True:
            paramStr = urllib.urlencode(params)
            get_url = url+("?%s" % paramStr if params else "")
            try:
                tstart = time.clock()
                print "start P3 get"
                resp = urllib2.urlopen(get_url,timeout=5.0)
                rtndata_str = resp.read()
                rtndata = json.loads(rtndata_str)
                print "P3 get", time.clock()-tstart
            except urllib2.URLError,e:
                if not hasattr(e,"code") or e.code in [502,504]: # Bad gateway, gateway timeout
                    print "%s: retrying" % e
                    time.sleep(1.0)
                    continue
                elif e.code == 404:   # Not found
                    if "endEtm" in params: 
                        break
                    else:
                        yield None
                else:
                    raise
            nrows = 0
            for drow in rtndata:
                nrows += 1
                if drow == lastRow: continue    # Duplicate row, discard
                lastRow = drow
                etime = drow['EPOCH_TIME']
                if ('LOGTYPE' in drow) and (drow['LOGTYPE'] != params["logtype"]): continue
                for d in self.discardList: 
                    if d in drow: del drow[d]
                yield DataTuple(etime, rtndata[-1]['EPOCH_TIME'], drow)
            params["startEtm"] = etime    # Start at the last time, need to reject duplicate lines
            if (nrows<params["limit"]):
                if "endEtm" in params: 
                    break
                else:
                    yield None
                    
    def genAnalyzerData(self,startEtm,endEtm=None,limit=500):
        url = '%s/%s/%s/%s/%s' % (self.csp, "rest", self.svc, self.ticket, self.v_rsc)
        get_params = dict(qry="byEpoch",anz=self.analyzerName,limit=limit,startEtm=startEtm,logtype="dat")
        if endEtm is not None: get_params["endEtm"] = endEtm
        return self._genCore(url,get_params)
    
    def genGpsData(self,startEtm,endEtm=None,limit=500):
        url = '%s/%s/%s/%s/%s' % (self.csp, "rest", self.svc, self.ticket, self.v_rsc)
        get_params = dict(qry="byEpoch",anz=self.analyzerName,limit=limit,startEtm=startEtm,logtype="GPS_Raw")
        if endEtm is not None: get_params["endEtm"] = endEtm
        return self._genCore(url,get_params)

    def genWsData(self,startEtm,endEtm=None,limit=500):
        url = '%s/%s/%s/%s/%s' % (self.csp, "rest", self.svc, self.ticket, self.v_rsc)
        get_params = dict(qry="byEpoch",anz=self.analyzerName,limit=limit,startEtm=startEtm,logtype="WS_Raw")
        if endEtm is not None: get_params["endEtm"] = endEtm
        return self._genCore(url,get_params)

class P3SourceGap(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return "Epoch time gap too large. Next available epoch %s" % self.value

class P3NoDataYet(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return "No data yet for epoch time %s" % self.value
        
class P3NoDataUntil(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return "No data until %s" % self.value

class P3_Source(object):
    """P3_Source objects are associated with collections in the P3 Mongo database.
    They expose a getData method which is used to request the value of the source at 
    a specified epoch time. The requested times must be in approximately 
    non-decreasing order for a given source, since only a number (maxStore) 
    of previously fetched data are buffered and available for interpolation
    
    The getData method returns a dictionary containing the data at the given time, 
    calculated using linear interpolation.
    
    It can raise the following exceptions:
        P3SourceGap: Indicates that linear interpolation is not possible because the 
          available epoch times which cover the requested time are too far apart. 
          This indicates there was a gap in the data source.
          Exception value indicates the epoch time of the next available datum.
        P3NoDataYet: Indicates that the requested epoch time lies in the future of the
          time range available for the source. Value indicates requested epoch time.
        P3NoDataUntil: Indicates that the requested epoch time lies in the past of the
          time range present in the buffer. Value indicates first epoch time in buffer.
        StopIteration: Indicates that the underlying generator has run out of data,
          because the requested time is after its endEtm
    """
        
    def __init__(self,accessor,endEtm=None,maxGap=2.0,maxStore=10,limit=500):
        # The accessor is a generator function which yields documents from
        #  the P3 collection. The maximum difference in epoch times allowed
        #  before there is considered to be a gap in the data is "maxGap"
        self.accessor = accessor
        self.generator = None
        self.endEtm = endEtm
        self.oldData = deque()
        self.maxStore = maxStore
        self.latestEtm = -1
        self.currentEtm = -1
        self.maxGap = maxGap
        self.limit = limit
        self.accessLock = threading.Lock()
        
    def getNext(self):
        """Gets a datum from the generator (if available) and adds it to the deque. Length of
        deque is always kept no greater than self.maxStore. Returns True if a point was added 
        to the deque"""
        if (self.generator is None):
            self.generator = self.accessor(startEtm,self.endEtm,limit=self.limit)
        d = self.generator.next()
        if d is None:
            return False
        self.oldData.append((d.etm,d.data))
        self.latestEtm = d.latestEtm
        self.currentEtm = d.etm
        if len(self.oldData) > self.maxStore:
            self.oldData.popleft()
        return True

    def getData(self,reqEtm):
        """Get data at epoch time "reqEtm" using linear interpolation. Run this
        within a lock since multiple threads may try to access it when sources
        are being synchronized."""
        start = time.clock()
        self.accessLock.acquire()
        try:
            if self.latestEtm < reqEtm:
                startEtm = reqEtm - self.maxGap
                self.generator = self.accessor(startEtm,self.endEtm,limit=self.limit)
                if not self.getNext():
                    raise P3NoDataYet(reqEtm)
            while self.currentEtm <= reqEtm:
                if not self.getNext():
                    raise P3NoDataYet(reqEtm)
            etm, savedEtm = None, None
            data, savedData = None, None
            for (etm, data) in reversed(self.oldData):
                if etm <= reqEtm:
                    if savedEtm != etm:
                        if (savedEtm-etm) > self.maxGap:
                            raise P3SourceGap(savedEtm)
                        else:
                            alpha = float(reqEtm-etm)/(savedEtm-etm)
                    else:
                        alpha = 0.5
                    result = {}
                    for k in data:
                        if k not in savedData: continue
                        if isinstance(data[k],(int,float)) and isinstance(savedData[k],(int,float)):
                            result[k] = alpha*savedData[k] + (1.0-alpha)*data[k]
                        else:
                            result[k] = NOT_A_NUMBER
                    return result
                else:
                    savedEtm = etm
                    savedData = data
            else:
                firstEtm,firstData = self.oldData[0]
                raise P3NoDataUntil(firstEtm)
        finally:
            self.accessLock.release()
            d = time.clock()-start
            if d>1.0: print "getData took", d

class SyncSource(object):
    """Class which provides a generator method which yields time-aligned data from a list
    of P3_Source instances. A time offset may be specified for each source. Data are yielded
    for epoch times that are multiples of the specified interval in the format
        
        epochTime, [dataDict1, dataDict2,...]
    
    If any source raises StopIteration, so does this generator. If no data are available, 
    it yields None. """
    
    def __init__(self,sourceList,offsetList,interval=1.0,startEtm=0.0):
        self.sourceList = sourceList
        self.offsetList = offsetList
        self.interval = interval
        self.startEtm = startEtm
        pass

    def generator(self):    
        # Generate synchronized data at startEtm+n*self.interval for integer n.
        #  n is advanced as necessary to retrieve data available from all sources
        def getFromSource(src,etm,offset,resultQueue,idx):
            # Function to be run in thread to get data from a source at the correct
            #  epoch time etm+offset. It puts a tuple (idx,result) on the resultQueue
            #  where the type of result indicates what happened and returns a value for
            #  the source of index idx.
            try:
                resultQueue.put((idx,src.getData(etm+offset)))
            except StopIteration,e:
                resultQueue.put((idx,e))
            except P3NoDataYet:
                resultQueue.put((idx,None))
            except P3SourceGap,e:
                resultQueue.put((idx,etm+self.interval*math.ceil((e.value-offset-etm)/self.interval)))
            except P3NoDataUntil,e:
                resultQueue.put((idx,etm+self.interval*math.ceil((e.value-offset-etm)/self.interval)))
            
        
        oldestTs = []
        nSources = len(self.sourceList)
        while True:
            results = [None for i in range(nSources)]
            # Fetch data from sources in threads to hasten fetches from the P3 server
            threadList = []
            resultQueue = Queue.Queue(nSources)
            startEtm = self.startEtm
            for i,(s,o) in enumerate(zip(self.sourceList,self.offsetList)):
                th = threading.Thread(target=getFromSource,args=(s,startEtm,o,resultQueue,i))
                threadList.append(th)
                th.setDaemon(True)
                th.start()
            # Wait for all the threads to complete and work out what to do by getting from resultQueue
            for th in threadList:
                th.join()
            validResults = 0
            yieldNone = False
            for i in range(nSources):
                idx,r = resultQueue.get()
                if r is None: yieldNone = True
                elif isinstance(r,StopIteration): return
                elif isinstance(r,dict): 
                    results[idx] = r
                    validResults += 1
                else: self.startEtm = max(self.startEtm,r)
            if yieldNone: 
                yield None    
            elif validResults == nSources:
                yield startEtm,results
                self.startEtm = startEtm + self.interval
                
if __name__ == "__main__":
    p3 = P3_Accessor("FCDS2006")
    #endEtm   = calendar.timegm(time.strptime("2012-03-23T03:00:00","%Y-%m-%dT%H:%M:%S"))
    endEtm = 1332491271
    analyzerSource = P3_Source(p3.genAnalyzerData,endEtm=endEtm)
    gpsSource = P3_Source(p3.genGpsData,endEtm=endEtm)
    wsSource = P3_Source(p3.genWsData,endEtm=endEtm)
    # startEtm = calendar.timegm(time.strptime("2012-03-23T08:20:00","%Y-%m-%dT%H:%M:%S"))
    # startEtm = calendar.timegm(time.strptime("2012-03-23T02:00:00","%Y-%m-%dT%H:%M:%S"))
    #startEtm = 0
    startEtm = 1332463740
    #syncSource = SyncSource([analyzerSource,gpsSource,wsSource],[0.0,1.5,2.6],interval=60.0,startEtm=startEtm)
    syncSource = SyncSource([gpsSource,wsSource],[0.0,0.0],interval=60.0,startEtm=startEtm)
    tstart = time.clock()
    for i,d in enumerate(syncSource.generator()):
        print i,time.clock()-tstart,d
        raw_input()
        tstart = time.clock()
    
    #startEtm = calendar.timegm(time.strptime("2012-03-23T00:48:59","%Y-%m-%dT%H:%M:%S"))
    #endEtm   = calendar.timegm(time.strptime("2012-03-23T01:18:59","%Y-%m-%dT%H:%M:%S"))
    #startEtm = calendar.timegm(time.strptime("2012-03-23T02:00:00","%Y-%m-%dT%H:%M:%S"))
    #endEtm   = calendar.timegm(time.strptime("2012-03-23T03:00:00","%Y-%m-%dT%H:%M:%S"))
    #for i,dat in enumerate(p3.genAnalyzerData(startEtm,endEtm)):
