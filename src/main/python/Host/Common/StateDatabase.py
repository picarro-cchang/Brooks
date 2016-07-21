#!/usr/bin/python
"""
FILE:
  StateDatabase.py

DESCRIPTION:
  Allows saving of analyzer state and sensor history in an sqlite3 database 

SEE ALSO:
  Specify any related information.

HISTORY:
  29-Nov-2013  sze  Extracted from analyzerUsbIf

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import copy
from ctypes import c_float
import Queue
import sqlite3
import sys
import threading

from Host.autogen import interface
from Host.Common.SharedTypes import lookup, Singleton, StateDatabaseError

# We are not allowed to access an sqlite3 database for write from multiple threads in NTFS.
#  We thus create a handler running in a single thread which services requests enqueued
#  from multiple clients. On the read side, we make the function block until the data are
#  available. In order to maintain the correct sequence of reads, a lock is used to serialize them.


def protectedRead(func):
    """Decorator for methods that read from the database. 

    The decorated method is protected by an RLock and executed in a separate thread.
        Communication with the database is serialized via a transmit and a receive queue.
    """

    def wrapper(self, *args):
        """Wraps function to execute in thread.
        """
        def _func(*args):
            """Create a closure around the method func.
            """
            return func(self, *args)
        self.dbLock.acquire()
        txId = self.getId()
        self.safeTxQueuePut((txId, _func, args))
        while True:
            rxId, exc, result = self.rxQueue.get()
            self.dbLock.release()
            if exc: # This may be from the current read, or from some previous writes
                raise exc
            if rxId == txId:
                break
            else:
                self.logFunc("Unexpected ID when fetching result from database", Level=2)
        return result
    return wrapper


class StateDatabase(Singleton):

    """Database for storing state of the CRDS analyzer.

    This is a Singleton which may be accessed after initial creation simply by calling
        StateDatabase().

    Args:
        fileName: File for sqlite3 database
        logFunc: Function used for logging messages
    """

    periodByLevel = [10.0, 100.0, 1000.0, 10000.0]
    initialized = False
    txId = 0

    def __init__(self, fileName=None, logFunc=None):
        if not self.initialized:
            self.fileName = fileName
            self.con = None
            self.dbLock = threading.Lock()
            self.txQueueSizeLimit = 50
            self.rxQueueSizeLimit = 50
            self.txQueue = Queue.Queue(self.txQueueSizeLimit)
            self.rxQueue = Queue.Queue(self.rxQueueSizeLimit)
            self.maxTxQueueSize = 0
            self.maxRxQueueSize = 0
            self.stopThread = threading.Event()
            self.hThread = threading.Thread(target=self.txQueueHandler)
            self.hThread.setDaemon(True)
            self.hThread.start()
            self.initialized = True
            self.lastTimeCheckWlmHist = None
            self.logFunc = logFunc
            # Max size for WLM history table is 180 days
            self.wlmHistMaxTime_s = 15552000
            # Check WLM History table size and delete old data every 30 minutes
            self.wlmHistCheckPeriod_s = 1800
        elif fileName is not None:
            raise ValueError("StateDatabase has already been initialized")

    def myLog(self, *args, **kwargs):
        """Logs messages via the optionally specified logfunc
        """
        if self.logFunc is not None:
            return self.logFunc(*args, **kwargs)

    def checkInitialized(self):
        if not self.initialized:
            raise ValueError("Cannot execute when database is closed")

    def close(self):
        self.stopThread.set()
        self.hThread.join()
        self.initialized = False

    @staticmethod    
    def getId():
        """Get next ID for a database request.

        Should be called while holding dbLock.
        """
        StateDatabase.txId += 1
        return StateDatabase.txId

    def safeTxQueuePut(self, txCmd):
        """Submit a command onto the transmit queue.

        Args:
            txCmd: Function to be executed for the command.
        """
        try:
            self.txQueue.put_nowait(txCmd)
            txQueueSize = self.txQueue.qsize()
            if txQueueSize > self.maxTxQueueSize:
                self.maxTxQueueSize = txQueueSize
                self.myLog("StateDatabase tx queue new max size = %d while executing (%s, %s)" % 
                           (txQueueSize, txCmd[0], txCmd[1]), Level=1)
                if txQueueSize == self.txQueueSizeLimit:
                    self.myLog("StateDatabase tx queue has reached the max size limit while executing (%s, %s)" % 
                               (txCmd[0], txCmd[1]), Level=2)
        except Queue.Full:
            self.myLog("Put on database txQueue failed.")

    def safeRxQueuePut(self, rxData):
        """Place the results of executing a command onto the receive queue

        Args:
            rxData: Data to be sent back, typically a tuple consisting of the command Id,
                the result of executing the command and any exception.
        """
        try:
            self.rxQueue.put_nowait(rxData)
            rxQueueSize = self.rxQueue.qsize()
            if rxQueueSize > self.maxRxQueueSize:
                self.maxRxQueueSize = rxQueueSize
                self.myLog("StateDatabase rx queue new max size = %d" % rxQueueSize, Level=1)
                if rxQueueSize == self.rxQueueSizeLimit:
                    self.myLog("StateDatabase rx queue has reached the max size limit", Level=2)
        except Queue.Full:
            self.myLog("Put on database rxQueue failed.")

    def saveFloatRegList(self, floatList):
        """Save a list of (name,value) pairs in the floating point register table.

        Returns immediately after submitting request to the transmit queue.

        Args:
            floatList: A list of tuples (regName, value) to be saved
        """
        def _saveFloatRegList(floatList):
            """SQL command to save list of registers to the dasRegFloat table.
            """ 
            self.con.executemany("insert or replace into dasRegFloat values (?,?)", floatList)
            self.con.commit()
        self.safeTxQueuePut((self.getId(), _saveFloatRegList, [copy.copy(floatList)]))

    def saveIntRegList(self, intList):
        """Save a list of (name,value) pairs in the integer register table.

        Returns immediately after submitting request to the transmit queue.

        Args:
            intList: A list of tuples (regName, value) to be saved
        """
        def _saveIntRegList(intList):  # pylint: disable=C0111
            self.con.executemany("insert or replace into dasRegInt values (?,?)", intList)
            self.con.commit()
        self.safeTxQueuePut((self.getId(), _saveIntRegList, [copy.copy(intList)]))

    def saveWlmHist(self, wlmHist):
        """Save WLM parameters into the WLM History table."""
        def _saveWlmHist(*wlmHist):  # pylint: disable=C0111
            self.con.execute("insert into wlmHistory values (?,?,?,?,?,?,?)", wlmHist)
            # Maintain database size based on timestamp
            timestamp = wlmHist[0]
            if self.lastTimeCheckWlmHist == None:
                self.lastTimeCheckWlmHist = timestamp
            elif timestamp - self.lastTimeCheckWlmHist > self.wlmHistCheckPeriod_s * 1000:
                cutoffTime = timestamp - self.wlmHistMaxTime_s * 1000
                self.con.execute("delete from wlmHistory where timestamp<=?", (cutoffTime,))
                self.lastTimeCheckWlmHist = timestamp
            else:
                pass
            self.con.commit()
        self.safeTxQueuePut((self.getId(), _saveWlmHist, wlmHist))

    def saveRegList(self, regList):
        """Save a list of (name,value) pairs in the appropriate register table"""
        floatList = []
        intList = []
        for reg, value in regList:
            reg = lookup(reg)
            regInfo = interface.registerInfo[reg]
            if regInfo.type == c_float:
                floatList.append((regInfo.name, value))
            else:
                intList.append((regInfo.name, value))
        self.saveFloatRegList(floatList)
        self.saveIntRegList(intList)

    def writeSnapshot(self, level, sensors, minSensors, maxSensors, sumSensors, pointsInSum, maxIdx):
        """Write the current snapshot to the database"""
        # pylint: disable=C0111
        def _writeSnapshot(level, sensors, minSensors, maxSensors, 
                           sumSensors, pointsInSum, maxIdx):  
            maxRows = 1024
            if maxIdx[level] < 0:
                values = self.con.execute(
                    "select max(idx) from history where level=?",
                    (level,)).fetchall()
                maxIdx[level] = values[0][0]
                if maxIdx[level] is None:
                    maxIdx[level] = -1
            if sensors:
                maxIdx[level] += 1
                dataList = []
                for streamNum in sensors:
                    timestamp, value = sensors[streamNum]
                    minVal = minSensors.get(streamNum, value)
                    maxVal = maxSensors.get(streamNum, value)
                    average = sumSensors.get(streamNum, value) / pointsInSum.get(streamNum, 1)
                    dataList.append((level, timestamp, streamNum, average, minVal,
                                     maxVal, maxIdx[level]))
                self.con.executemany(
                    "insert into history values (?,?,?,?,?,?,?)", dataList)

                if maxIdx[level] % 10 == 0:
                    self.con.execute("delete from history where level=? and idx<=?",
                                    (level, maxIdx[level] - maxRows))
                self.con.commit()
        self.safeTxQueuePut((self.getId(), _writeSnapshot, [level, sensors.copy(), minSensors.copy(), maxSensors.copy(),
                                                            sumSensors.copy(), pointsInSum.copy(), copy.copy(maxIdx)]))

    @protectedRead
    def getFloatRegList(self):
        """Fetch all floating point registers in the database.
        """
        return self.con.execute("select * from dasRegFloat").fetchall()

    @protectedRead
    def getFloatReg(self, regName):
        """Get a specific floating point register by name from the database
        
        Args:
            regName: Name of the register
            
        Returns: Floating point value of register
        """
        values = self.con.execute(
            "select value from dasRegFloat where name=?", (regName,)).fetchall()
        if len(values) != 1:
            raise IndexError("Cannot access %s" % regName)
        else:
            return values[0][0]

    @protectedRead
    def getIntRegList(self):
        """Fetch all integer registers in the database
        """
        return self.con.execute("select * from dasRegInt").fetchall()

    @protectedRead
    def getIntReg(self, regName):
        """Get a specific integer register by name from the database
        
        Args:
            regName: Name of the register
            
        Returns: Integer value of register
        """
        values = self.con.execute(
            "select value from dasRegInt where name=?",
            (regName,)).fetchall()
        if len(values) != 1:
            raise KeyError("Cannot access %s" % regName)
        else:
            return values[0][0]

    @protectedRead
    def getHistory(self, streamNum):
        """Get the history for one sensor from the database
        
        Args:
            streamNum: Stream number for the sensor
        Returns:
            List of tuples containing time, value, level, minVal and maxVal
        """
        values = self.con.execute(
            "select time,value,level,minVal,maxVal from history" +
            " where streamNum=?",
            (streamNum,)).fetchall()
        return values

    @protectedRead
    def getHistoryByCommand(self, command, args=None):
        """Get data from database by injecting a command and arguments
        
        Args:
            command: SQL command with ? for arguments
            args: Arguments to fill out SQL command
        """
        argsTuple = (args,) if args is not None else ()
        values = self.con.execute(command, *argsTuple).fetchall()
        return values

    def txQueueHandler(self):
        """Creates the connection to the database and services the queue of requests"""
        self.con = sqlite3.connect(self.fileName)
        try:
            tableNames = [s[0] for s in self.con.execute("select tbl_name from sqlite_master where type='table'").fetchall()]
            if not tableNames:
                if sys.version_info < (2,7):
                    self.con.execute("pragma auto_vacuum=FULL")
                else:
                    self.con.execute("pragma journal_mode=WAL")
            if "dasRegInt" not in tableNames:
                self.con.execute("create table dasRegInt (name text primary key,value integer)")
            if "dasRegFloat" not in tableNames:
                self.con.execute("create table dasRegFloat (name text primary key,value real)")
            if "wlmHistory" not in tableNames:
                self.con.execute("create table wlmHistory (timestamp integer," +
                                 "vLaserNum integer, wlmOffset real," +
                                 "freqMin real, valMin real, freqMax real, valMax real)")
            if "history" not in tableNames:
                self.con.execute(
                    "create table history (level integer," +
                    "time integer,streamNum integer,value real," +
                    "minVal real,maxVal real,idx integer)")
            self.con.commit()
            while not self.stopThread.isSet():
                try:
                    txId,func,args = self.txQueue.get(timeout=0.5)
                except Queue.Empty: # See if we need to stop
                    continue
                # Place a response on rxQueue if there is a return value or if an error occurs
                #  N.B. If a tx request does not return a value but throws an exception, this will
                #  be sent back. It is up to the rxQueue handler to check that the id of the response
                #  matches that of the request, and to ignore exceptions from tx requests without
                #  responses. This is done for speed, so that tx requests can return without waiting
                #  for the database commit.
                try:
                    r = func(*args)
                    e = None
                except Exception, e:
                    pass
                if (r is not None) or (e is not None):
                    self._safeRxQueuePut((txId,e,r))
        finally:
            self.con.commit()
            self.con.close()


class SensorHistory(Singleton):
    """Manages history of sensor outputs for updating the analyzer state database.

    History is maintained at a series of levels, each associated with a particular period
        e.g. level 0 could be a period of 10s, level 1 could be a period of 100s etc.
    Time for each level is discretized into intervals with boundaries at multiples of 
        the period.
    For a given level, within each interval, we maintain the minimum, maximum,  
        average and current values of the data from each sensor.    
    """
    initialized = False

    def __init__(self):
        if not self.initialized:
            # Dictionary indexed by sensor stream ID for current sensor data
            self.latestSensors = {}
            self.periods = StateDatabase().periodByLevel
            # Lists indexed by history "level", each level having a
            #  collation period (1s, 10s, 100s, 1000s, 10000s)

            # Time at which last snapshot was written for this level
            self.lastArchived = [0 for _ in self.periods]
            # Last index for each level
            self.maxIdx = [-1 for _ in self.periods]
            # Timestamp of the most recent data seen so far
            self.mostRecent = 0
            # Following lists of dictionaries are indexed by level
            #  and then by sensor stream ID
            self.minSensors = [{} for _ in self.periods]
            self.maxSensors = [{} for _ in self.periods]
            self.sumSensors = [{} for _ in self.periods]
            self.pointsInSum = [{} for _ in self.periods]
            self.initialized = True

    @staticmethod
    def needToArchive(last, now, period):
        """Return true if there is an exact multiple of period between
        last and now"""
        return (now // period) * period > last

    def record(self, data):
        """Called to record sensor data.

        This is called whenever new sensor data arrive (Different streams have 
            different reporting periods). A new "snapshot" of the
            latest data (from all sensors) is written to the database once
            we cross a time which is a multiple of the period associated with
            each recording level.

        Args:
            data: Object of type SensorEntryType with data from one sensor.
        """
        if data.timestamp != self.mostRecent:
            # This point occured at a new time. Check if we need to write out
            #  snapshot of current data at the various levels because we have crossed
            #  an interval boundary for that level.
            for i, period_s in enumerate(self.periods):
                period_ms = int(1000 * period_s)
                if self.needToArchive(
                        self.lastArchived[i], data.timestamp, period_ms):
                    stateDatabase = StateDatabase()
                    stateDatabase.writeSnapshot(i, self.latestSensors,
                                                self.minSensors[i],
                                                self.maxSensors[i],
                                                self.sumSensors[i],
                                                self.pointsInSum[i],
                                                self.maxIdx)
                    self.lastArchived[i] = data.timestamp
                    self.minSensors[i] = {}
                    self.maxSensors[i] = {}
                    self.sumSensors[i] = {}
                    self.pointsInSum[i] = {}
            self.mostRecent = data.timestamp
        self.latestSensors[data.streamNum] = (data.timestamp, data.value)
        # Update the sensor statistics
        for i, period_s in enumerate(self.periods):
            minSensors = self.minSensors[i]
            maxSensors = self.maxSensors[i]
            sumSensors = self.sumSensors[i]
            pointsInSum = self.pointsInSum[i]
            if data.streamNum in minSensors:
                minSensors[data.streamNum] = min(minSensors[data.streamNum], data.value)
            else:
                minSensors[data.streamNum] = data.value
            if data.streamNum in maxSensors:
                maxSensors[data.streamNum] = max(maxSensors[data.streamNum], data.value)
            else:
                maxSensors[data.streamNum] = data.value
            if data.streamNum in sumSensors:
                sumSensors[data.streamNum] = sumSensors[data.streamNum] + data.value
            else:
                sumSensors[data.streamNum] = data.value
            if data.streamNum in pointsInSum:
                pointsInSum[data.streamNum] = pointsInSum[data.streamNum] + 1
            else:
                pointsInSum[data.streamNum] = 1
