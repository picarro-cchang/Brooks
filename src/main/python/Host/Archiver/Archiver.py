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
    14-07-29 sze   Added conditionals for linux/windows

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
import sys
import os
import getopt
import threading
import shutil
import stat
import time
import Queue
import zipfile
from cStringIO import StringIO
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_ARCHIVER, RPC_PORT_DRIVER, RPC_PORT_SUPERVISOR
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import *
from Host.Common.timestamp import unixTime
from Host.Common.S3Uploader import S3Uploader
from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.SingleInstance import SingleInstance

APP_NAME = "Archiver"
__version__ = 1.0
CONFIG_DIR = os.environ["PICARRO_CONF_DIR"]
LOG_DIR = os.environ["PICARRO_LOG_DIR"]
_DEFAULT_CONFIG_NAME = "Archiver.ini"
_MAIN_CONFIG_SECTION = "MainConfig"

EventManagerProxy_Init(APP_NAME,DontCareConnection = True)
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
    os.remove(filename)
    return True
    # try:
    #     os.chmod(filename,stat.S_IREAD | stat.S_IWRITE)
    #     os.remove(filename)
    #     return True
    # except OSError,e:
    #     Log("Error deleting file: %s. %s" % (filename,e))
    #     return False

def sortByName(top,nameList,reversed=False):
    return []
    # nameList.sort()
    # if not reversed:
    #     return nameList
    # else:
    #     return nameList[::-1]

def sortByMtime(top,nameList,reversed=False):
    """Sort a list of files by modification time"""
    return []
    # # Decorate with the modification time of the file for sorting
    # fileList = [(os.path.getmtime(os.path.join(top,name)),name) for name in nameList]
    # fileList.sort()
    # if not reversed:
    #     return [name for t,name in fileList]
    # else:
    #     return [name for t,name in fileList[::-1]]

