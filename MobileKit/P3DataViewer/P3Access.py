#!/usr/bin/python
"""
File Name: P3Access.py
Purpose: Allows serialized access to PCubed with input and output queues 
    and a worker executing in a thread

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from P3RestApi import P3RestApi
from Queue import Queue
import threading

class P3Access(object):
    def __init__(self, authentication):
        restP = {}
        restP['host'] = authentication["Host"]
        restP['port'] = authentication["Port"]
        restP['site'] = authentication["Site"]
        restP['identity'] = authentication["Identity"]
        restP['psys'] = authentication["Sys"]
        restP['svc'] = 'gdu'
        restP['debug'] = False
        restP['version'] = '1.0'
        
        restP['resource'] = 'AnzMeta'
        restP['rprocs'] = ["AnzMeta:byAnz"]
        self.anzMeta = P3RestApi(**restP)
        
        restP['resource'] = 'AnzLogMeta'
        restP['rprocs'] = ["AnzLogMeta:byEpoch"]
        self.anzLogMeta = P3RestApi(**restP)
        
        restP['resource'] = 'AnzLog'
        restP['rprocs'] = ["AnzLog:byEpoch", "AnzLog:byPos"]
        self.anzLog = P3RestApi(**restP)
        
        restP['resource'] = 'GduService'
        restP['rprocs'] = ["GduService:runProcess", "GduService:getProcessStatus"]
        self.gduService = P3RestApi(**restP)
        
        self.inputQueue = Queue(0)
        self.outputQueue = Queue(0)
        self.workerThread = threading.Thread(target=self.worker)
        self.workerThread.setDaemon(True)
        self.workerThread.start()
        self.numFails = 0
        
    def worker(self):
        """Performs unit of work from input queue by calling a method and enqueuing result.

        The entries on the input queue are tuples with following elements:
            func: Method to call
            args: Positional arguments for method
            kwargs: Keyword arguments for method
            ident: Identification that is passed through to output
            onSuccess: Callback function for success, called with result and ident
            onFail: Callback function for failure, called with exception and ident
        """
        assert isinstance(self.inputQueue, Queue)
        while True:
            func, args, kwargs, ident, onSuccess, onFail = self.inputQueue.get()
            try:
                result = func(*args, **kwargs)
                self.outputQueue.put((onSuccess, result, ident))
                self.numFails = 0
            except Exception, exc:
                self.numFails += 1
                self.outputQueue.put((onFail, exc, ident))
        
    def getAnalyzerList(self):
        res = self.anzMeta.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'doclist':True}})
        return res[1]['result']['ANALYZER']
    
    def getLogFiles(self, analyzer, limit=10):
        res = self.anzLogMeta.get({'existing_tkt':True, 
                                   'qryobj':{'qry':'byEpoch', 'doclist':True, 'anz':analyzer,
                                             'startEtm':0, 'endEtm':2000000000, 'logtype':'dat', 
                                             'limit':limit, 'reverse':True }})
        if res[1]['result']:
            return analyzer, res[1]['result']['name']
        else:
            return analyzer, []
        
    def getLogMetadata(self, alog):
        res = self.anzLogMeta.get({'existing_tkt':True, 
                                   'qryobj':{'qry':'byEpoch', 'alog':alog, 'startEtm':0,
                                             'logtype':'dat', 'limit':1, 'doclist':True}})
        result = res[1]['result']
        return alog, result
    
    def getLogByPos(self, alog, startPos, limit=500):
        res = self.anzLog.get({'existing_tkt':True, 
                          'qryobj':{'alog':alog, 
                                    'qry':'byPos', 'doclist':True, 'logtype':'dat', 
                                    'startPos':startPos, 'limit':limit}})        
        result = res[1]['result']
        return alog, result
