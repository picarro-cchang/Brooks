#!/usr/bin/python
#
"""
File Name: ActiveFileManager.py
Purpose: Manages active HDF5 files which are still being written to by the instrument
Description: This application listens to broadcasts from the driver, ringdown frequency converter and data manager and
    stores the data in a collection of HDF5 files. These files will ultimately be sent to the archiver, but while they
    are still being written to by the instrument, we need to carefully control requests to read the data by 
    interspersing them with the writes. The active file manager runs a single thread that services the listener 
    queues which cause writes to the actve files and also handles the RPC calls which read from the files. 

File History:
    06-Jun-2010  sze       Initial version.
Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "ActiveFileManager"

import ctypes
import getopt
from glob import glob
import inspect
import numpy
import os
from Queue import Queue
import socket
import sys
import tables
import threading
import time
import traceback

from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_SENSORSTREAM, BROADCAST_PORT_DATA_MANAGER
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, RPC_PORT_DATA_MANAGER, RPC_PORT_ACTIVE_FILE_MANAGER
from Host.Common.SharedTypes import RPC_PORT_ARCHIVER
from Host.Common.SharedTypes import Singleton
from Host.Common.StringPickler import ArbitraryObject
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.timestamp import getTimestamp
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

class ArchiverProxy(Singleton):
    """Encapsulates access to the Archiver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,RPC_PORT_ARCHIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="ActiveFileManager")
            self.initialized = True

# For convenience in calling archiver functions
Archiver = ArchiverProxy().rpc
    
class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")

class ActiveFileManagerRpcHandler(Singleton):
    def __init__(self,parent):
        self.server = CmdFIFO.CmdFIFOServer(("", RPC_PORT_ACTIVE_FILE_MANAGER),
                                            ServerName = "ActiveFileManager",
                                            ServerDescription = "Manager for active instrument file",
                                            threaded = True)
        self.parent = parent    # Active file manager
        self._register_rpc_functions()

    def _register_rpc_functions_for_object(self, obj):
        """ Registers the functions in ActiveFileManagerRpcHandler class which are accessible by XML-RPC

        NOTE - this automatically registers ALL member functions that don't start with '_'.

        i.e.:
          - if adding new rpc calls, just define them (with no _) and you're done
          - if putting helper calls in the class for some reason, use a _ prefix
        """
        classDir = dir(obj)
        for s in classDir:
            attr = obj.__getattribute__(s)
            if callable(attr) and (not s.startswith("_")) and (not inspect.isclass(attr)):
                #if __debug__: print "registering", s
                self.server.register_function(attr,DefaultMode=CmdFIFO.CMD_TYPE_Blocking)

    def _register_rpc_functions(self):
        """ Registers the functions accessible by XML-RPC """
        #register the functions contained in this file...
        self._register_rpc_functions_for_object( self )
        Log("Registered RPC functions")
                    
    def getRdData(self,*a,**k):
        """ Get ringdown data specified by "varList" from "tstart" (inclusive) up to "tstop" (exclusive).
            Result is a numpy record array which is placed on the rpcResultQueue by genRdData.
            Only "active" files are used to satisfy the request since the database is expected to deal
            with files which have already been archived"""
        self.parent.rpcCommandQueue.put((self.parent.genRdData,(a,k))) 
        result = self.parent.rpcResultQueue.get()
        if isinstance(result,Exception):
            raise result
        else:
            return result
            
    def getRdDataStruct(self,*a,**k):
        """ Get "structure" of the data available from the ringdown data in the time range "tstart" (inclusive) 
        up to "tstop" (exclusive). The result is a dictionary whose keys are the column names and whose
        values are the data types of the columns.
        Only "active" files are used to satisfy the request since the database is expected to deal 
        with files which have already been archived"""
        self.parent.rpcCommandQueue.put((self.parent.genRdDataStruct,(a,k))) 
        result = self.parent.rpcResultQueue.get()
        if isinstance(result,Exception):
            raise result
        else:
            return result
            
    def getSensorData(self,*a,**k):
        """ Get sensor data specified by "streamName" from "tstart" (inclusive) up to "tstop" (exclusive).
            Result is a numpy record array which is placed on the rpcResultQueue by genSensorData.
            Only "active" files are used to satisfy the request since the database is expected to deal
            with files which have already been archived"""
        self.parent.rpcCommandQueue.put((self.parent.genSensorData,(a,k))) 
        result = self.parent.rpcResultQueue.get()
        if isinstance(result,Exception):
            raise result
        else:
            return result
            
    def getDmData(self,*a,**k):
        """ Get data manager for "mode" and "source" whose columns are specified by "varList" from 
            "tstart" (inclusive) up to "tstop" (exclusive). 
            Result is a numpy record array which is placed on the rpcResultQueue by genDmData.
            Only "active" files are used to satisfy the request since the database is expected to deal 
            with files which have already been archived"""
        self.parent.rpcCommandQueue.put((self.parent.genDmData,(a,k))) 
        result = self.parent.rpcResultQueue.get()
        if isinstance(result,Exception):
            raise result
        else:
            return result

    def getDmDataStruct(self,*a,**k):
        """ Get "structure" of the data available from the data manager in the time range "tstart" (inclusive) 
        up to "tstop" (exclusive). The result is a nested dictionary keyed by instrument mode, then by analysis
        name and finally by column name. The value is a string giving the column type. Only "active" files 
        are used to satisfy the request since the database is expected to deal with files which have already 
        been archived """
        
        self.parent.rpcCommandQueue.put((self.parent.genDmDataStruct,(a,k))) 
        result = self.parent.rpcResultQueue.get()
        if isinstance(result,Exception):
            raise result
        else:
            return result
            
    def shutdown(self):
        self.parent._shutdownRequested = True
        
        