def walkTree(top,onError=None,sortDir=None,sortFiles=None,reversed=False):
    """Generator which traverses a directory tree rooted at "top" in bottom to top order (i.e., the children are visited
    before the parent, and directories are visited before files.) The order of directory traversal is determined by
    "sortDir" and the order of file traversal is determined by "sortFiles". If "onError" is defined, exceptions during
    directory listings are passed to this function. When the function yields a result, it is either the pair
    ('file',fileName)  or ('dir',directoryName)"""
    return
    # try:
    #     names = os.listdir(top)
    # except OSError, err:
    #     if onError is not None:
    #         onError(err)
    #     return
    # # Obtain lists of directories and files which are not links
    # dirs, nondirs = [], []
    # for name in names:
    #     fullName = os.path.join(top,name)
    #     if not os.path.islink(fullName):
    #         if os.path.isdir(fullName):
    #             dirs.append(name)
    #         else:
    #             nondirs.append(name)
    # # Sort the directories and nondirectories (in-place)
    # if sortDir is not None:
    #     dirs = sortDir(top,dirs,reversed)
    # if sortFiles is not None:
    #     nondirs = sortFiles(top,nondirs,reversed)
    # # Recursively call walkTree on directories
    # for dir in dirs:
    #     for x in walkTree(os.path.join(top,dir),onError,sortDir,sortFiles,reversed):
    #         yield x
    # # Yield up files
    # for file in nondirs:
    #     yield 'file', os.path.join(top,file)
    # # Yield up the current directory
    # yield 'dir', top

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
        return "-".join(pathList)
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
        if sys.platform == 'win32':
            self.destHandle = CreateFile(self.destPathName,GENERIC_WRITE,
                                     FILE_SHARE_READ,None,CREATE_ALWAYS,
                                     FILE_ATTRIBUTE_NORMAL,0)
            if self.destHandle == INVALID_HANDLE_VALUE:
                Log('Cannot open live archive file %s' % self.destPathName, Level=2)
                return False
        else:
            self.destFp = file(self.destPathName,"w")
            if not self.destFp:
                Log('Cannot open live archive file %s' % self.destPathName, Level=2)
                return False

        self.updating = True
        self.srcFp = open(self.srcPathName,'rb')
        if not self.srcFp:
            Log('Cannot open datalogger file %s' % self.srcPathName, Level=2)
            return False
        # self.archiveGroup.makeSpace(0,1)
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
            # self.archiveGroup.makeSpace(nBytes,0)
            if sys.platform == 'win32':
                WriteFile(self.destHandle,data)
            else:
                self.destFp.write(data)
            self.bytesCopied += nBytes

    def stopUpdate(self):
        self.updating = False
        if sys.platform == 'win32':
            CloseHandle(self.destHandle)
        else:
            self.destFp.close()
        if self.srcFp:
            self.srcFp.close()
        self.updateThread.join(15.0)
        if self.updateThread.isAlive():
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
        # RSF
        # if not os.path.exists(self.groupRoot):
        #     os.makedirs(self.groupRoot,0775)
        #     Log("Creating archive group directory %s" % (self.groupRoot,))
        # Create temporary filename for compression and aggregation
        self.tempFileName = os.path.join(archiver.storageRoot,groupName + ".zip")
        if os.path.exists(self.tempFileName):
            self.cmdQueue.put(("archiveFile",(self.tempFileName,)))
        # Dictionary of live archives by source file name
        self.liveArchiveDict = {}
        # Lock for arbitrating access to file deletion routines to make space for new data
        self.makeSpaceLock = threading.Lock()

        # For data uploading
        # self.uploader = archiver.uploader
        # self.retryUploadInterval = archiver.retryUploadInterval
        self.uploadEnabled = archiver.config.getboolean(groupName,'UploadEnabled', False)
        # self.uploadRetryPath = os.path.join(self.groupRoot, "upload")
        # Flag to scan the "upload" folder and upload any remaining files
        # self.retryUploadNeeded = True
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
                       stopLiveArchive = self.stopLiveArchive) #,
                       # retryUpload = self.retryUpload)
        self.updateAndGetArchiveSize()
        Log("Group %s, files %d, bytes %d" % (self.name,self.fileCount,self.byteCount,))
        while True:
            try:
                cmd,args = self.cmdQueue.get()
                startTime = time.time()
                cmdDict[cmd](*args)
                if cmd != "archiveData":
                    Log("Archiver command %s took %s seconds" % (cmd,time.time()-startTime))
            except Exception, exc:
                Log("Exception in ArchiveGroup server",
                    dict(GroupName = self.name), Verbose = "Exception = %s %r" % (exc, exc))

    # def retryUploadScheduler(self):
    #     return

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
        return
        # The treeWalker is used to delete the oldest entries when required
        # self.treeWalker = walkTree(self.groupRoot,sortDir=sortByName,sortFiles=sortByMtime,reversed=False)
        # Create a uploadTreeWalker to retry uploading the newest entries when required
        # self.uploadTreeWalker = walkTree(self.uploadRetryPath,sortDir=sortByName,sortFiles=sortByMtime,reversed=True)
        # Remove empty subdirectories
        # self._removeEmptySubdirs()

    def extractFiles(self,destDir, startTime=None, endTime=None, uniqueFileNames = False, resultQueue = None):
        """Extract all files between the specified starting and ending times to the destination directory. If uniqueFileNames is
           True, the group name and date code are prepended to each file. Returns the number of files copied, and places them on
           the specified resultQueue. """
        return 0


    def doesFileExist(self,fileName,timestamp):
        """Inquires if the specified file name exists in this group for the specified timestamp"""
        return True

    def startLiveArchive(self, source, timestamp=None, copier=False):
        if timestamp is None:
            now = time.time()
        else:
            now = unixTime(timestamp)
        timeTuple = self.maketimetuple(now)

        pathName = makeStoragePathName(timeTuple,self.quantum)
        # pathName = os.path.join(self.groupRoot, pathName)

        # RSF
        # Hack to organize by date at the top level then by type
        # i.e. Log/Archive/2018/08/DataLog_User/<file>
        #
        # Actually it's flat, 2018-08-11
        # RDF files are a special case because they are large so
        # we append "RDF" to the directory name.  This is to make sorting
        # and deleting only the RDF files easier.
        if ("RDF" in self.groupRoot):
            pathName = pathName + "-RDF"
        pathName = os.path.join(os.path.split(self.groupRoot)[0],
                                pathName,
                                os.path.basename(self.groupRoot)) # date before file type name

        if not os.path.exists(pathName):
            os.makedirs(pathName,0775)
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
            pass


    def stopLiveArchive(self, source, copier=False):
        if source in self.liveArchiveDict:
            a = self.liveArchiveDict[source]
            a.stopUpdate()
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
                    pass
                else: # Just store a file
                    fileToArchive = sourceFileName

            # If we are aggregating, return immediately unless the aggregation count has been reached
            if self.aggregationCount != 0:
                self.aggregation += 1
                if self.aggregation < self.aggregationCount:
                    return
            self.aggregation = 0
            print("Archiving:", fileToArchive, sourceFileName, self.aggregationCount)
            status = self.archiveFile(fileToArchive, sourceFileName, removeOriginal, timestamp)
            # If archiving fails, do not remove original
            removeOriginal = removeOriginal and status
        finally:
            if removeOriginal and sourceIsPath and os.path.exists(source):
                deleteFile(source)

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
            # pathName = os.path.join(
            #     self.groupRoot, makeStoragePathName(timeTuple, self.quantum))
            pathName = makeStoragePathName(timeTuple, self.quantum)
            # pathName = os.path.join(self.groupRoot, pathName)

            # RSF
            # Hack to organize by date at the top level then by type
            # i.e. Log/Archive/2018/08/DataLog_User/<file>
            #
            # Actually it's flat, 2018-08-11
            # RDF files are a special case because they are large so
            # we append "RDF" to the directory name.  This is to make sorting
            # and deleting only the RDF files easier.
            if("RDF" in self.groupRoot):
                pathName = pathName + "-RDF"
            pathName = os.path.join(os.path.split(self.groupRoot)[0],
                                    pathName,
                                    os.path.basename(self.groupRoot))  # date before file type name

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

        # Determine size of new file to determine if it will fit
        # Get rid of the oldest file until total file size or total file count can fit
        nBytes = os.path.getsize(fileToArchive)
        # Returns True if archiving succeeded
        status = False
        # First make room for the file by deleting old files, if necessary
        # if self.makeSpace(nBytes, 1):
        if True:
            if not os.path.exists(pathName):
                os.makedirs(pathName,0775)

            targetName = os.path.join(pathName, targetName)
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


