# Fetching data from P3

import urllib2
import urllib

try:
    import simplejson as json
except:
    import json

from collections import deque
from namedtuple import namedtuple
import calendar
import datetime
import sys
import time
import traceback
import math
import threading
import Queue

NOT_A_NUMBER = 1e1000/1e1000

DataTuple = namedtuple("DataTuple",["etm","latestEtm","data"])
PosTuple  = namedtuple("PosTuple", ["pos","latestPos","data"])

class P3_Accessor(object):
    """Factories used to make accessors that access AnzLog and AnzLogMeta documents stored in collections 
    in the P3 MongoDB.
    
    The parameter supplied to the factory is the log type. For example, 
        genAnzLog("WS_Dat") returns an accessor, which is a function that is used to make a generator for 
            getting the weather station data.
        genAnzLog("WS_Dat")(startEtm,endEtm=None,limit=500) is the generator itself which yields documents
            lying between startEtm and endEtm. Note that limit is the maximum number of documents to retrieve
            from the database at one time, and is not the maximum number of documents that the generator 
            will yield. The generator only terminates once there are no more documents in the time range.
            
            In order to ameliorate the latency needed to fetch from the database, each accessor can spawn
            a background thread to preemptively fetch buffers from the database that the generator may
            subsequently be called upon to yield.
        
        Similarly genAnzLogMeta(logtype) is an accessor for the analyzer log metadata.
    
    The resulting generators yield tuples consisting of the epoch time and a document from the collection 
    which lie within the range of times startEtm through endEtm. If the endEtm argument is omitted, 
    the generator does not terminate, but yields None if there are no documents yet available from the 
    collection"""
    
    def __init__(self,anz):
        self.csp = "https://dev.picarro.com/node"
        self.svc = "gdu"
        self.analyzerName = anz
        #self.discardList = ["EPOCH_TIME", "LOGTYPE", "FILENAME_nint", "_id", "SERVER_HASH", "row"]
        #self.discardList = ["LOGTYPE", "FILENAME_nint", "_id", "SERVER_HASH"]
        self.discardList = ["FILENAME_nint", "_id", "SERVER_HASH"]
        self.getTicket()
        
    def getTicket(self):
        # Version and Resource
        v_rsc = "1.0/Admin"
        qry = "issueTicket"
        sys = "APITEST"
        svc = "sec"
        identity = "85490338d7412a6d31e99ef58bce5de6"
        ticket = "dummy"
        rprocs = '["AnzLog:byEpoch","AnzLogMeta:byEpoch"]'
        get_url = '%s/%s/%s/%s/%s?qry=%s&sys=%s&identity=%s&rprocs=%s' %(self.csp, "rest", svc, ticket, v_rsc, qry, sys, identity, rprocs)
        # print "GET URL: %s"  % get_url

        params = {"qry": qry, "sys": sys, "identity": identity, "rprocs": rprocs}
        post_url = '%s/%s/%s/%s/%s' %(self.csp, "rest", svc, ticket, v_rsc)
        # print "POST URL: %s"  % post_url

        while True:
            try:
                resp = urllib2.urlopen(post_url, data=urllib.urlencode(params))
                rtndata_str = resp.read()
                # print "POST Response: %s: %s" % (resp.code, rtndata_str)
                break
            except urllib2.URLError,e:
                print "Error: ", e
                time.sleep(1.0)
                print "Retrying..."
            
        rtndata = json.loads(rtndata_str)
        # print "rtndata", rtndata

        if "ticket" in rtndata:
            self.ticket = rtndata["ticket"]
        else:
            self.ticket = None
        return rtndata
    
    def _genCore(self,params,v_rsc,lwm=500,prefetch=30.0):
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
        N.B. "limit" is NOT the maximum number of documents to be retrieved by the generator.
        
        When documents are returned, any keys which lie in self.discardList are removed.
        
        We detect when there are no (more) data on the server when it raises a 404 error.
        
        "lwm" indicates a low-water mark, when there are fewer than this number of documents in 
        the buffer, a new buffer is fetched
        "prefetch" indicates how far in the past (in seconds) to start fetching from when a new start 
        time is requested which is too far in the future of what has been buffered
        """
        threadDict = dict(thread=None,start=None,latestEtm=0,lastRow=None)
        resultQueue = Queue.Queue()
        def fetchBuffer():
            # Fetch the next buffer's worth of data from P3. To be executed in a thread
            # Write the result or an uncaught exception into resultQueue
            paramStr = urllib.urlencode(params)
            while True:
                try:
                    tstart = time.clock()
                    url = '%s/%s/%s/%s/%s' % (self.csp, "rest", self.svc, self.ticket, v_rsc)
                    get_url = url+("?%s" % paramStr if params else "")
                    print "URL: %s" % get_url
                    resp = urllib2.urlopen(get_url,timeout=5.0)
                    rtndata_str = resp.read()
                    # Only push rows which are of the correct logtype
                    etm = params["startEtm"]
                    for drow in json.loads(rtndata_str):
                        if drow == threadDict["lastRow"]: continue    # Duplicate row, discard
                        if ('LOGTYPE' in drow) and (drow['LOGTYPE'] != params["logtype"]): continue
                        threadDict["lastRow"] = drow
                        if 'EPOCH_TIME' in drow:
                            etm = drow['EPOCH_TIME']
                        else:
                            etm = drow['etmname']
                        # We make a copy so that drow can be used to check for duplicate rows
                        drowCopy = drow.copy()
                        for d in self.discardList: 
                            if d in drowCopy: del drowCopy[d]
                        resultQueue.put((etm,drowCopy))
                    threadDict["latestEtm"] = etm
                    # print "P3 get from %s, %.1f s, startTime %.1f, lastTime %.1f" % (params["logtype"],time.clock()-tstart,params["startEtm"],threadDict["latestEtm"])
                    params["startEtm"] = etm    # Start at the last time, but may need to reject duplicate lines
                    params["excludeStart"] = True
                    return
                except urllib2.URLError,e:
                    if not hasattr(e,"code") or e.code in [502,504]: # Bad gateway, gateway timeout
                        print "%s: retrying" % e
                        time.sleep(1.0)
                        continue
                    elif e.code == 404:   # Not found
                        return
                    elif e.code == 403:   # Forbidden, get new ticket
                        print "Permission denied, getting a new ticket"
                        self.getTicket()
                    else:
                        print e
                        print traceback.format_exc()
                        resultQueue.put(e)
                except Exception,e:
                    print traceback.format_exc()
                    resultQueue.put(e)
                    
        while True:
            if resultQueue.empty(): # We must initiate a fetch unless one is in progress
                if threadDict["thread"] is None or not threadDict["thread"].isAlive():
                    threadDict["thread"] = threading.Thread(target=fetchBuffer)
                    threadDict["thread"].setDaemon(True)
                    threadDict["start"] = time.clock()
                    threadDict["thread"].start()
                # We must wait for the thread to complete and then yield the document    
                threadDict["thread"].join()
                if resultQueue.empty(): # Nothing there, either yield None or return to raise StopIteration
                    if "endEtm" in params: 
                        return
                    else:
                        reqEtm = yield None
                else: # Return the next available document
                    d = resultQueue.get()
                    if isinstance(d,Exception): 
                        print traceback.format_exc()
                        raise d
                    etm,drow = d
                    reqEtm = yield DataTuple(etm, threadDict["latestEtm"], drow)
            else:
                d = resultQueue.get()
                # Check that:
                #  a) no fetch is in progress, 
                #  b) the queue length is below the low-water mark, and 
                #  c) it has been at least two seconds since the last fetch 
                # If so initiate another fetch in the background
                if (not threadDict["thread"].isAlive()) and (resultQueue.qsize()<lwm) and (time.clock()-threadDict["start"]>2.0):
                    threadDict["thread"] = threading.Thread(target=fetchBuffer)
                    threadDict["thread"].setDaemon(True)
                    threadDict["start"] = time.clock()
                    threadDict["thread"].start()
                if isinstance(d,Exception):
                    print traceback.format_exc()
                    raise d
                etm,drow = d
                reqEtm = yield DataTuple(etm, threadDict["latestEtm"], drow)
            if reqEtm is not None:
                # We have a hint as to the epoch time at which the data are required
                #  If it is too far into the future, we clear the buffer and restart
                if reqEtm > threadDict["latestEtm"]:
                    if (threadDict["thread"] is not None) and (threadDict["thread"].isAlive()):
                        threadDict["thread"].join()
                        if reqEtm > threadDict["latestEtm"]:
                            # print "Emptying prefetch queue"
                            # Empty out the queue and specify new start time
                            while not resultQueue.empty(): resultQueue.get() 
                            params["startEtm"] = max(etm,reqEtm - prefetch)
                
    def genAnzLog(self,logtype):
        def _genAnzLog(startEtm,endEtm=None,limit=500,**kwds):
            get_params = dict(qry="byEpoch",anz=self.analyzerName,limit=limit,startEtm=startEtm,logtype=logtype)
            if kwds: get_params.update(kwds)
            if endEtm is not None: get_params["endEtm"] = endEtm
            return self._genCore(get_params,v_rsc="1.0/AnzLog",lwm=limit)
        return _genAnzLog
        
    def genAnzLogMeta(self,logtype):
        def _genAnzLogMeta(startEtm,endEtm=None,limit=500,**kwds):
            get_params = dict(qry="byEpoch",anz=self.analyzerName,limit=limit,startEtm=startEtm,logtype=logtype)
            if kwds: get_params.update(kwds)
            if endEtm is not None: get_params["endEtm"] = endEtm
            return self._genCore(get_params,v_rsc="1.0/AnzLogMeta",lwm=limit)
        return _genAnzLogMeta

class P3_Accessor_ByPos(object):
    """Factories used to make accessors that access AnzLog and AnzLogMeta documents stored in collections 
    in the P3 MongoDB.
    
    The parameter supplied to the factory is the log type. For example, 
        genAnzLog("WS_Dat") returns an accessor, which is a function that is used to make a generator for 
            getting the weather station data.
        genAnzLog("WS_Dat")(startPos,endPos=None,limit=500) is the generator itself which yields documents
            lying between startPos (inclusive) and endPos (exclusive). Note that limit is the maximum number 
            of documents to retrieve from the database at one time, and is not the maximum number of documents 
            that the generator will yield. The generator only terminates once there are no more documents in 
            the range of positions (rows).
            
            In order to ameliorate the latency needed to fetch from the database, each accessor can spawn
            a background thread to preemptively fetch buffers from the database that the generator may
            subsequently be called upon to yield.
        
        Similarly genAnzLogMeta(logtype) is an accessor for the analyzer log metadata.
    
    The resulting generators yield tuples consisting of the epoch time and a document from the collection 
    which lie within the range of rows startPos through endPos. If the endPos argument is omitted, 
    the generator does not terminate, but yields None if there are no documents yet available from the 
    collection"""
    
    def __init__(self,alog):
        self.csp = "https://dev.picarro.com/node"
        self.svc = "gdu"
        self.alogName = alog
        #self.discardList = ["EPOCH_TIME", "LOGTYPE", "FILENAME_nint", "_id", "SERVER_HASH", "row"]
        #self.discardList = ["LOGTYPE", "FILENAME_nint", "_id", "SERVER_HASH"]
        self.discardList = ["FILENAME_nint", "_id", "SERVER_HASH"]
        self.getTicket()
        
    def getTicket(self):
        # Version and Resource
        v_rsc = "1.0/Admin"
        qry = "issueTicket"
        sys = "APITEST"
        svc = "sec"
        identity = "85490338d7412a6d31e99ef58bce5de6"
        ticket = "dummy"
        rprocs = '["AnzLog:byPos"]'
        get_url = '%s/%s/%s/%s/%s?qry=%s&sys=%s&identity=%s&rprocs=%s' %(self.csp, "rest", svc, ticket, v_rsc, qry, sys, identity, rprocs)
        # print "GET URL: %s"  % get_url

        params = {"qry": qry, "sys": sys, "identity": identity, "rprocs": rprocs}
        post_url = '%s/%s/%s/%s/%s' %(self.csp, "rest", svc, ticket, v_rsc)
        print "POST URL: %s"  % post_url

        while True:
            try:
                resp = urllib2.urlopen(post_url, data=urllib.urlencode(params))
                rtndata_str = resp.read()
                print "POST Response: %s: %s" % (resp.code, rtndata_str)
                break
            except urllib2.URLError,e:
                print "Error: ", e
                time.sleep(1.0)
                print "Retrying..."
            
        rtndata = json.loads(rtndata_str)
        print "rtndata", rtndata

        if "ticket" in rtndata:
            self.ticket = rtndata["ticket"]
        else:
            self.ticket = None
        return rtndata
    
    def _genCore(self,params,v_rsc,lwm=500):
        """Generator which yields PosTuples from the specified P3 server url, passing in the
        parameters as the dictionary "params". Documents are fetched in non-decreasing order of
        epoch times, lying between params["startPos"] and params["endPos"], and the generator raises 
        StopIteration after all matching documents are yielded. 
        However, if params does not contain "endPos", this indicates we are accessing a continually 
        updating live archive, and the generator will yield None while no more matching documents 
        are present.
       
        Data from MongoDB are fetched from the server in blocks of up to params["limit"] documents
        at a time. The log type is specified as params["logtype"] and returned documents are filtered
        to exclude those which contain LOGTYPE keys which do not match this specification. 
        N.B. "limit" is NOT the maximum number of documents to be retrieved by the generator.
        
        When documents are returned, any keys which lie in self.discardList are removed.
        
        We detect when there are no (more) data on the server when it raises a 404 error.
        
        "lwm" indicates a low-water mark, when there are fewer than this number of documents in 
        the buffer, a new buffer is fetched
        """
        threadDict = dict(thread=None,start=None,latestPos=0)
        resultQueue = Queue.Queue()
        def fetchBuffer():
            # Fetch the next buffer's worth of data from P3. To be executed in a thread
            # Write the result or an uncaught exception into resultQueue
            paramStr = urllib.urlencode(params)
            while True:
                try:
                    tstart = time.clock()
                    url = '%s/%s/%s/%s/%s' % (self.csp, "rest", self.svc, self.ticket, v_rsc)
                    get_url = url+("?%s" % paramStr if params else "")
                    print get_url
                    resp = urllib2.urlopen(get_url,timeout=5.0)
                    rtndata_str = resp.read()
                    # Only push rows which are of the correct logtype
                    startPos = params["startPos"]
                    for drow in json.loads(rtndata_str):
                        if ('LOGTYPE' in drow) and (drow['LOGTYPE'] != params["logtype"]): continue
                        row = drow['row']
                        # We make a copy so that drow can be used to check for duplicate rows
                        drowCopy = drow.copy()
                        for d in self.discardList: 
                            if d in drowCopy: del drowCopy[d]
                        resultQueue.put((row,drowCopy))
                        if row>= params["endPos"]-1: break
                    threadDict["latestPos"] = row
                    print "P3 get from %s, %.1f s, startTime %.1f, lastTime %.1f" % (params["logtype"],time.clock()-tstart,params["startPos"],threadDict["latestPos"])
                    params["startPos"] = row+1    # Start at the next row
                    return
                except urllib2.URLError,e:
                    if not hasattr(e,"code") or e.code in [502,504]: # Bad gateway, gateway timeout
                        print "%s: retrying" % e
                        time.sleep(1.0)
                        continue
                    elif e.code == 404:   # Not found
                        return
                    elif e.code == 403:   # Forbidden, get new ticket
                        print "Permission denied, getting a new ticket"
                        self.getTicket()
                    else:
                        print e
                        print traceback.format_exc()
                        resultQueue.put(e)
                except Exception,e:
                    print traceback.format_exc()
                    resultQueue.put(e)
                    
        while True:
            if resultQueue.empty(): # We must initiate a fetch unless one is in progress
                print "*** Result Queue is empty"
                if threadDict["thread"] is None or not threadDict["thread"].isAlive():
                    if params["startPos"] < params["endPos"]:
                        threadDict["thread"] = threading.Thread(target=fetchBuffer)
                        threadDict["thread"].setDaemon(True)
                        threadDict["start"] = time.clock()
                        threadDict["thread"].start()
                    else:
                        threadDict["thread"] = None
                # We must wait for the thread to complete and then yield the document    
                if threadDict["thread"]: 
                    threadDict["thread"].join()
                if resultQueue.empty(): # Nothing there, either yield None or return to raise StopIteration
                    if "endPos" in params: 
                        return
                    else:
                        reqRow = yield None
                else: # Return the next available document
                    d = resultQueue.get()
                    if isinstance(d,Exception): 
                        print traceback.format_exc()
                        raise d
                    row,drow = d
                    reqRow = yield PosTuple(row, threadDict["latestPos"], drow)
            else:
                d = resultQueue.get()
                # Check that:
                #  a) no fetch is in progress, 
                #  b) the queue length is below the low-water mark, and 
                #  c) it has been at least two seconds since the last fetch 
                # If so initiate another fetch in the background
                if (threadDict["thread"] is None or not threadDict["thread"].isAlive()) and (resultQueue.qsize()<lwm) and (time.clock()-threadDict["start"]>2.0):
                    if params["startPos"] < params["endPos"]:
                        threadDict["thread"] = threading.Thread(target=fetchBuffer)
                        threadDict["thread"].setDaemon(True)
                        threadDict["start"] = time.clock()
                        threadDict["thread"].start()
                    else:
                        threadDict["thread"] = None
                if isinstance(d,Exception):
                    print traceback.format_exc()
                    raise d
                row,drow = d
                reqRow = yield PosTuple(row, threadDict["latestPos"], drow)
            if reqRow is not None:
                # We have a hint as to the row at which the data are required
                if reqRow > threadDict["latestPos"]:
                    if (threadDict["thread"] is not None) and (threadDict["thread"].isAlive()):
                        threadDict["thread"].join()
                        if reqRow > threadDict["latestPos"]:
                            print "Emptying prefetch queue"
                            # Empty out the queue and specify new start time
                            while not resultQueue.empty(): resultQueue.get() 
                            params["startPos"] = max(row,reqPos)
                
    def genAnzLog(self,logtype):
        def _genAnzLog(startEtm,endEtm=None,limit=500,**kwds):
            get_params = dict(qry="byPos",alog=self.alogName,limit=limit,startPos=startPos,logtype=logtype)
            if kwds: get_params.update(kwds)
            if endPos is not None: get_params["endPos"] = endPos
            return self._genCore(get_params,v_rsc="1.0/AnzLog",lwm=limit)
        return _genAnzLog
                
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
        
    def __init__(self,accessor,name,endEtm=None,maxGap=2.0,maxStore=10,limit=500):
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
        self.name = name
        
    def getNext(self,reqEtm=None):
        """Gets a datum from the generator (if available) and adds it to the deque. Length of
        deque is always kept no greater than self.maxStore. Returns True if a point was added 
        to the deque. The argument reqEtm may be used to indicate the epoch time at which the
        data are required. The generator may use this to flush its buffer if the requested time
        is too far away from the available data."""
        if self.generator is None:     # or (reqEtm-self.latestEtm)>self.maxGap:
            startEtm = reqEtm - self.maxGap
            self.generator = self.accessor(startEtm,self.endEtm,limit=self.limit)
            reqEtm = None
        d = self.generator.send(reqEtm)
        if d is None:
            return False
        self.oldData.append((d.etm,d.data))
        self.latestEtm = d.latestEtm
        self.currentEtm = d.etm
        if len(self.oldData) > self.maxStore:
            self.oldData.popleft()
        return True

    def getData(self,reqEtm):
        """
        Get data at epoch time "reqEtm" using linear interpolation. If the data is not a numeric quantity,
        return NOT_A_NUMBER if we have to interpolate between two unequal values, or the common value if
        the value in the closest rows on each side of reqEtm are the same.
        """
        #if self.latestEtm < reqEtm:
        #    print "Starting a new generator", self.name, self.latestEtm, reqEtm
        #    startEtm = reqEtm - self.maxGap
        #    self.generator = self.accessor(startEtm,self.endEtm,limit=self.limit)
        #    if not self.getNext():
        #        raise P3NoDataYet(reqEtm)
        while self.currentEtm <= reqEtm:
            if not self.getNext(reqEtm):
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
                    elif data[k]==savedData[k]:
                        result[k] = data[k]
                    else:
                        result[k] = NOT_A_NUMBER
                return result
            else:
                savedEtm = etm
                savedData = data
        else:
            firstEtm,firstData = self.oldData[0]
            raise P3NoDataUntil(firstEtm)

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
        #  n is advanced as necessary to retrieve data available from all source           
        while True:
            results = []
            for s,o in zip(self.sourceList,self.offsetList):
                try:
                    results.append(s.getData(self.startEtm+o))
                except StopIteration,e:
                    return
                except P3NoDataYet:
                    yield None
                except P3SourceGap,e:
                    self.startEtm += self.interval*math.ceil((e.value-o-self.startEtm)/self.interval)
                    break
                except P3NoDataUntil,e:
                    self.startEtm += self.interval*math.ceil((e.value-o-self.startEtm)/self.interval)
                    break
            else:
                yield self.startEtm,results
                self.startEtm += self.interval
                
if __name__ == "__main__":
    p3 = P3_Accessor("FCDS2006")
    
    #startEtm = calendar.timegm(time.strptime("2012-03-23T02:30:00","%Y-%m-%dT%H:%M:%S"))
    #endEtm   = calendar.timegm(time.strptime("2012-03-23T03:00:00","%Y-%m-%dT%H:%M:%S"))

    startEtm = calendar.timegm(time.strptime("2012-03-23T02:04:30","%Y-%m-%dT%H:%M:%S"))
    endEtm   = calendar.timegm(time.strptime("2012-03-23T04:00:00","%Y-%m-%dT%H:%M:%S"))
    
    for i,m in enumerate(p3.genAnzLog("peaks")(startEtm=startEtm,endEtm=endEtm)):
        print i,m
        raw_input()
    sys.exit()
        
    # for i,m in enumerate(p3.genAnzLogMeta("peaks")(startEtm=startEtm,endEtm=endEtm)):
        # alog = m.data["LOGNAME"]        
        # acc = P3_Accessor_ByPos(alog)
        # print "Starting to access", alog
        # for p in acc.genAnzLog("peaks")(startPos=0,endPos=5000):
            # print p
            # raw_input()

    
    # etmLast = None
    # for d in p3.genAnalyzerData(startEtm,limit=20):
    #     print d
    #     if etmLast == d.etm:
    #         raw_input()
    #     etmLast = d.etm
        
    # endEtm = 1332491271
    #analyzerSource = P3_Source(p3.genAnzLog("dat"),"analyzerSource",endEtm=endEtm,limit=100)
    #gpsSource = P3_Source(p3.genAnzLog("GPS_Raw"),"gpsSource",endEtm=endEtm,limit=100)
    #wsSource = P3_Source(p3.genAnzLog("WS_Raw"),"wsSource",endEtm=endEtm,limit=100)
        
    
    # startEtm = calendar.timegm(time.strptime("2012-03-23T08:20:00","%Y-%m-%dT%H:%M:%S"))
    # startEtm = calendar.timegm(time.strptime("2012-03-23T02:00:00","%Y-%m-%dT%H:%M:%S"))
    # startEtm = 0
    # startEtm = 1332463740
    syncSource = SyncSource([gpsSource,wsSource,wsSource],[0.0,0.0,1.5],interval=240.0,startEtm=startEtm)
    # syncSource = SyncSource([gpsSource,wsSource],[0.0,0.0],interval=60.0,startEtm=startEtm)
    tstart = time.clock()
    for i,d in enumerate(syncSource.generator()):
        print i,time.clock()-tstart,d
        # raw_input()
        tstart = time.clock()
    #startEtm = calendar.timegm(time.strptime("2012-03-23T00:48:59","%Y-%m-%dT%H:%M:%S"))
    #endEtm   = calendar.timegm(time.strptime("2012-03-23T01:18:59","%Y-%m-%dT%H:%M:%S"))
    #startEtm = calendar.timegm(time.strptime("2012-03-23T02:00:00","%Y-%m-%dT%H:%M:%S"))
    #endEtm   = calendar.timegm(time.strptime("2012-03-23T03:00:00","%Y-%m-%dT%H:%M:%S"))
    #for i,dat in enumerate(p3.genAnalyzerData(startEtm,endEtm)):
