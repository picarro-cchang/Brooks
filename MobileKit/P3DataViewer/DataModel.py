#!/usr/bin/python
"""
File Name: DataModel.py
Purpose: Model for analyzer log data fetched from PCubed

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from threading import Timer
from P3Access import P3Access
from Subject import Subject

class DataModel(Subject):
    """Model for analyzer log data fetched from PCubed.

    Args:
        p3Access: P3Access object for communicating with PCubed.
    """
    parameterSetIndex = 0

    def __init__(self, p3Access):
        assert isinstance(p3Access, P3Access)
        Subject.__init__(self)
        self.analyzers = None
        self.analyzer = None
        self.logName = None
        self.logFileId = None
        self.analyzerLogs = None
        self.logMetaData = None
        self.logVars = None
        self.logData = None
        self.lastException = None
        self.changed = ""
        self.p3Access = p3Access
        self.p3Failures = 0

        self.startPos = None
        self.batchSize = None
        
    def newParameterSetIndex(self):
        """Gets next parameter set index.

        A new parameterSetIndex is generated whenever any of the parameters which affect
        getting of data logs change. By checking the value, it is possible to decide whether
        to continue getting more data.
        """
        DataModel.parameterSetIndex += 1
        return DataModel.parameterSetIndex

    def outputQueueHandler(self):
        while not self.p3Access.outputQueue.empty():
            func, result, ident = self.p3Access.outputQueue.get()
            func(result, ident)

    def failed(self, exc, index):
        """Callback when an exception is raised.

        Args:
            exc: Exception object returned from P3Access method call
        """
        self.set("lastException", "Error fetching data from PCubed", True)
        self.set("p3Failures", self.p3Access.numFails)
        Timer(10.0, self.recoverFromP3Error, (), {}).start()
    
    def recoverFromP3Error(self):
        self.p3Access.inputQueue.put((self.p3Access.getAnalyzerList,(),{},
                                      self.newParameterSetIndex(),
                                      self.recoverFromP3Success, 
                                      self.failed))
        
    def recoverFromP3Success(self, analyzerList, index):
        """Success callback when fetching list of analyzers after P3 failure

        Args:
            analyzerList: List of analyzers in the environment
        """
        self.set("p3Failures", self.p3Access.numFails)
        self.set("analyzer", None)
        self.set("logName", None)
        self.set("logFileId", None)
        self.set("analyzerLogs", None)
        self.set("logMetaData", None)
        self.set("logVars", None)
        self.set("logData", None)
        self.set("analyzers", analyzerList, True)
        
    def getAnalyzers(self):
        """Gets analyzers available in the environment.
        """
        self.p3Access.inputQueue.put((self.p3Access.getAnalyzerList,(),{},
                                      self.newParameterSetIndex(),
                                      self.getAnalyzerListSuccess, 
                                      self.failed))
        
    def getAnalyzerListSuccess(self, analyzerList, index):
        """Success callback when fetching list of analyzers.

        Args:
            analyzerList: List of analyzers in the environment
        """
        self.set("analyzers", analyzerList)
    
    def getAnalyzerLogs(self, analyzer, limit=10):
        """Set the analyzer and get its logs.

        The most recent logs are fetched in reverse time order.

        Args:
            analyzer: Name of analyzer
            limit: Maximum number of logs to fetch
        """
        parameterSetIndex = self.newParameterSetIndex()
        assert analyzer in self.analyzers
        self.set("analyzer", analyzer)
        self.set("logName", None)
        self.set("logFileId", None)
        self.set("analyzerLogs", None)
        self.set("logMetaData", None)
        self.set("logVars", None)
        self.set("logData", None)
        self.p3Access.inputQueue.put((self.p3Access.getLogFiles, (),
                                      dict(analyzer=analyzer, limit=limit),
                                      parameterSetIndex,
                                      self.getAnalyzerLogsSuccess,
                                      self.failed))

    def getAnalyzerLogsSuccess(self, result, index):
        """Success callback when fetching list of analyzer logs.

        Args:
            result: tuple consisting of (analyzer, analyzerLogs)
        """
        analyzer, analyzerLogs = result
        self.set("analyzerLogs", analyzerLogs)
        
    def getAnalyzerLog(self, logName, startPos=0, batchSize=500):
        """Set the logName, fetch associated metadata and data.

        This gets the metadata and asynchronously calls getAnalyzerMetadataSuccess
            if it completes successfully.

        Args:
            logName: Name of analyzer log to fetch or @@Live:<analyzer>
            startPos: Row at which to start fetching log
            batchSize: Maximum number of rows to fetch on each PCubed query
        """
        parameterSetIndex = self.newParameterSetIndex()
        assert logName.startswith("@@Live:") or logName in self.analyzerLogs
        self.startPos = startPos
        self.batchSize = batchSize
        self.set("logName", logName)
        self.set("logMetaData", None)
        self.set("logVars", None)
        self.set("logData", None)
        self.p3Access.inputQueue.put((self.p3Access.getLogMetadata, (),
                                      dict(alog=logName),
                                      parameterSetIndex,
                                      self.getAnalyzerMetadataSuccess,
                                      self.failed))
        
    def getAnalyzerMetadataSuccess(self, result, index):
        """Success callback when fetching metadata for a log.

        Sets the logMetaData and logVars model variables, then calls P3Access
            getLogByPos method to fetch first set of rows of log data.

        Args:
            result: tuple consisting of (logName, metadata)
        """
        if self.parameterSetIndex != index: 
            return
        alog, metadata = result
        docmap = metadata['docmap'][0]
        logFileId = metadata["FILENAME_nint"][0]
        self.set("logMetaData", metadata)
        self.set("logFileId", logFileId)        
        self.set("logVars", sorted(docmap.keys()))
        self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                      dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                      index,
                                      self.getLogByPosSuccess, 
                                      self.failed))

    def getLogMore(self, alog, index):
        """Called to get more rows from the log file when there was no data on the last call
        """
        if self.parameterSetIndex != index: 
            return
        if alog.startswith("@@Live:"):
            # Make metadata call to see if we have a new log
            self.p3Access.inputQueue.put((self.p3Access.getLogMetadata, (),
                                          dict(alog=alog),
                                          index,
                                          self.checkNewLogfileSuccess,
                                          self.failed))
        else:
            # Try getting more data
            self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                          dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                          index,
                                          self.getLogByPosSuccess, 
                                          self.failed))

    def checkNewLogfileSuccess(self, result, index):
        if self.parameterSetIndex != index: 
            return
        alog, metadata = result
        logFileId = metadata["FILENAME_nint"][0]
        if self.logFileId != logFileId:
            # This is a new log file
            docmap = metadata['docmap'][0]
            self.set("logMetaData", metadata)
            self.set("logVars", sorted(docmap.keys()))
            self.set("logFileId", logFileId)
            self.set("logData", None)
            self.startPos = 0
            index = self.newParameterSetIndex()
        # Get the next chunk of data
        self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                      dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                      index,
                                      self.getLogByPosSuccess, 
                                      self.failed))
        
    def getLogByPosSuccess(self, result, index):
        """Success callback when fetching rows from a data log.

        Extends the logData model variable, then tries to get more data.
            If the most recent fetch returned no rows, the subsequent fetch
            is delayed by 5s. If the log name has changed since the request
            was enqueued, discard the data received.

        TODO: What happens when user restarts the data log and we have selected "live"?

        Args:
            result: tuple consisting of (logName, metadata)
        """
        if self.parameterSetIndex != index: 
            return
        if self.logData is None:
            self.logData = {}
        alog, logData = result

        if "FILENAME_nint" in logData:
            logFileId = set(logData["FILENAME_nint"])
            assert len(logFileId) == 1, "Did not expect file ids %s in log data" % logFileId
            if self.logFileId != logFileId.pop():
                print "Log restart detected by changing logFileId"
                # Make metadata call to get information about the new log
                self.p3Access.inputQueue.put((self.p3Access.getLogMetadata, (),
                                              dict(alog=alog),
                                              index,
                                              self.checkNewLogfileSuccess,
                                              self.failed))
                return
        for var in logData:
            if var not in self.logData:
                self.logData[var] = []
            self.logData[var].extend(logData[var])
        newStartPos = self.logData["row"][-1] + 1
        
        if self.startPos == newStartPos:
            Timer(5.0, self.getLogMore, (), dict(alog=alog,index=index)).start()
        else:
            self.set("logData", self.logData, force=True)
            self.startPos = newStartPos
            self.p3Access.inputQueue.put((self.p3Access.getLogByPos,(),
                                          dict(alog=alog, startPos=self.startPos, limit=self.batchSize),
                                          index,
                                          self.getLogByPosSuccess, 
                                          self.failed))
