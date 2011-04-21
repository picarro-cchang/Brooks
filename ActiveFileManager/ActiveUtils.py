#!/usr/bin/python
#
"""
File Name: ActiveUtils.py
Purpose: Utilities for accessing archived and active files

File History:
    06-Nov-2010  sze  Initial version.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import numpy
import os
from re import compile, match
from cPickle import load, dump, HIGHEST_PROTOCOL
import sys
import tables
import traceback
from Host.ActiveFileManager.ActiveFileManager import ActiveFile, recArrayExtract
from Host.Common import timestamp
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.timestamp import getTimestamp

ActiveFileManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_ACTIVE_FILE_MANAGER,
                                    ClientName="django", IsDontCareConnection=False)
ANALYZER_DATA = 'C:/Picarro/AnalyzerData'

def overlap(int1, int2):
    """Determines if intervals int1 and int 2 overlap"""
    start1, stop1 = int1
    start2, stop2 = int2
    if start1 > stop1 or start2 > stop2:
        raise ValueError('Invalid time interval')
    return start2 <= start1 < stop2 or start1 <= start2 < stop1

def fetchFilesInRange(top, startTimestamp, stopTimestamp, reverse=False):
    """Generator which yields HDF5 filenames containing data which overlap with 
    the specified timestamp range in a time-based directoy tree rooted at top.
    The filenames must be of the form startTimestamp_stopTimestamp_*. If reverse
    is False, the files are fetched in order of increasing time, while if reverse
    is True, they are fetched in order of decreasing time.
    """
    # Ensure top ends with a '/'
    top = top.strip().replace('\\', '/')
    if not top or top[-1] != '/':
        top += '/'
    ltop = len(top)
    startTuple = timestamp.timestampToUtcDatetime(startTimestamp).timetuple()
    stopTuple = timestamp.timestampToUtcDatetime(stopTimestamp).timetuple()
    for p, dirs, files in os.walk(top):
        dirs.sort()
        if reverse:
            dirs.reverse()
        pre = p.find(top)
        if pre < 0:
            raise ValueError('Path should start with top-level name')
        if dirs:
            if not reverse:
                before = 0
                for d in dirs:
                    # Get list of year, month, day, ... from directory name
                    timeList = map(int, os.path.join(p[pre + ltop:], d).replace('\\', '/').split('/'))
                    if timeList < list(startTuple[:len(timeList)]):
                        before += 1
                # Remove directories with files before specified time
                # This must be a slice assignment to change dirs in-place
                dirs[:] = dirs[before:]
            else:
                after = 0
                for d in dirs:
                    # Get list of year, month, day, ... from directory name
                    timeList = map(int, os.path.join(p[pre + ltop:], d).replace('\\', '/').split('/'))
                    if timeList > list(stopTuple[:len(timeList)]):
                        after += 1
                # Remove directories with files before after time
                # This must be a slice assignment to change dirs in-place
                dirs[:] = dirs[after:]
        if files:
            for f in files if not reverse else files[::-1]:
                try:
                    baseTime, stopTime = map(int, f.split('_')[:2])
                except:
                    try:
                        baseTime, = map(int, f.split('_')[:1])
                        stopTime = baseTime + 60000
                    except:
                        continue
                if overlap((baseTime, stopTime), (startTimestamp, stopTimestamp)):
                    yield os.path.join(p, f)

def getDmData(mode,source,tstart,tstop,varList):
    """Return numpy record array with requested variables and specified start and stop times"""
    result_list = []
    try:
        for f in fetchFilesInRange(ANALYZER_DATA, tstart, tstop):
            a = ActiveFile()
            try:
                a.open(f)
                table = a.getDmDataTable(mode, source)
                if table is not None:
                    selected = table.readWhere('(timestamp >= %d) & (timestamp < %d)' % (tstart, tstop))
                    if selected is not None:
                        result_list.append(recArrayExtract(selected,varList))
            finally:
                a.close()
    except Exception, e:
        print "Error %s, %r" % (e,e)
        traceback.print_exc()
    selected = ActiveFileManager.getDmData(mode, source, tstart, tstop, varList)
    if selected is not None: result_list.append(selected)
    if result_list:
        return numpy.concatenate(result_list)
    else:
        return None

def getSensorData(tstart,tstop,streamName):
    """Return numpy record array with requested sensor stream and specified start and stop times"""
    result_list = []
    try:
        for f in fetchFilesInRange(ANALYZER_DATA, tstart, tstop):
            a = ActiveFile()
            try:
                a.open(f)
                table = a.getSensorDataTable()
                if table is not None:
                    index = a.streamLookup.get(streamName,streamName)
                    selected = table.readWhere('(timestamp >= %d) & (timestamp < %d) & (streamNum == %s)' % (tstart,tstop,index))
                    if selected is not None:
                        result_list.append(recArrayExtract(selected,["timestamp",("value",str(streamName))]))
            finally:
                a.close()
    except Exception, e:
        print "Error %s, %r" % (e,e)
        traceback.print_exc()
    selected = ActiveFileManager.getSensorData(tstart, tstop, streamName)
    if selected is not None: result_list.append(selected)
    if result_list:
        return numpy.concatenate(result_list)
    else:
        return None
        
def getRdData(tstart,tstop,varList):
    """Return numpy record array with requested variables and specified start and stop times"""
    result_list = []
    try:
        for f in fetchFilesInRange(ANALYZER_DATA, tstart, tstop):
            a = ActiveFile()
            try:
                a.open(f)
                table = a.getRdDataTable()
                if table is not None:
                    selected = table.readWhere('(timestamp >= %d) & (timestamp < %d)' % (tstart, tstop))
                    if selected is not None:
                        result_list.append(recArrayExtract(selected,varList))
            finally:
                a.close()
    except Exception, e:
        print "Error %s, %r" % (e,e)
        traceback.print_exc()
    selected = ActiveFileManager.getRdData(tstart, tstop, varList)
    if selected is not None: result_list.append(selected)
    if result_list:
        return numpy.concatenate(result_list)
    else:
        return None
        
def sortByName(top, nameList):
    nameList.sort()
    return nameList

def sortByMtime(top, nameList):
    """Sort a list of files by modification time"""
    # Decorate with the modification time of the file for sorting
    fileList = [(os.path.getmtime(os.path.join(top, name)), name) for name in nameList]
    fileList.sort()
    return [name for _, name in fileList]
    
def walkTree(top, onError=None, sortDir=None, sortFiles=None):
    """Generator which traverses a directory tree rooted at "top" in bottom to top order (i.e., the children are visited
    before the parent, and directories are visited before files.) The order of directory traversal is determined by
    "sortDir" and the order of file traversal is determined by "sortFiles". If "onError" is defined, exceptions during
    directory listings are passed to this function. When the function yields a result, it is either the pair
    ('file',fileName)  or ('dir',directoryName)"""
    try:
        names = os.listdir(top)
    except OSError, err:
        if onError is not None:
            onError(err)
        return
    # Obtain lists of directories and files which are not links
    dirs, nondirs = [], []
    for name in names:
        fullName = os.path.join(top, name)
        if not os.path.islink(fullName):
            if os.path.isdir(fullName):
                dirs.append(name)
            else:
                nondirs.append(name)
    # Sort the directories and nondirectories (in-place)
    if sortDir is not None:
        dirs = sortDir(top, dirs)
    if sortFiles is not None:
        nondirs = sortFiles(top, nondirs)
    # Recursively call walkTree on directories
    for dir in dirs:
        for x in walkTree(os.path.join(top, dir), onError, sortDir, sortFiles):
            yield x
    # Yield up files
    for file in nondirs:
        yield 'file', os.path.join(top, file)
    # Yield up the current directory
    yield 'dir', top

def getRdDataStruct(tstart,tstop):
    # Generate a dictionary whose keys are the available ringdown data columns. The values 
    #  stored are the data types of the desired columns as strings.
    # We iterate backwards through the files since the latest files are more likely to contain 
    #  all the data columns.
    dataDict = ActiveFileManager.getRdDataStruct(tstart, tstop)
    for f in fetchFilesInRange(ANALYZER_DATA, tstart, tstop, reverse=True):
        af = ActiveFile()
        af.open(f)
        try:
            rdDataTable = af.handle.getNode(af.baseGroup,"rdData")
            colnames = rdDataTable.colnames
            typeDict = rdDataTable.coltypes
            for c in colnames:
                if c not in dataDict:
                    dataDict[c] = typeDict[c]
        finally:
            af.close()
    return dataDict
    
def getDmDataStruct(tstart,tstop):
    # Generate a nested dictionary, the first level is indexed by mode, the second by analysis 
    #  name and the third by available data columns. The values stored are the column data types
    #  as strings.
    # We iterate backwards through the files since the latest files are more likely to contain 
    #  all the data columns.
    dataDict = ActiveFileManager.getDmDataStruct(tstart, tstop)
    for f in fetchFilesInRange(ANALYZER_DATA, tstart, tstop, reverse=True):
        af = ActiveFile()
        af.open(f)
        try:
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
        finally:
            af.close()
    return dataDict

def dictMerge(targetDict,srcDict):
    """Recursively updates targetDict so that it contains all the keys in srcDict"""
    for s in srcDict:
        if s not in targetDict:
            targetDict[s] = srcDict[s]
        else:
            if isinstance(targetDict[s],dict) and isinstance(srcDict[s],dict):
                dictMerge(targetDict[s],srcDict[s])
            else:
                targetDict[s] = srcDict[s]


def getDirectoryDataStruct(path):
    """Go through files in a directory and determine available data"""
    filePatt = compile("\d{14}_\d{14}_c.h5")
    dsPatt = compile("\d+.pic")
    dirList = [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
    for d in dirList:
        getDirectoryDataStruct(os.path.join(path, d))
    files = [name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name))]
    if files:
        dataDict = {}
        matches = 0
        for f in files:
            if match(filePatt,f):
                matches += 1
                filename = os.path.join(path,f)
                #af = tables.openFile(filename,"r")
                af = ActiveFile()
                af.open(filename)
                modes = af.handle.getNode(af.baseGroup,"dataManager")._v_children
                for m in modes:
                    if m not in dataDict:
                        dataDict[m] = {}
                    analyses = modes[m]._v_children
                    for a in analyses:
                        if a not in dataDict[m]:
                            colnames = analyses[a].colnames
                            typeDict = analyses[a].coltypes
                            dataDict[m][a] = (colnames,[typeDict[c] for c in colnames])
                af.close()
            elif match(dsPatt,f):
                matches += 1
                filename = os.path.join(path,f)
                fp = file(filename,"rb")
                dictMerge(dataDict,load(fp))
                fp.close()
        if matches:
            fp = file(path+'.pic',"wb")
            dump(dataDict,fp,HIGHEST_PROTOCOL)
            fp.close()

def recArrayToJSON(recArray):
    obj = {}
    for n in recArray.dtype.names:
        obj[n] = [float(v) for v in recArray[n]]
    return obj
    
if __name__ == "__main__":
    option = input("Option? ") if len(sys.argv)<=1 else int(sys.argv[1])
    if option == 0:
        startTimestamp = input("startTimestamp? ")
        stopTimestamp  = input("stopTimestamp? ")
        reverse = input("reverse? ")
        print [f for f in fetchFilesInRange(ANALYZER_DATA, startTimestamp, stopTimestamp, reverse)]
        sys.exit()
    elif option == 1:
        tstop = getTimestamp()
        tstart = tstop - 2*3600 * 1000
        print getDmDataStruct(tstart, tstop)
    elif option == 2:
        tstop = getTimestamp()
        tstart = tstop - 2*3600 * 1000
        mode = "CFADS_mode"
        source = "analyze_CFADS"
        varList = ["timestamp","CO2","CH4","H2O"]
        dmData = getDmData(mode,source,tstart,tstop,varList)
        print recArrayToJSON(dmData)
    elif option == 3:
        tstop = getTimestamp()
        tstart = tstop - 3600 * 1000
        r = getSensorData(tstart,tstop,'WarmBoxTemp')
        print r
        print 'Number of points', len(r)
    elif option == 4:
        tstop = getTimestamp()
        tstart = tstop - 100 * 1000
        r = getRdData(tstart,tstop,['timestamp','waveNumber','uncorrectedAbsorbance'])
        print len(r)
    elif option == 5:
        tstop = getTimestamp()
        tstart = tstop - 10 * 1000
        r = ActiveFileManager.getRdDataStruct(tstart,tstop)
        print r        