ctype2coltype = { ctypes.c_byte:tables.Int8Col, ctypes.c_uint:tables.UInt32Col, ctypes.c_int:tables.Int32Col, 
                  ctypes.c_short:tables.Int16Col, ctypes.c_ushort:tables.UInt16Col, ctypes.c_longlong:tables.Int64Col, 
                  ctypes.c_float:tables.Float32Col, ctypes.c_double:tables.Float64Col }
        
# def recArrayExtract(A,fields):
    # """
    # Extract the list of named fields (columns) out of a numpy record array to produce
    # another. Each element of fields is either the name of a field in A or a tuple 
    # (originalName,newName) giving the original name of the field in A and the new name
    # of the field in the output array.
    # The field dtypes are copied from the source to the destination file
    # """
    # aFields = A.dtype.fields
    # oldFields = []
    # newFields = {}
    # for field in fields:
        # if isinstance(field,tuple):
            # originalName,newName = field
            # oldFields.append(originalName)
            # newFields[originalName] = newName
        # else:
            # oldFields.append(field)
            # newFields[field] = field
    # dtype = [(newFields[name],aFields[name][0]) for name in oldFields if name in aFields]
    # B = numpy.zeros(len(A),dtype=dtype)
    # for name in oldFields: 
        # if name in aFields:
            # B[newFields[name]] = A[name]
    # return B

def recArrayExtract(A,fields,fieldTypes=None):
    """
    Extract the list of named fields (columns) out of a numpy record array to produce
    another. Each element of fields is either the name of a field in A or a tuple 
    (originalName,newName) giving the original name of the field in A and the new name
    of the field in the output array.
    
    If fieldTypes is specified, it should be a list of strings with the names of the 
    dtypes associated with fields. When fieldTypes is not None, the output record array
    always has as many fields as specified by the "fields" argument, and their types are
    given by "fieldTypes". On the other hand, if fieldTypes is None, the output record 
    array only has fields that are present in the "fields" and in the original array. The
    field dtypes are copied from those of the source array.
    """
    aFields = A.dtype.fields
    oldFields = []
    newFields = {}
    for field in fields:
        if isinstance(field,tuple):
            originalName,newName = field
            oldFields.append(originalName)
            newFields[originalName] = newName
        else:
            oldFields.append(field)
            newFields[field] = field
    if fieldTypes is None:
        dt = [(newFields[name],aFields[name][0]) for name in oldFields if name in aFields]
    else:
        dt = [(newFields[name],numpy.dtype(fieldTypes[i])) for i,name in enumerate(oldFields)]
    B = numpy.zeros(len(A),dtype=dt)
    for name in oldFields: 
        if name in aFields:
            B[newFields[name]] = A[name]
    return B
    