class Archiver(object):
    """The archiver manages storage of data and files, placing them in FIFO order into storage groups whose sizes may be
    specified."""
    def __init__(self,configFile):
        self.configFile = configFile
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        if not self.LoadConfig(self.configFile):
            Log("Failed to load config.")
            return
        self.storageRoot = os.path.abspath(self.storageRoot)
        if not os.path.exists(self.storageRoot):
            os.makedirs(self.storageRoot,0775)
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
        self.rpcServer.register_function(self.RPC_ArchiveFile, NameSlice = 4)
        self.rpcServer.register_function(self.RPC_GetLiveArchiveFileName, NameSlice = 4)
        self.rpcServer.serve_forever()

    def LoadConfig(self,filename):
        self.config = CustomConfigObj(filename)
        basePath = os.path.split(filename)[0]
        try:
            self.storageRoot = os.path.join(LOG_DIR, 'Archive')

            # For S3 uploader
            # uploadBucketName = self.config.get(_MAIN_CONFIG_SECTION, "UploadBucketName", "picarro_analyzerup")
            try:
                analyzerId = CRDS_Driver.fetchInstrInfo("analyzername")
                if analyzerId == None:
                    analyzerId = "Unknown"
            except Exception, err:
                print("Link to CRDS_Driver not established, analyzer ID unknown.")
                print("You can ignore this error if running in virtual mode.")
                analyzerId = "Unknown"
            # self.uploader = S3Uploader(uploadBucketName, analyzerId)
            # self.retryUploadInterval = self.config.getfloat(_MAIN_CONFIG_SECTION, "RetryUploadInterval", 30.0)

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


def HandleCommandSwitches():
    shortOpts = 'h'
    longOpts = ["help","test","ini="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    # if "/?" in args or "/h" in args:
    #     options["-h"] = ""
    #
    # executeTest = False
    # if "-h" in options or "--help" in options:
    #     PrintUsage()
    #     sys.exit(0)
    # else:
    #     if "--test" in options:
    #         executeTest = True
    #
    # #Start with option defaults...
    configFile = ""

    if "--ini" in options:
        configFile = os.path.join(CONFIG_DIR, options["--ini"])
        print "Config file specified at command line: %s" % configFile

    return (configFile)

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
    my_instance = SingleInstance(APP_NAME)
    if my_instance.alreadyrunning():
        Log("Instance of %s already running" % APP_NAME, Level=2)
    else:
        try:
            #Get and handle the command line options...
            configFile = HandleCommandSwitches()
            ar = Archiver(configFile)
            Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
            ar.startServer()
        except Exception, e:
            LogExc("Unhandled exception in %s: %s" % (APP_NAME, e), Level=3)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                Log("Restart request to supervisor sent", Level=0)
            else:
                Log("Restart request to supervisor not sent", Level=2)


if __name__ == "__main__":
    main()
