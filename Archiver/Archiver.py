#!/usr/bin/python
#
"""
File Name: Archiver.py
Purpose:
    This application handles the storage (and retrieval) of files that should
    be archived.  It manages the space to make sure the storage limits are
    are not exceeded.

File History:
    07-01-05 sze   First release
    07-01-10 sze   Added comments, return number of files extracted
    07-02-01 sze   Add Directory key to allow a group to be stored in an arbitrary location
    07-08-22 sze   Wrap binary data for archival
    08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj
    08-09-30 alex  Added level 0 as the "Quantum" option. Also enabled Archiver to store and manage data for DataLogger
    09-07-03 alex  Provide an option to construct the storage paths using local time (generally GMT is used)
    10-06-14 sze   Allow a timestamp to be specified when calling archiveData
    10-06-15 sze   New RPC function "DoesFileExist"
    
Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
APP_NAME = "Archiver"
__version__ = 1.0
_DEFAULT_CONFIG_NAME = "Archiver.ini"
_MAIN_CONFIG_SECTION = "MainConfig"

import sys
import os
import getopt
import doctest
import threading
import traceback
import shutil
import stat
import time
import Queue
import zipfile
from inspect import isclass
from cStringIO import StringIO
from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,\
                      INVALID_HANDLE_VALUE
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_LOGGER, RPC_PORT_ARCHIVER, RPC_PORT_DRIVER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import *
from Host.Common.timestamp import timestampToUtcDatetime, unixTime
from Host.Common.S3Uploader import S3Uploader

EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes
    
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                            APP_NAME,
                                            IsDontCareConnection = False)
                                            
#
# Functions
#
def NameOfThisCall():
    return sys._getframe(1).f_code.co_name

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

def deleteFile(filename):
    """Delete a file, reporting any error, but not causing an exception. Returns True if delete succeeded"""
    try:
        os.chmod(filename,stat.S_IREAD | stat.S_IWRITE)
        os.remove(filename)
        return True
    except OSError,e:
        Log("Error deleting file: %s. %s" % (filename,e))
        return False

def sortByName(top,nameList,reversed=False):
    nameList.sort()
    if not reversed:
        return nameList
    else:
        return nameList[::-1]

def sortByMtime(top,nameList,reversed=False):
    """Sort a list of files by modification time"""
    # Decorate with the modification time of the file for sorting
    fileList = [(os.path.getmtime(os.path.join(top,name)),name) for name in nameList]
    fileList.sort()
    if not reversed:
        return [name for t,name in fileList]
    else:
        return [name for t,name in fileList[::-1]]
    
def walkTree(top,onError=None,sortDir=None,sortFiles=None,reversed=False):
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
        fullName = os.path.join(top,name)
        if not os.path.islink(fullName):
            if os.path.isdir(fullName):
                dirs.append(name)
            else:
                nondirs.append(name)
    # Sort the directories and nondirectories (in-place)
    if sortDir is not None:
        dirs = sortDir(top,dirs,reversed)
    if sortFiles is not None:
        nondirs = sortFiles(top,nondirs,reversed)
    # Recursively call walkTree on directories
    for dir in dirs:
        for x in walkTree(os.path.join(top,dir),onError,sortDir,sortFiles,reversed):
            yield x
    # Yield up files
    for file in nondirs:
        yield 'file', os.path.join(top,file)
    # Yield up the current directory
    yield 'dir', top

def makeStoragePathName(struct_time,level):
    """Convert a struct_time object into a relative path name, using entries in struct_time up to the specified level:
    level = 0: flat (no timestamp in the path name)
    level = 1: year only
    level = 2: include month
    level = 3: include monthday
    level = 4: include hours
    level = 5: include minutes
    level = 6: include seconds

    >>> import time
    >>> import calendar
    >>> print makeStoragePathName(time.gmtime(1167863366),5)
    2007/01/03/22/29
    >>> print makeStoragePathName(time.gmtime(1167863366),3)
    2007/01/03
    """
    if level<0 or level>6:
        raise ValueError,"Invalid level in makeStoragePathName (valid value: 0...6)"
    elif level>0:    
        pathList = ["%04d" % (struct_time[0],)]
        for i in range(1,level):
            pathList.append("%02d" % (struct_time[i],))
        return "/".join(pathList)
    else:
        # Flat directory without timestamp
        return "."

class LiveArchive(object):
    """Class used to monitor a file generated by the data logger and which copies any changes to a user-accessible file
    opened for shared reading and exclusive writing. Runs in a separate thread."""
    def __init__(self,srcPathName,destPathName,archiveGroup):
        self.srcPathName = srcPathName
        self.destPathName = destPathName
        self.bytesCopied = 0
        self.updating = False
        self.srcFp = None
        self.archiveGroup = archiveGroup
        self.oldNBytes = 0
        
    # Live updating for data logs
    def startUpdate(self):
        self.destHandle = CreateFile(self.destPathName,GENERIC_WRITE,
                                     FILE_SHARE_READ,None,CREATE_ALWAYS,
                                     FILE_ATTRIBUTE_NORMAL,0)
        if self.destHandle == INVALID_HANDLE_VALUE:
            Log('Cannot open live archive file %s' % self.destPathName, Level=2)
            return False
        self.updating = True
        self.srcFp = open(self.srcPathName,'rb')
        if not self.srcFp:
            Log('Cannot open datalogger file %s' % self.srcPathName, Level=2)
            return False
        self.archiveGroup.makeSpace(0,1)
        self.updateThread = threading.Thread(target=self.updater)
        self.updateThread.setDaemon(True)
        self.updateThread.start()
        return True

    def updater(self):
        while self.updating:
            data = self.srcFp.readline()
            if not data:
                time.sleep(1.0)
                continue
            nBytes = len(data)
            self.archiveGroup.makeSpace(nBytes,0)
            WriteFile(self.destHandle,data)
            self.bytesCopied += nBytes
            
    def stopUpdate(self):
        self.updating = False
        CloseHandle(self.destHandle)
        if self.srcFp:
            self.srcFp.close()
        self.updateThread.join(15.0)
        if self.updateThread.isAlive():
            Log('Live archive %s cannot be closed' % self.destPathName, Level=3)
    
    # Live copying for coordinator output files
    def startCopy(self):
        self.destHandle = CreateFile(self.destPathName,GENERIC_WRITE,
                                     FILE_SHARE_READ,None,CREATE_ALWAYS,
                                     FILE_ATTRIBUTE_NORMAL,0)
        if self.destHandle == INVALID_HANDLE_VALUE:
            Log('Cannot open live archive file %s' % self.destPathName, Level=2)
            return False
        self.updating = True
        self.oldNBytes = 0
        self.srcFp = open(self.srcPathName,'rb')
        if not self.srcFp:
            Log('Cannot open datalogger file %s' % self.srcPathName, Level=2)
            return False
        self.archiveGroup.makeSpace(0,1)
        self.copyThread = threading.Thread(target=self.copier)
        self.copyThread.setDaemon(True)
        self.copyThread.start()
        return True

    def makeCopy(self):
        self.srcFp.seek(0)
        data = self.srcFp.read()
        nBytes = len(data)
        deltaNBytes = nBytes - self.oldNBytes
        if deltaNBytes > 0:
            self.archiveGroup.makeSpace(deltaNBytes,0)
            SetFilePointer(self.destHandle, 0, FILE_BEGIN)
            WriteFile(self.destHandle,data)
            self.oldNBytes = nBytes
                
    def copier(self):
        while self.updating:
            self.makeCopy()
            time.sleep(10.0)
        # Make the last copy before exiting
        self.makeCopy()
        CloseHandle(self.destHandle)
        if self.srcFp:
            self.srcFp.close()
            deleteFile(self.srcPathName)
        
    def stopCopy(self):
        self.updating = False
        self.copyThread.join(20.0)
        if self.copyThread.isAlive():
            Log('Live archive %s cannot be closed' % self.destPathName, Level=3)
            
class ArchiveGroup(object):
    """Class associated with each storage group. This corresponds to a directory called "groupName" created under the
    storageRoot of the archiver. Under this directory, files are stored in a tree organized by file modification time in GMT.
    The number of levels of the tree (potentially year, month, day, hour, minute and second) is determined by "quantum".
    Limits may be placed on the number of megabytes in the files and/or the number of files in the group.

    Depending on the options specified for the storage group, data may be aggregated and/or compressed before storage.
    Such compression and aggregation are handled by the zipfile module.

    Since operations on an archive group may potentially take awhile, they are carried out in a separate (daemonic) thread
    of execution called "serverThread". Commands to be executed are passed via a queue called cmdQueue. This allows the
    archiver to handle supervisor pings even if it has to do lengthy operations on the disk."""

    def __init__(self, groupName, archiver):
        assert isinstance(archiver,Archiver)
        self.name = groupName
        try:
            self.groupRoot = archiver.config.get(groupName,'Directory')
        except:
            self.groupRoot = os.path.join(archiver.storageRoot,groupName)

        if archiver.config.get(groupName,"StorageFolderTime","gmt").lower() == "local":
            self.maketimetuple = time.localtime
        else:
            self.maketimetuple = time.gmtime
                
        self.maxCount = archiver.config.getint(groupName,'MaxCount')
        self.maxSize = int(1000000 * archiver.config.getfloat(groupName,'MaxSize_MB'))
        try:
            self.quantum = archiver.config.getint(groupName,'Quantum')
        except KeyError:
            self.quantum = 3
        self.aggregation = 0
        self.cmdQueue = Queue.Queue(0) # Queue for commands
        # Enqueue command to initialize the archive group
        self.cmdQueue.put(("init",()))

        self.serverThread = threading.Thread(target=self.server)
        self.fileCount = -1
        self.byteCount = -1

        try:
            self.compress = archiver.config.getboolean(groupName, "Compress")
        except KeyError:
            self.compress = False
        try:
            self.aggregationCount = archiver.config.getint(groupName, "AggregationCount")
        except KeyError:
            self.aggregationCount = 0
        if not os.path.exists(self.groupRoot):
            os.makedirs(self.groupRoot)
            Log("Creating archive group directory %s" % (self.groupRoot,))
        # Create temporary filename for compression and aggregation
        self.tempFileName = os.path.join(archiver.storageRoot,groupName + ".zip")
        if os.path.exists(self.tempFileName): 
            self.cmdQueue.put(("archiveFile",(self.tempFileName,)))
        # Dictionary of live archives by source file name
        self.liveArchiveDict = {}
        # Lock for arbitrating access to file deletion routines to make space for new data
        self.makeSpaceLock = threading.Lock()
        
        # For data uploading
        self.uploader = archiver.uploader
        self.retryUploadInterval = archiver.retryUploadInterval
        self.uploadEnabled = archiver.config.getboolean(groupName,'UploadEnabled', False)
        self.uploadRetryPath = os.path.join(self.groupRoot, "upload")
        # Flag to scan the "upload" folder and upload any remaining files
        self.retryUploadNeeded = True
        if self.uploadEnabled:
            self.retryUploadThread = threading.Thread(target=self.retryUploadScheduler)
            self.retryUploadThread.setDaemon(True)
            self.retryUploadThread.start()
            
        self.serverThread.setDaemon(True)
        self.serverThread.start()

    def server(self):
        """This is the main thread function which listens to requests from the cmdQueue and executes them sequentially.
        Commands on cmdQueue consist of a pair (command,argumentList). The command is looked up using cmdDict, and the
        arguments are passed to the appropriate function."""
        cmdDict = dict(archiveData = self.archiveData,
                       copyFiles = self.extractFiles,
                       getFileNames = self.getFileNames,
                       refreshStats = self.updateAndGetArchiveSize,
                       init = self.initArchiveGroup,
                       archiveFile = self.archiveFile,
                       startLiveArchive = self.startLiveArchive,
                       stopLiveArchive = self.stopLiveArchive,
                       retryUpload = self.retryUpload)
        self.updateAndGetArchiveSize()
        Log("Group %s, files %d, bytes %d" % (self.name,self.fileCount,self.byteCount,))
        while True:
            try:
                cmd,args = self.cmdQueue.get()
                startTime = time.clock()
                cmdDict[cmd](*args)
                if cmd != "archiveData":
                    Log("Archiver command %s took %s seconds" % (cmd,time.clock()-startTime))
            except Exception, exc:
                Log("Exception in ArchiveGroup server",
                    dict(GroupName = self.name), Verbose = "Exception = %s %r" % (exc, exc))
                    
    def retryUploadScheduler(self):
        while True:
            if self.retryUploadNeeded:
                self.cmdQueue.put(("retryUpload",()))
            time.sleep(self.retryUploadInterval)

    def zipSource(self, source, targetPath):
        """
        Compresses the source (either a filename or a (name,data) tuple) and puts it into targetPath.
        """
        if self.aggregationCount > 0:
            if os.path.exists(targetPath):
                writeMode = "a"
            else:
                writeMode = "w"
        else:
            writeMode = "w"

        if self.compress:
            compressMode = zipfile.ZIP_DEFLATED
        else:
            compressMode = zipfile.ZIP_STORED

        zf = zipfile.ZipFile(targetPath, writeMode, compressMode)
        try:
            if isinstance(source,tuple):
                sourceName, sourceData = source
                zf.writestr(sourceName, sourceData)
            else:
                # Need to convert filename to a str to avoid Unicode errors
                zf.write(str(source))

        finally:
            zf.close()
            del zf

    def initArchiveGroup(self):
        # The treeWalker is used to delete the oldest entries when required
        self.treeWalker = walkTree(self.groupRoot,sortDir=sortByName,sortFiles=sortByMtime,reversed=False)
        # Create a uploadTreeWalker to retry uploading the newest entries when required
        self.uploadTreeWalker = walkTree(self.uploadRetryPath,sortDir=sortByName,sortFiles=sortByMtime,reversed=True)
        # Remove empty subdirectories
        self._removeEmptySubdirs()        
        
    def extractFiles(self,destDir, startTime=None, endTime=None, uniqueFileNames = False, resultQueue = None):
        """Extract all files between the specified starting and ending times to the destination directory. If uniqueFileNames is
           True, the group name and date code are prepended to each file. Returns the number of files copied, and places them on
           the specified resultQueue. """
        count = 0
        if not os.path.exists(destDir):
            os.makedirs(destDir)
        for type,name in walkTree(self.groupRoot,sortDir=sortByName,sortFiles=sortByName,reversed=False):
            if type == 'file':
                fileTime = os.path.getmtime(name)
                if (startTime is not None) and fileTime < startTime: continue
                if (endTime is not None) and fileTime > endTime: continue
                destName = os.path.split(name)[-1]
                if uniqueFileNames: destName = time.strftime(self.name+"_%Y%m%d_%H%M%S_",time.gmtime(fileTime)) + destName
                try:
                    shutil.copy2(name,os.path.join(destDir,destName))
                    count += 1
                except Exception,e:
                    Log("Extract file error copying %s. %s" % (name,e,))
                time.sleep(0)
        if resultQueue is not None: resultQueue.put(count)
        return count
        
    def doesFileExist(self,fileName,timestamp):
        """Inquires if the specified file name exists in this group for the specified timestamp"""
        timeTuple = self.maketimetuple(unixTime(timestamp))
            
        pathName = makeStoragePathName(timeTuple,self.quantum)
        pathName = os.path.join(self.groupRoot,pathName)
        targetName = os.path.join(pathName,os.path.split(fileName)[-1])
        return os.path.exists(targetName)

    def startLiveArchive(self, source, timestamp=None, copier=False):
        if timestamp is None:
            now = time.time() 
        else:
            now = unixTime(timestamp)
        timeTuple = self.maketimetuple(now)
            
        pathName = makeStoragePathName(timeTuple,self.quantum)
        pathName = os.path.join(self.groupRoot,pathName)

        if not os.path.exists(pathName): 
            os.makedirs(pathName)
        targetName = os.path.join(pathName,os.path.split(source)[-1])

        a = LiveArchive(source, targetName, self)
        if not copier:
            if a.startUpdate():
                self.liveArchiveDict[source] = a
                # print "LiveArchive started for source %s, timestamp %s, target %s" % (source, timestamp, targetName)
            else:
                pass
                # print "LiveArchive failed"
        else:
            # Archive all the old files in the source directory first
            sourceDir = os.path.split(source)[0]
            for root, dirs, files in os.walk(sourceDir):
                for filename in files:
                    path = os.path.join(root,filename)
                    if source not in path:
                        #print "Cleaning...", path
                        self.archiveData(path, True, None)
            if a.startCopy():
                self.liveArchiveDict[source] = a
                Log("LiveArchive started for source %s, timestamp %s, target %s" % (source, timestamp, targetName))
            else:
                Log("LiveArchive failed")
        
    def stopLiveArchive(self, source, copier=False):
        if source in self.liveArchiveDict:
            a = self.liveArchiveDict[source]
            if not copier:
                a.stopUpdate()
            else:
                a.stopCopy()
            # print "LiveArchive stopped for source %s" % (source,)
        else:
            pass
            # print "No valid live archive for %s" % (source,)

    def archiveData(self, source, removeOriginal=False, timestamp=None):
        """Store the specified data in the group, setting its modification time to the current time. "source" may either be a string
        specifying a file name or a tuple consisting of a data descriptor and the data"""
        try:
            if isinstance(source, tuple):
                sourceIsPath = False
                sourceFileName = "%s" % source[0]
            else:
                sourceIsPath = True
                sourceFileName = source

            if self.aggregationCount != 0 or self.compress: # Use zip to aggregate / compress data
                try:
                    self.zipSource(source,self.tempFileName)
                    fileToArchive = self.tempFileName

                except Exception, e:
                    #some problem working with the zip file, we should kill it and start fresh...
                    Log("Exception raised when adding to zip file.  File skipped and a new zip will be started on the next archive.",
                        dict(AggregateFile = self.tempFileName,
                             StoredGroup = self.name,
                             StoredData = sourceFileName,
                             Verbose = "Exception = %s %r" % (e, e)))
                    if not deleteFile(self.tempFileName): 
                        self.aggregation = 0
                    return
            else: # We are not aggregating and not compressing, so copy to temporary file if data are being sent as a string
                if not sourceIsPath:
                    tempFP = file(self.tempFileName, "wb")
                    shutil.copyfileobj(StringIO(source[1]), tempFP)
                    tempFP.close()
                    fileToArchive = self.tempFileName
                else: # Just store a file
                    fileToArchive = sourceFileName

            # If we are aggregating, return immediately unless the aggregation count has been reached
            if self.aggregationCount != 0:
                self.aggregation += 1
                if self.aggregation < self.aggregationCount: return
            self.aggregation = 0
            status = self.archiveFile(fileToArchive, sourceFileName, removeOriginal, timestamp)
            # If archiving fails, do not remove original
            removeOriginal = removeOriginal and status
        finally:
            if removeOriginal and sourceIsPath and os.path.exists(source):
                deleteFile(source)

    def makeSpace(self,nBytes,nFiles):
        """ Makes space the archive group by deleting old files as necessary so that we can add the specified number of
        bytes and files. Adds nBytes and nFiles to the current counts. This function can be called with negative nBytes or
        nFiles to indicate that some data or files have been deleted.
        
        Returns only when the cleanup is complete. This function is protected by a lock so that only 
        a single thread can execute it at once """
        self.makeSpaceLock.acquire()
        try:
            if self.maxSize > 0 and nBytes > self.maxSize:
                Log("Cannot fit data into archive group %s" % (self.name,),Level=3)
                return False
            nLoops = 0 
            while (self.maxSize > 0 and self.byteCount + nBytes > self.maxSize) or \
                  (self.maxCount > 0 and self.fileCount + nFiles > self.maxCount):
                # Delete files and directories starting with the oldest
                self._deleteOldest()
                nLoops += 1
                if nLoops == 100:
                    Log("More than 100 deletions required in group %s to make space for new data" % (self.name,),Level=2)
            self.byteCount += nBytes
            self.fileCount += nFiles
            return True
        finally:
            self.makeSpaceLock.release()

    def archiveFile(self, fileToArchive, sourceFileName=None, removeOriginal=True, timestamp=None):
        # Once we get here, we have something to be archived
        if not os.path.exists(fileToArchive):
            raise ValueError,"Cannot archive non-existent file: %s" % (fileToArchive,)

        # If timestamp is None, use current time to store file in the correct location (local or GMT)
        #  otherwise use the specified timestamp
        if timestamp is None:
            now = time.time() 
        else:
            now = unixTime(timestamp)
        timeTuple = self.maketimetuple(now)
        
        # The storage path for files to be uploaded is different from files to be archived locally
        if self.uploadEnabled:
            pathName = os.path.join(self.uploadRetryPath, makeStoragePathName(timeTuple,self.quantum))
        else:
            pathName = os.path.join(self.groupRoot, makeStoragePathName(timeTuple,self.quantum))

        renameFlag = True
        # Determine the target sourceFiles
        # The only case when sourceFileName is None is when the Archiver computes the temporary files
        if self.aggregationCount == 0 and sourceFileName != None:
            if self.compress:
                targetName = os.path.split(sourceFileName)[-1]+".zip"
            else:
                targetName = os.path.split(sourceFileName)[-1]
                renameFlag = removeOriginal
        else:
            targetName = time.strftime(self.name+"_%Y%m%d_%H%M%S.zip",timeTuple)
                
        # Upload file to data warehouse if required
        if self.uploadEnabled:
            if self.uploader.upload(fileToArchive, targetName) == "OK":
                Log("(Upload) %s uploaded" % (targetName,))
                print "(Upload) %s uploaded" % (targetName,)
                if renameFlag:
                    deleteFile(fileToArchive)
                return True
            else:
                self.retryUploadNeeded = True
                Log("(Upload) Failed to upload %s" % (targetName,))
                print "(Upload) Failed to upload %s" % (targetName,)
                # Upload has failed, so archive those files locally just like others

        # Determine size of new file to determine if it will fit
        # Get rid of the oldest file until total file size or total file count can fit
        nBytes = os.path.getsize(fileToArchive)
        # Returns True if archiving succeeded
        status = False
        # First make room for the file by deleting old files, if necessary
        if self.makeSpace(nBytes, 1):
            if not os.path.exists(pathName): 
                os.makedirs(pathName)
                
            targetName = os.path.join(pathName, targetName)
            if os.path.exists(targetName):
                # Replace existing file
                try:
                    oldBytes = os.path.getsize(targetName)
                    os.chmod(targetName,stat.S_IREAD | stat.S_IWRITE)
                    os.remove(targetName)
                    self.makeSpace(-oldBytes, -1)
                except OSError, e:
                    Log("Error removing file %s. %s" % (targetName,e))
            try:
                if renameFlag:
                    os.rename(fileToArchive,targetName)
                else:
                    shutil.copy2(fileToArchive,targetName)
                # On success, touch file modification and last access times, and increment the byte and file counts
                os.utime(targetName,(now,now))
                status = True
            except IOError,e:
                Log("IOError renaming or copying file to %s. %s" % (targetName,e))
            except OSError,e:
                Log("OSError renaming or copying file to %s. %s" % (targetName,e))
                
        # Make sure the temporary file is gone
        if os.path.exists(self.tempFileName): 
            deleteFile(self.tempFileName)
        return status
        
    def retryUpload(self):
        """Use the treeWalker to upload the newest file in the "upload" directory. Returns the number of
        bytes freed, number of file uploaded (0 or 1), and the name of the file uploaded,.
        Also updates self.fileCount and self.byteCount as a side-effect.
        """
        # Once we get here, the data upload function is enabled and some local files are waiting to be uploaded
        self.makeSpaceLock.acquire()
        nBytes = 0
        nFiles = 0
        name = None
        try:
            # Always restart the generator
            self.uploadTreeWalker = walkTree(self.uploadRetryPath,sortDir=sortByName,sortFiles=sortByMtime,reversed=True)
            type, name = self.uploadTreeWalker.next()
        except Exception, err:
            print "%r" % err
            self.retryUploadNeeded = False
            return nBytes, nFiles, name
        else:
            if type == "file":
                nBytes, nFiles = self._retryUploadFile(name)
            else: # Deal with directories
                while type != "file":
                    if name == self.uploadRetryPath:
                        self.retryUploadNeeded = False
                        break
                    else:
                        try:
                            self._deleteUploadDir(name)
                            type, name = self.uploadTreeWalker.next()
                        except:
                            break
                if type == "file":
                    nBytes, nFiles = self._retryUploadFile(name)

            self.byteCount -= nBytes
            self.fileCount -= nFiles
            return nBytes, nFiles, name
        finally:
            self.makeSpaceLock.release()
            
    def _retryUploadFile(self, name):
        nBytes = 0
        nFiles = 0
        targetName = os.path.split(name)[-1]
        try:
            if self.uploader.upload(name, targetName) == "OK":
                Log("(Retry Upload) %s uploaded" % (name,))
                print "(Retry Upload) %s uploaded" % (name,)
                nBytes = os.path.getsize(name)
                nFiles = 1
                deleteFile(name)
        except Exception, err:
            print "_retryUploadFile Error: %r" % err
        return nBytes, nFiles
        
    def _deleteUploadDir(self, name):
        try:
            os.chmod(name,stat.S_IREAD | stat.S_IWRITE)
            os.rmdir(name)
            Log("(Retry Upload) Directory %s deleted" % (name,))
            print "(Retry Upload) Directory %s deleted" % (name,)
        except Exception, err:
            print "_deleteUploadDir Error: %r" % err
                    
    def updateAndGetArchiveSize(self):
        """
        Determine the number of files and number of bytes presently in the archive group.
        Update and return self.fileCount and self.byteCount.
        """
        fileCount = 0
        byteCount = 0
        for root, dirs, files in os.walk(self.groupRoot):
            fileCount += len(files)
            byteCount += sum([os.path.getsize(os.path.join(root, fname)) for fname in files])
        self.fileCount = fileCount
        self.byteCount = byteCount
        return fileCount, byteCount

    def getFileNames(self,queue):
        """Get a list of file names for this storage group sorted in order of modification time and place it on the
        specified queue"""
        queue.put([os.path.split(name)[-1] for type,name in walkTree(self.groupRoot,sortDir=sortByName,sortFiles=sortByMtime,reversed=False)
                   if type == 'file'])

    def _deleteOldest(self):
        """Use the treeWalker to remove the oldest file or directory in the archive group. Returns the number of
        bytes freed, number of files removed, the name of the file or directory removed, and a status message.
        Also updates self.fileCount and self.byteCount as a side-effect"""
        try:
            type, name = self.treeWalker.next()
        except StopIteration:
            # We have run out, restart the generator at the root
            self.updateAndGetArchiveSize()
            self.treeWalker = walkTree(self.groupRoot,sortDir=sortByName,sortFiles=sortByMtime,reversed=False)
            type, name = self.treeWalker.next()
        
        if type == 'file':
            nBytes = os.path.getsize(name)
            nFiles = 1
            try:
                os.chmod(name,stat.S_IREAD | stat.S_IWRITE)
                os.remove(name)
                msg = 'ok'
            except OSError,e:
                nBytes = 0
                nFiles = 0
                msg = '%s' % (e,)
        else: # Deal with directories
            nBytes = 0
            nFiles = 0
            if name == self.groupRoot:
                msg = 'root'
            else:
                try:
                    os.chmod(name,stat.S_IREAD | stat.S_IWRITE)
                    os.rmdir(name)
                    msg = 'ok'
                except OSError,e:
                    msg = '%s' % (e,)
        self.byteCount -= nBytes
        self.fileCount -= nFiles
        return nBytes, nFiles, name, msg
        
    def _removeEmptySubdirs(self):
        for root, dirs, files in os.walk(self.groupRoot):
            for dirname in dirs:
                try: # Remove empty directories
                    os.rmdir(os.path.join(root,dirname))
                except:
                    pass
                    
class Archiver(object):
    """The archiver manages storage of data and files, placing them in FIFO order into storage groups whose sizes may be
    specified."""
    def __init__(self,configFile):
        self.configFile = configFile
        if not self.LoadConfig(self.configFile):
            Log("Failed to load config.")
            return
        self.storageRoot = os.path.abspath(self.storageRoot)
        if not os.path.exists(self.storageRoot):
            os.makedirs(self.storageRoot)
            Log("Creating archive directory %s" % (self.storageRoot,))
        self.storageGroups = {}
        for groupName in self.storageGroupNames:
            self.storageGroups[groupName] = ArchiveGroup(groupName,self)
            Log("Opening storage group %s" % (groupName,))

    def startServer(self):
        #Now set up the RPC server...
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_ARCHIVER),
                                               ServerName = "Archiver",
                                               ServerDescription = "The archive manager that manages usage of storage space.",
                                               ServerVersion = __version__,
                                               threaded = True)
        #Register the rpc functions...
        self.rpcServer.register_function(self.RPC_StartLiveArchive, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_StopLiveArchive, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_ArchiveData, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_ArchiveFile, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_CopyFileDates, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_CopyRecentFiles, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_CopyAllFiles, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_GetGroupList, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_GetGroupInfo, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_RefreshGroupStats, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_GetFileNames, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_DoesFileExist, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_GetLiveArchiveFileName, NameSlice = 4)
        self.rpcServer.serve_forever()

    def LoadConfig(self,filename):
        self.config = CustomConfigObj(filename)
        basePath = os.path.split(filename)[0]
        try:
            self.storageRoot = os.path.join(basePath, self.config.get(_MAIN_CONFIG_SECTION,'StorageRoot'))
            
            # For S3 uploader
            uploadBucketName = self.config.get(_MAIN_CONFIG_SECTION, "UploadBucketName", "picarro_analyzerup")
            try:
                analyzerId = CRDS_Driver.fetchInstrInfo("analyzername")
                if analyzerId == None:
                    analyzerId = "Unknown"
            except Exception, err:
                print err
                analyzerId = "Unknown"
            self.uploader = S3Uploader(uploadBucketName, analyzerId)
            self.retryUploadInterval = self.config.getfloat(_MAIN_CONFIG_SECTION, "RetryUploadInterval", 30.0)
            
            # Fetch names of storage groups
            self.storageGroupNames = self.config.list_sections()
            self.storageGroupNames.remove(_MAIN_CONFIG_SECTION)
        except:
            Log("Load config failed. %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
            return False
        return True

    def RPC_StartLiveArchive(self, groupName, sourceFile, timestamp = None, copier = False):
        """Create a 'live' archive of the source file in the specified archive group"""
        sourceFile = os.path.abspath(sourceFile)
        group = self.storageGroups[groupName]
        if not os.path.exists(sourceFile):
            raise ValueError,"Source file %s does not exist" % (sourceFile,)
        group.cmdQueue.put(("startLiveArchive",(sourceFile, timestamp, copier)))
        return "startLiveArchive command queued for group %s" % (groupName,)
    
    def RPC_GetLiveArchiveFileName(self,groupName,sourceFile):
        try:
            group = self.storageGroups[groupName]
            return (True,os.path.abspath(group.liveArchiveDict[sourceFile].destPathName))
        except:
            return (False,sourceFile)
        
    def RPC_StopLiveArchive(self, groupName, sourceFile, copier = False):
        """Stop a previously started 'live' archive of the source file in the specified archive group"""
        sourceFile = os.path.abspath(sourceFile)
        group = self.storageGroups[groupName]
        group.cmdQueue.put(("stopLiveArchive",(sourceFile, copier)))
        return "stopLiveArchive command queued for group %s" % (groupName,)
        
    def RPC_ArchiveFile(self, groupName, sourceFile, removeOriginal = True, timestamp = None):
        """Archive the file SourceFile according to the rules of the storage group groupName. If removeOriginal
        is true, the source file is deleted when archival is done. The archive time is the current time, unless
        an explicit timestamp is specified."""
        sourceFile = os.path.abspath(sourceFile)
        group = self.storageGroups[groupName]
        if not os.path.exists(sourceFile):
            raise ValueError,"Source file %s does not exist" % (sourceFile,)
        group.cmdQueue.put(("archiveData",(sourceFile, removeOriginal, timestamp)))
        return "archiveFile command queued for group %s" % (groupName,)

    def RPC_ArchiveData(self, groupName, dataName, wrappedData, timestamp = None):
        """Archive the named dataBytes according to the rules of the storage group groupName. 
        The archive time is the current time, unless an explicit timestamp is specified."""
        group = self.storageGroups[groupName]
        group.cmdQueue.put(("archiveData",((dataName,wrappedData.data), False, timestamp)))
        return "archiveData command queued for group %s" % (groupName,)

    def RPC_DoesFileExist(self,groupName,fileName,timestamp):
        """Determine if the specified file exists in the specified archive group for the given timestamp.
            Throws exception if archive group does not exist."""
        group = self.storageGroups[groupName]
        return group.doesFileExist(fileName,timestamp)
        
    def RPC_CopyFileDates(self, groupName, startDate_s, stopDate_s, destDir, uniqueFileNames = False, timeOut = 30):
        """Copies archived files in groupName from startDate_s to stopDate_s to destDir. Both startDate_s and
        stopDate_s are in "seconds since epoch". The date checked is the file modification on the archive file.
        For aggregates, this means the zip file, not the contents. Returns number of files copied, or raises the
        Queue.Empty exception if a timeout occurs.

        If uniqueFileNames == True, a group-unique prefix is added to each destination file."""
        group = self.storageGroups[groupName]
        resultQueue = Queue.Queue(0)
        group.cmdQueue.put(("copyFiles",(destDir,startDate_s,stopDate_s,uniqueFileNames,resultQueue)))
        return resultQueue.get(timeout=timeOut)

    def RPC_CopyRecentFiles(self, groupName, lengthOfTime_s, destDir, uniqueFileNames = False, timeOut = 30):
        """Copies archived files in groupName in the last lengthOfTime_s to destDir. Both startDate_s and
        stopDate_s are in "seconds since epoch". The date checked is the file modification on the archive file.
        For aggregates, this means the zip file, not the contents. Returns number of files copied, or raises the
        Queue.Empty exception if a timeout occurs.

        If uniqueFileNames == True, a group-unique prefix is added to each destination file."""
        group = self.storageGroups[groupName]
        now = time.time()
        resultQueue = Queue.Queue(0)
        group.cmdQueue.put(("copyFiles",(destDir,now-lengthOfTime_s,now,uniqueFileNames,resultQueue)))
        return resultQueue.get(timeout=timeOut)

    def RPC_CopyAllFiles(self, groupName, destDir, uniqueFileNames = False, timeOut = 30):
        """Copies all archived files in groupName to destDir. Both startDate_s and stopDate_s are in
        "seconds since epoch". The date checked is the file modification on the archive file.
        For aggregates, this means the zip file, not the contents. Returns number of files copied, or raises the
        Queue.Empty exception if a timeout occurs.

        If uniqueFileNames == True, a group-unique prefix is added to each destination file."""
        group = self.storageGroups[groupName]
        resultQueue = Queue.Queue(0)
        group.cmdQueue.put(("copyFiles",(destDir,None,None,uniqueFileNames,resultQueue)))
        return resultQueue.get(timeout=timeOut)

    def RPC_GetFileNames(self, groupName, timeOut = 30):
        """Gets the list of file names in the specified storage group groupName. Since this is potentially a lengthy
        operation, a timeout may be specified on the operation of this function"""
        group = self.storageGroups[groupName]
        resultQueue = Queue.Queue(0)
        group.cmdQueue.put(("getFileNames",(resultQueue,)))
        return resultQueue.get(timeout=timeOut)

    def RPC_GetGroupList(self):
        """Gets the list of storage group names"""
        return self.storageGroups.keys()

    def RPC_GetGroupInfo(self,groupName):
        """Gets information about the specified storage group groupName"""
        group = self.storageGroups[groupName]
        return dict(fileCount = group.fileCount, byteCount = group.byteCount,
                    compress = group.compress, aggregationCount = group.aggregationCount,
                    StorageDir = group.groupRoot)

    def RPC_RefreshGroupStats(self,groupName):
        """Re-traverses the tree associated with groupName to refresh the file and byte counts"""
        group = self.storageGroups[groupName]
        group.cmdQueue.put(("refreshStats",()))
        return "refreshStats command queued for group %s" % (groupName,)

def HandleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help","test"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    executeTest = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)
    else:
        if "--test" in options:
            executeTest = True

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (configFile, executeTest)

HELP_STRING = \
"""\
Archiver.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./Archiver.ini"

"""

def PrintUsage():
    print HELP_STRING

def main():
    #Get and handle the command line options...
    configFile, test = HandleCommandSwitches()
    ar = Archiver(configFile)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    if test:
        fname = "c:/temp/AADS06wlm.dat"
        seqnum = 0
        while True:
            tmpName = "c:/temp/seq%07d.dat" % (seqnum,)
            seqnum += 1
            shutil.copy2(fname,tmpName)
            ar.RPC_ArchiveFile("Spectra",tmpName,True)
            print "%s" % (ar.RPC_GetGroupInfo("Spectra"),)
            # ar.storageGroups["Spectra"].archiveData(tmpName,removeOriginal=True)
            time.sleep(0.5)
    else:
        ar.startServer()

if __name__ == "__main__":
    try:
        main()
    except:
        tbMsg = traceback.format_exc()
        print "Unhandled exception trapped by last chance handler"
        print "%s" % (tbMsg,)