class ActiveFile(object):
    """Objects of this class are associated with HDF5 files in the active file directory.
       The class is used to abstract away details about accessing HDF5 files."""
       
    # The following dictionaries are used to create HDF5 tables. They are initialized
    #  from the ctypes structure definitions of the corresponding broadcasts.
    Init = False
    SensorDataDescr = {}
    RdDataDescr = {}
    DmDataDescr = {}
    
    def structureToDescr(self,structure):
        descr = {}
        for name,cls in structure._fields_:
            descr[name] = (ctype2coltype[cls])()
        return descr
        
    def makeDescr(self):
        ActiveFile.SensorDataDescr = self.structureToDescr(interface.SensorEntryType)
        ActiveFile.RdDataDescr = self.structureToDescr(interface.ProcessedRingdownEntryType)
    
    def __init__(self):
        self.handle = None
        self.baseTime = None    # Base time is in ms
        self.stopTime = None
        self.archivalStartTimestamp = None
        self.compressedFilePath = None
        if not ActiveFile.Init: # Compute descriptors once
            self.makeDescr()
            ActiveFile.Init = True
        self.streamLookup = {}
        self.sensorDataTableMemo = None
        self.rdDataTableMemo = None
        
    def create(self,dirName,baseTime,stopTime):
        self.baseTime = baseTime
        self.stopTime = stopTime
        self.tsRange = "%d_%d" % (self.baseTime,self.stopTime)
        self.abspath = os.path.abspath(os.path.join(dirName,"%s.h5" % self.tsRange))
        self.handle = tables.openFile(self.abspath,"w")
        self.baseGroup = self.handle.createGroup("/","t_"+self.tsRange)
        self.baseGroup._f_setAttr("baseTime",self.baseTime)
        self.baseGroup._f_setAttr("stopTime",self.stopTime)
        t = self.handle.createTable(self.baseGroup,"sensorData",self.SensorDataDescr,expectedrows=2000000)
        t._f_setAttr("streamNames",interface.STREAM_MemberTypeDict)
        for k in interface.STREAM_MemberTypeDict:
            self.streamLookup[interface.STREAM_MemberTypeDict[k][7:]] = k 
        self.handle.createTable(self.baseGroup,"rdData",self.RdDataDescr,expectedrows=1000000)
        self.handle.createGroup(self.baseGroup,"dataManager")
        return self
        
    def getSensorDataTable(self):
        if self.sensorDataTableMemo is None:
            try:
                self.sensorDataTableMemo = self.handle.getNode(self.baseGroup,"sensorData")
                streamDict = self.sensorDataTableMemo._f_getAttr("streamNames")
                for k in streamDict:
                    self.streamLookup[streamDict[k][7:]] = k 
            except tables.exceptions.NoSuchNodeError:
                pass
        return self.sensorDataTableMemo
        
    def getRdDataTable(self):
        if self.rdDataTableMemo is None:
            try:    
                self.rdDataTableMemo = self.handle.getNode(self.baseGroup,"rdData")
            except tables.exceptions.NoSuchNodeError:
                pass
        return self.rdDataTableMemo
        
    def getDmDataTable(self,mode,source):
        try:
            modeGroup = getattr(self.handle.getNode(self.baseGroup,"dataManager"),mode)
            return getattr(modeGroup,source)
        except tables.exceptions.NoSuchNodeError:
            return None
        
    def retrieveOrMakeDmDataTable(self,mode,source,colNames):
        try:
            modeGroup = getattr(self.handle.getNode(self.baseGroup,"dataManager"),mode)
        except AttributeError:
            n = self.handle.getNode(self.baseGroup,"dataManager")
            modeGroup = self.handle.createGroup(n,mode)
        try:
            colNameSet = set(colNames)
            table = getattr(modeGroup,source)
            oldColNameSet = set(table.colnames)
            if colNameSet.issubset(oldColNameSet):
                return table
            else:
                # The columns have changed, so we need to extend the table
                table.rename('__tempTable__')
                newTable = self.handle.createTable(modeGroup,source,self.descrFromColNames(colNameSet.union(oldColNameSet)),expectedrows=500000)
                for row in table.iterrows():
                    newrow = newTable.row
                    for name in table.colnames:
                        newrow[name] = row[name]
                    newrow.append()
                newTable.flush()
                table.remove()
                return newTable
        except AttributeError:
            table = self.handle.createTable(modeGroup,source,self.descrFromColNames(colNameSet),expectedrows=500000)
            return table
            
    def descrFromColNames(self,colNameSet):
        """Construct a table description dictionary from the set of column names.
            At present, all columns are associated with a Float32Col. Later this will 
            be moodifiable using INI file options. Two additional columns "time" and 
            "timestamp" are added of type Float64Col and Int64Col respectively""" 
        descr = {}
        colNameSet = colNameSet.union(set(['time','timestamp']))
        for name in colNameSet:
            if name in ['time']:  
                descr[name] = tables.Float64Col()
            elif name in ['timestamp']:  
                descr[name] = tables.Int64Col()
            else: 
                descr[name] = tables.Float32Col()
        return descr
            
    def open(self,filename):    
        self.abspath = os.path.abspath(filename)
        self.handle = tables.openFile(filename,"a")
        # For active files, we expect there to be only a single group off
        #  the root, named by the base and stop timestamps
        for node in self.handle.iterNodes("/"):
            self.baseGroup = node
            self.baseTime = node._f_getAttr("baseTime")
            self.stopTime = node._f_getAttr("stopTime")
            self.tsRange = "%d_%d" % (self.baseTime,self.stopTime)
            if "t_" + self.tsRange != node._v_name:
                raise ValueError("Bad timestamp attributes in %s" % filename) 
            return self

    def close(self):
        self.handle.close()
        self.handle = None
        
    def remove(self):
        if self.handle is not None: self.close()
        os.remove(self.abspath)
        
    def getRdData(self,tstart,tstop,varList):
        """Get ringdown data lying in the specified time range"""
        table = self.getRdDataTable()
        if table is not None:
            selected = table.readWhere('(timestamp >= %d) & (timestamp < %d)' % (tstart,tstop))
            return recArrayExtract(selected,varList)
        else:
            return None

    def getSensorData(self,tstart,tstop,streamName):
        """Get sensor data lying in the specified time range."""
        table = self.getSensorDataTable()
        if table is not None:
            index = self.streamLookup.get(streamName,streamName)
            selected = table.readWhere('(timestamp >= %d) & (timestamp < %d) & (streamNum == %s)' % (tstart,tstop,index))
            return recArrayExtract(selected,["timestamp",("value",str(streamName))])
        else:
            return None

    def getDmData(self,mode,source,tstart,tstop,varList):
        """Get data manager data from specified mode and source lying in the specified time range"""
        table = self.getDmDataTable(mode,source)
        if table is not None:
            selected = table.readWhere('(timestamp >= %d) & (timestamp < %d)' % (tstart,tstop))
            return recArrayExtract(selected,varList)
        else:
            return None
        
class ActiveFileManager(object):
    def __init__(self,configFile):
        self.config = CustomConfigObj(configFile)
        basePath = os.path.split(configFile)[0]
        self.activeFilePeriod = self.config.getint("MainConfig","Period_s",600)
        self.graceInterval = self.config.getint("MainConfig","GraceInterval_s",60)
        self.archiveGroupName = self.config.get("MainConfig", "ArchiveGroupName", "Analyzer_Data")
        self.activeFileDir = os.path.join(basePath, self.config.get("MainConfig","ActiveDir","ActiveFiles"))
        if not os.path.exists(self.activeFileDir): os.makedirs(self.activeFileDir)

        self.sensorQueue = Queue(0)
        self.sensorListener = Listener.Listener(self.sensorQueue,
                                                BROADCAST_PORT_SENSORSTREAM,
                                                interface.SensorEntryType,
                                                retry = True,
                                                name = "ActiveFileManager listener")
        self.rdQueue = Queue(0)
        self.rdListener = Listener.Listener(self.rdQueue,
                                            BROADCAST_PORT_RD_RECALC,
                                            interface.ProcessedRingdownEntryType,
                                            retry = True,
                                            name = "ActiveFileManager listener")
        self.dmQueue = Queue(0)
        self.dmListener = Listener.Listener(self.dmQueue,
                                            BROADCAST_PORT_DATA_MANAGER,
                                            ArbitraryObject,
                                            retry = True,
                                            name = "ActiveFileManager listener")
        self.rpcHandler = ActiveFileManagerRpcHandler(self)
        self.activeFiles = {}   # Maintains open files, keyed by baseTimes
        self.rpcThread = RpcServerThread(self.rpcHandler.server, self.rpcHandler.shutdown)
        self.rpcCommandQueue = Queue(0)
        self.rpcResultQueue  = Queue(0)
        
        self._shutdownRequested = False
        self.rpcInProgress = False
        
        self.sensorDataTable = None
        self.sensorDataBaseTime = 0
        self.rdDataTable = None
        self.rdDataBaseTime = 0
        self.dmDataTable = None

    def openActiveFiles(self):
        """Go through files with extension .h5 in the active file directory
           and open them."""
        fileList = glob(os.path.join(self.activeFileDir,'*.h5'))
        print "active files: ", fileList
        for f in fileList:
            a = ActiveFile().open(f)
            self.activeFiles[a.baseTime] = a
        
    def getBaseTime(self,timestamp):
        return int(numpy.floor(timestamp / (1000*self.activeFilePeriod)) * (1000*self.activeFilePeriod))

    def getActiveFile(self,timestamp):
        """Creates or gets a pre-existing active file associated with the specified timestamp."""
        baseTime = self.getBaseTime(timestamp)
        if baseTime not in self.activeFiles:
            a = ActiveFile().create(self.activeFileDir,baseTime,baseTime+1000*self.activeFilePeriod)
            self.activeFiles[a.baseTime] = a
        return self.activeFiles[baseTime]
    
    def closeActiveFiles(self):
        for a in self.activeFiles.values():
            a.close()
    
    def removeOldFiles(self,timestamp):
        for k,a in self.activeFiles.items():
            if timestamp > a.baseTime + 1000*(self.activeFilePeriod + self.graceInterval):
                if a.archivalStartTimestamp is None: # Start archival process
                    a.compressedFilePath = self.compressHdf5File(a)
                    a.archivalStartTimestamp = getTimestamp()
                    Archiver.ArchiveFile(self.archiveGroupName, a.compressedFilePath, removeOriginal=True, timestamp=a.baseTime)
                else: # Check if archival is complete
                    if Archiver.DoesFileExist(self.archiveGroupName, a.compressedFilePath, a.baseTime):
                        del self.activeFiles[k]
                        a.remove()
    
    def doRpcRequests(self):
        """Carry out up to 500ms of work satisfying up to 10 RPC requests from the rpcCommandQueue. 
        Since some requests can involve looking through many H5 files and take a long time, a request 
        is done by a generator which keeps track of which H5 files have been processed so far. A completed 
        request places a result array on the rpcResultQueue. The rpcInProgress attribute is True while a 
        request has not yet been completely satisfied.
        """
        for iter in range(10):
            if self.rpcInProgress:
                a,k = self.lastRpcParams
            elif not self.rpcCommandQueue.empty():
                self.lastRpcCmd, self.lastRpcParams = self.rpcCommandQueue.get()
            else:
                return
            a,k = self.lastRpcParams
            try:
                self.rpcInProgress = self.genWrapper(self.lastRpcCmd,*a,**k)
                if self.rpcInProgress: # This operation is taking a long time, try again next time
                    return
            except Exception,e:
                self.rpcInProgress = False
                self.rpcResultQueue.put(e)

    def genWrapper(self,gen,*a,**k):
        """Wrapper for a generator so that it gives a method which returns False to indicate
           that the generator has terminated and placed a result on rpcResultQueue and which 
           returns True if there is still more work to do"""
        if not self.rpcInProgress:
            self.gen = gen(*a,**k)
            startTime = None
        else:
            startTime = time.clock()
        try:
            self.gen.send(startTime)
            return True
        except StopIteration:
            return False
            
    def genRdData(self,tstart,tstop,varList):
        results = []
        t = time.clock()
        for baseTime in sorted(self.activeFiles.keys()):
            # Determine if [tstart,tstop) and [baseTime,stopTime) are disjoint
            if tstop <= baseTime: continue
            a = self.activeFiles[baseTime]
            if tstart >= a.stopTime: continue
            d = a.getRdData(tstart,tstop,varList)
            if d is not None:
                results.append(d)
            if time.clock()-t > 0.5: t = yield True # Indicate not yet done
        if results:
            self.rpcResultQueue.put(numpy.concatenate(results))
        else:
            self.rpcResultQueue.put(None)

    def genSensorData(self,tstart,tstop,streamName):
        results = []
        t = time.clock()
        for baseTime in sorted(self.activeFiles.keys()):
            # Determine if [tstart,tstop) and [baseTime,stopTime) are disjoint
            if tstop <= baseTime: continue
            a = self.activeFiles[baseTime]
            if tstart >= a.stopTime: continue
            d = a.getSensorData(tstart,tstop,streamName)
            if d is not None: 
                results.append(d)
            if time.clock()-t > 0.5: t = yield True # Indicate not yet done
        if results:
            self.rpcResultQueue.put(numpy.concatenate(results))
        else:
            self.rpcResultQueue.put(None)

    def genDmData(self,mode,source,tstart,tstop,varList):
        results = []
        t = time.clock()
        latestException = None
        for baseTime in sorted(self.activeFiles.keys()):
            # Determine if [tstart,tstop) and [baseTime,stopTime) are disjoint
            if tstop <= baseTime: continue
            a = self.activeFiles[baseTime]
            if tstart >= a.stopTime: continue
            # We may get an AttributeError exception in genDmData for the most
            #  recent files if the required tables have not yet been created.
            #  Similarly, when the analyer is warming up, we may not have the 
            #  correct modes or sources available.
            # We only report an error if there are no results
            try:
                d = a.getDmData(mode,source,tstart,tstop,varList)
                if d is not None:
                    results.append(d)
                if time.clock()-t > 0.5: t = yield True # Indicate not yet done
            except AttributeError,e:
                latestException = e
        if results:
            self.rpcResultQueue.put(numpy.concatenate(results))
        else:
            self.rpcResultQueue.put(None)

    def genRdDataStruct(self,tstart,tstop):
        dataDict = {}
        t = time.clock()
        for baseTime in sorted(self.activeFiles.keys(),reverse=True):
            # Determine if [tstart,tstop) and [baseTime,stopTime) are disjoint
            if tstop <= baseTime: continue
            af = self.activeFiles[baseTime]
            if tstart >= af.stopTime: continue
            #
            if time.clock()-t > 0.5: t = yield True # Indicate not yet done
            # We now have an active file which overlaps with [tstart,tstop)
            rdDataTable = af.handle.getNode(af.baseGroup,"rdData")
            colnames = rdDataTable.colnames
            typeDict = rdDataTable.coltypes
            for c in colnames:
                if c not in dataDict:
                    dataDict[c] = typeDict[c]
        if dataDict:
            self.rpcResultQueue.put(dataDict)
        else:
            self.rpcResultQueue.put(None)
             
    def genDmDataStruct(self,tstart,tstop):
        dataDict = {}
        t = time.clock()
        for baseTime in sorted(self.activeFiles.keys(),reverse=True):
            # Determine if [tstart,tstop) and [baseTime,stopTime) are disjoint
            if tstop <= baseTime: continue
            af = self.activeFiles[baseTime]
            if tstart >= af.stopTime: continue
            #
            if time.clock()-t > 0.5: t = yield True # Indicate not yet done
            # We now have an active file which overlaps with [tstart,tstop)
            modes = af.handle.getNode(af.baseGroup,"dataManager")._v_children
            for m in modes:
                if m not in dataDict:
                    dataDict[m] = {}
                analyses = modes[m]._v_children
                for a in analyses:
                    if a not in dataDict[m]:
                        dataDict[m][a] = {}
                    colnames = analyses[a].colnames
                    typeDict = analyses[a].coltypes
                    for c in colnames:
                        if c not in dataDict[m][a]:
                            dataDict[m][a][c] = typeDict[c]
        if dataDict:
            self.rpcResultQueue.put(dataDict)
        else:
            self.rpcResultQueue.put(None)
            
    def compressHdf5File(self,activeFile):
        """Copy an uncompressed file to a new HDF5 file with the compression filters
           turned on. Returns name of the compressed file."""
        filters = tables.Filters(complevel=1,fletcher32=True)
        newPath = activeFile.abspath.replace('.h5','_c.h5')
        activeFile.handle.copyFile(newPath,filters=filters,copyuserattrs=True)
        return newPath
        
    # There is a directory in which the active file is maintained.
    # The timestamp is rounded down to a multiple of the activeFilePeriod to give the
    # "baseTime" which labels the active file to which the data belong.
    
    # Given a timestamp and an active file period, we need to see if a new file needs 
    #  to be created or if a pre-existing active file should be used.
    # Pre-existing active files which are no longer current must be closed and sent 
    #  to the archiver for compression and long-term storage
    # 
    # We keep track of an active file and the next active file so that points in a 
    #  queue that stradle the boundary between files can be dealt with properly. It 
    #  is only safe to close the current active file once there are data from all 
    #  queues whose baseTime values are after the baseTime of the current active 
    #  file. However, in order to cope with the situation in which no data arrive
    #  in a queue for an extended period, there is a grace period beyond which an
    #  active file is closed unconditionally.
       
    def run(self):
        self.rpcThread.start()
        # Here follows the main loop.
        Log("Starting main ActiveFileManager loop",Level=1)
        self.openActiveFiles()
        try:
            while not self._shutdownRequested:
                # Handle listener queues here
                while not self.sensorQueue.empty():
                    d = self.sensorQueue.get()
                    if not (self.sensorDataBaseTime <= d.timestamp < self.sensorDataBaseTime + self.activeFilePeriod):
                        if self.sensorDataTable is not None: 
                            try:
                                self.sensorDataTable.flush()
                            except:
                                pass
                        a = self.getActiveFile(d.timestamp)
                        self.sensorDataTable = a.getSensorDataTable()
                        self.sensorDataBaseTime = a.baseTime
                    row = self.sensorDataTable.row
                    for name,cls in interface.SensorEntryType._fields_:
                        row[name] = getattr(d,name)
                    row.append()
                if self.sensorDataTable is not None: 
                    try:
                        self.sensorDataTable.flush()
                    except:
                        pass

                while not self.rdQueue.empty():
                    d = self.rdQueue.get()
                    if not (self.rdDataBaseTime <= d.timestamp < self.rdDataBaseTime + self.activeFilePeriod):
                        if self.rdDataTable is not None: 
                            try:
                                self.rdDataTable.flush()
                            except:
                                pass
                        a = self.getActiveFile(d.timestamp)
                        self.rdDataTable = a.getRdDataTable()
                        self.rdDataBaseTime = a.baseTime
                    row = self.rdDataTable.row
                    for name,cls in interface.ProcessedRingdownEntryType._fields_:
                        row[name] = getattr(d,name)
                    row.append()
                if self.rdDataTable is not None: 
                    try:
                        self.rdDataTable.flush()
                    except:
                        pass
                
                while not self.dmQueue.empty():
                    d = self.dmQueue.get()
                    timestamp, mode, source = d['data']['timestamp'], d['mode'], d['source']
                    colNameSet = set(d['data'].keys())
                    a = self.getActiveFile(timestamp)
                    # Get data manager table for given mode and source, creating it if it does not 
                    #  exist
                    dmDataTable = a.retrieveOrMakeDmDataTable(mode,source,colNameSet)
                    if self.dmDataTable is not None and self.dmDataTable != dmDataTable:
                        try:
                            self.dmDataTable.flush()
                        except:
                            pass
                    self.dmDataTable = dmDataTable
                    row = self.dmDataTable.row
                    for name in colNameSet:
                        row[name] = d['data'][name]
                    row.append()
                if self.dmDataTable is not None: 
                    try:
                        self.dmDataTable.flush()
                    except:
                        pass
                ts = getTimestamp()
                # print "In main loop: %s, activeFiles: %s" % (self.getBaseTime(ts),self.activeFiles)
                self.getActiveFile(ts)  # Create new active file if needed
                if not self.rpcInProgress: self.removeOldFiles(ts)
                self.doRpcRequests()    # Perform next bit of work for RPC functions
                time.sleep(0.05)
                
            print "Shutdown requested"    
            Log("ActiveFileManager RPC handler shut down")
        except:
            type,value,trace = sys.exc_info()
            print "Unhandled Exception in main loop: %s: %s" % (str(type),str(value))
            print traceback.format_exc()
            Log("Unhandled Exception in main loop: %s: %s" % (str(type),str(value)),
                Verbose=traceback.format_exc(),Level=3)
        self.closeActiveFiles()
        
HELP_STRING = """ActiveFileManager.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./ActiveFileManager.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/ActiveFileManager.ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile

if __name__ == "__main__":
    configFile = handleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    a = ActiveFileManager(configFile)
    a.run()
    