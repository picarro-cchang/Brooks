"""
File Name: Archiver.py
Purpose:

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
import sys
import os
import getopt
import threading
import shutil
import time
import Queue
import zipfile
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_ARCHIVER, RPC_PORT_DRIVER, RPC_PORT_SUPERVISOR
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.timestamp import unixTime
from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.SingleInstance import SingleInstance
from Host.Common.LinuxWindowsTools import makeDirs

APP_NAME = "Archiver"
__version__ = 1.0
CONFIG_DIR = os.environ["PICARRO_CONF_DIR"]
LOG_DIR = os.environ["PICARRO_LOG_DIR"]
_DEFAULT_CONFIG_NAME = "Archiver.ini"
_MAIN_CONFIG_SECTION = "MainConfig"

EventManagerProxy_Init(APP_NAME, DontCareConnection=True)
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy(
    "http://localhost:%d" %
    RPC_PORT_DRIVER,
    APP_NAME,
    IsDontCareConnection=False)


def makeStoragePathName(struct_time, level=3):
    """
    Convert a struct_time object into a relative path name, using entries in
    struct_time up to the specified level:
    level = 1: year only
    level = 2: include month
    level = 3: include monthday
    """
    if level < 1 or level > 3:
        raise ValueError(
            "Invalid level in makeStoragePathName (valid value: 0...6)")
    else:
        pathList = ["%04d" % (struct_time[0],)]
        for i in range(1, level):
            pathList.append("%02d" % (struct_time[i],))
        return "-".join(pathList)


class LiveArchive(object):
    """
    Class used to monitor a file generated by the data logger and which
    copies any changes to a user-accessible file opened for shared reading and
    exclusive writing. Runs in a separate thread.
    """

    def __init__(self, srcPathName, destPathName, archiveGroup):
        self.srcPathName = srcPathName
        self.destPathName = destPathName
        self.updating = False
        self.srcFp = None
        self.archiveGroup = archiveGroup

    # Live updating for data logs
    def startUpdate(self):
        self.destFp = file(self.destPathName, "w")
        if not self.destFp:
            Log('Cannot open live archive file %s' %
                self.destPathName, Level=2)
            return False

        self.updating = True
        self.srcFp = open(self.srcPathName, 'rb')
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
            self.destFp.write(data)

    def stopUpdate(self):
        self.updating = False
        self.destFp.close()
        if self.srcFp:
            self.srcFp.close()
        self.updateThread.join(15.0)
        if self.updateThread.isAlive():
            Log('Live archive %s cannot be closed' %
                self.destPathName, Level=3)


class ArchiveGroup(object):
    """Class associated with each storage group. This corresponds to a directory
    called "groupName" created under the storageRoot of the archiver. Under this
    directory, files are stored in a tree organized by file modification time in
    GMT. The number of levels of the tree (potentially year, month, day, hour,
    minute and second) is determined by "quantum".

    Depending on the options specified for the storage group, data may be
    aggregated and/or compressed before storage.  Such compression and
    aggregation are handled by the zipfile module.

    Since operations on an archive group may potentially take awhile, they are
    carried out in a separate (daemonic) thread of execution called
    "serverThread". Commands to be executed are passed via a queue called
    cmdQueue. This allows the archiver to handle supervisor pings even if it has
    to do lengthy operations on the disk."""

    def __init__(self, groupName, archiver):
        assert isinstance(archiver, Archiver)
        self.name = groupName
        self.groupRoot = os.path.join(archiver.storageRoot, groupName)
        self.maketimetuple = time.gmtime
        self.quantum = archiver.config.getint(groupName, 'Quantum', 3)
        self.compress = archiver.config.getboolean(groupName, "Compress", False)
        self.aggregationCount = archiver.config.getint( groupName, "AggregationCount", 0)
        self.aggregation = 0
        self.cmdQueue = Queue.Queue(0)  # Queue for commands
        # Enqueue command to initialize the archive group
        self.cmdQueue.put(("init", ()))
        self.serverThread = threading.Thread(target=self.server)
        self.fileCount = -1

        # Create temporary filename for compression and aggregation
        self.tempFileName = os.path.join(
            archiver.storageRoot, groupName + ".zip")
        if os.path.exists(self.tempFileName):
            self.cmdQueue.put(("archiveFile", (self.tempFileName,)))
        # Dictionary of live archives by source file name
        self.liveArchiveDict = {}
        self.serverThread.setDaemon(True)
        self.serverThread.start()

    def server(self):
        """
        This is the main thread function which listens to requests from the
        cmdQueue and executes them sequentially.  Commands on cmdQueue consist
        of a pair (command,argumentList). The command is looked up using
        cmdDict, and the arguments are passed to the appropriate function.
        """
        cmdDict = dict(archiveData=self.archiveData,
                       archiveFile=self.archiveFile,
                       startLiveArchive=self.startLiveArchive,
                       stopLiveArchive=self.stopLiveArchive)
        # self.updateAndGetArchiveSize()
        while True:
            try:
                cmd, args = self.cmdQueue.get()
                startTime = time.time()
                cmdDict[cmd](*args)
                if cmd != "archiveData":
                    Log("Archiver command %s took %s seconds" %
                        (cmd, time.time() - startTime))
                time.sleep(1)
            except Exception as exc:
                Log("Exception in ArchiveGroup server", dict(
                    GroupName=self.name), Verbose="Exception = %s %r" % (exc, exc))

    def zipSource(self, source, targetPath):
        """
        Compresses the source (either a filename or a (name,data) tuple) and
        puts it into targetPath.
        """
        writeMode = "w"
        if self.aggregationCount > 0 and os.path.exists(targetPath):
                writeMode = "a"

        if self.compress:
            compressMode = zipfile.ZIP_DEFLATED
        else:
            compressMode = zipfile.ZIP_STORED

        zf = zipfile.ZipFile(targetPath, writeMode, compressMode)

        # Abort if the file is already full.  If this happens something is wrong
        # with the file or destination directory.  This doesn't fix the problem
        # but it does prevent the file growing uncontrollably.
        #
        numFilesInTheZipFile = len(zf.namelist())
        if numFilesInTheZipFile > self.aggregationCount:
            Log('Live archive %s is full. Move operation has failed.' %
                targetPath, Level=3)
            zf.close()
            del zf
            return

        try:
            if isinstance(source, tuple):
                sourceName, sourceData = source
                zf.writestr(sourceName, sourceData)
            else:
                # Need to convert filename to a str to avoid Unicode errors
                zf.write(str(source))

        finally:
            zf.close()
            del zf

    def startLiveArchive(self, source, timestamp=None, copier=False):
        if timestamp is None:
            now = time.time()
        else:
            now = unixTime(timestamp)
        timeTuple = self.maketimetuple(now)

        pathName = makeStoragePathName(timeTuple, self.quantum)

        # RSF
        # Hack to organize by date at the top level then by type
        # i.e. Log/Archive/2018/08/DataLog_User/<file>
        #
        # Actually it's flat, 2018-08-11
        # RDF files are a special case because they are large so
        # we append "RDF" to the directory name.  This is to make sorting
        # and deleting only the RDF files easier.
        if ("RDF" in self.groupRoot):
            pathName += "-RDF"
        pathName = os.path.join(
            os.path.split(
                self.groupRoot)[0], pathName, os.path.basename(
                self.groupRoot))  # date before file type name

        if not os.path.exists(pathName):
            makeDirs(pathName)
        targetName = os.path.join(pathName, os.path.split(source)[-1])

        a = LiveArchive(source, targetName, self)
        if not copier:
            if a.startUpdate():
                self.liveArchiveDict[source] = a
            else:
                Log("Archiver: Failed to start live archive")
        else:
            pass

    def stopLiveArchive(self, source, copier=False):
        if source in self.liveArchiveDict:
            a = self.liveArchiveDict[source]
            a.stopUpdate()
        else:
            pass

    def archiveData(self, source, removeOriginal=False, timestamp=None):
        """Store the specified data in the group, setting its modification time
        to the current time. "source" may either be a string specifying a file
        name or a tuple consisting of a data descriptor and the data"""
        try:
            if isinstance(source, tuple):
                sourceIsPath = False
                sourceFileName = "%s" % source[0]
            else:
                sourceIsPath = True
                sourceFileName = source

            if self.aggregationCount != 0 or self.compress:  # Use zip to aggregate / compress data
                try:
                    self.zipSource(source, self.tempFileName)
                    fileToArchive = self.tempFileName
                except Exception as e:
                    # some problem working with the zip file, we should kill it
                    # and start fresh...
                    Log("Exception raised when adding to zip file. \
                    File skipped and a new zip will be started on the next archive.",
                        dict(AggregateFile=self.tempFileName,
                             StoredGroup=self.name,
                             StoredData=sourceFileName,
                             Verbose="Exception = %s %r" % (e, e)))
                    return
            else:
                # We are not aggregating and not compressing, so copy to
                # temporary file if data are being sent as a string
                if not sourceIsPath:
                    pass
                else:  # Just store a file
                    fileToArchive = sourceFileName

            # If we are aggregating, return immediately unless the aggregation
            # count has been reached
            if self.aggregationCount != 0:
                self.aggregation += 1
                if self.aggregation < self.aggregationCount:
                    return
            self.aggregation = 0
            status = self.archiveFile(
                fileToArchive,
                sourceFileName,
                removeOriginal,
                timestamp)
            # If archiving fails, do not remove original
            removeOriginal = removeOriginal and status
        finally:
            if removeOriginal and sourceIsPath and os.path.exists(source):
                os.remove(source)

    def archiveFile(self, fileToArchive, sourceFileName=None,
                    removeOriginal=True, timestamp=None):
        # Once we get here, we have something to be archived
        if not os.path.exists(fileToArchive):
            raise ValueError(
                "Cannot archive non-existent file: %s" %
                (fileToArchive,))

        # If timestamp is None, use current time to store file in the correct
        # location (local or GMT) otherwise use the specified timestamp
        if timestamp is None:
            now = time.time()
        else:
            now = unixTime(timestamp)
        timeTuple = self.maketimetuple(now)

        # RSF
        # Hack to organize by date at the top level then by type
        # i.e. Log/Archive/2018/08/DataLog_User/<file>
        #
        # Actually it's flat, 2018-08-11
        # RDF files are a special case because they are large so
        # we append "RDF" to the directory name.  This is to make sorting
        # and deleting only the RDF files easier.
        pathName = makeStoragePathName(timeTuple, self.quantum)
        if("RDF" in self.groupRoot):
            pathName = pathName + "-RDF"
        pathName = os.path.join(
            os.path.split(
                self.groupRoot)[0], pathName, os.path.basename(
                self.groupRoot))  # date before file type name

        renameFlag = True
        # Determine the target sourceFiles
        # The only case when sourceFileName is None is when the Archiver
        # computes the temporary files
        if self.aggregationCount == 0 and sourceFileName is not None:
            if self.compress:
                targetName = os.path.split(sourceFileName)[-1] + ".zip"
            else:
                targetName = os.path.split(sourceFileName)[-1]
                renameFlag = removeOriginal
        else:
            targetName = time.strftime(
                self.name + "_%Y%m%d_%H%M%S.zip", timeTuple)

        # Returns True if archiving succeeded
        status = False
        if not os.path.exists(pathName):
            makeDirs(pathName)

        targetName = os.path.join(pathName, targetName)
        try:
            if renameFlag:
                os.rename(fileToArchive, targetName)
            else:
                shutil.copy2(fileToArchive, targetName)
            # On success, touch file modification and last access times, and
            # increment the file counts
            os.utime(targetName, (now, now))
            status = True
        except IOError as e:
            Log("IOError renaming or copying file to %s. %s" % (targetName, e))
        except OSError as e:
            Log("OSError renaming or copying file to %s. %s" % (targetName, e))

        # Make sure the temporary file is gone
        if os.path.exists(self.tempFileName):
            os.remove(self.tempFileName)
        return status


class Archiver(object):
    """
    The archiver manages storage of data and files, placing them in FIFO
    order into storage groups whose sizes may be specified.
    """

    def __init__(self, configFile):
        self.configFile = configFile
        self.supervisor = CmdFIFO.CmdFIFOServerProxy(
            "http://localhost:%d" %
            RPC_PORT_SUPERVISOR,
            APP_NAME,
            IsDontCareConnection=False)
        if not self.LoadConfig(self.configFile):
            Log("Failed to load config.")
            return
        self.storageRoot = os.path.abspath(self.storageRoot)
        if not os.path.exists(self.storageRoot):
            makeDirs(self.storageRoot)
            Log("Creating archive directory %s" % (self.storageRoot,))
        self.storageGroups = {}
        for groupName in self.storageGroupNames:
            self.storageGroups[groupName] = ArchiveGroup(groupName, self)
            Log("Opening storage group %s" % (groupName,))

    def startServer(self):
        # Now set up the RPC server...
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_ARCHIVER),
                                               ServerName="Archiver",
                                               ServerDescription="Archiver",
                                               ServerVersion=__version__,
                                               threaded=True)
        self.rpcServer.register_function(
            self.RPC_StartLiveArchive, NameSlice=4)
        self.rpcServer.register_function(self.RPC_StopLiveArchive, NameSlice=4)
        self.rpcServer.register_function(self.RPC_ArchiveFile, NameSlice=4)
        self.rpcServer.register_function(
            self.RPC_GetLiveArchiveFileName, NameSlice=4)
        self.rpcServer.serve_forever()

    def LoadConfig(self, filename):
        self.config = CustomConfigObj(filename)
        try:
            self.storageRoot = os.path.join(LOG_DIR, 'Archive')
            try:
                analyzerId = CRDS_Driver.fetchInstrInfo("analyzername")
                if analyzerId is None:
                    analyzerId = "Unknown"
            except Exception as err:
                print("Exception in Archiver:", err)
                print("Link to CRDS_Driver not established, analyzer ID unknown.")
                print("You can ignore this error if running in virtual mode.")
                analyzerId = "Unknown"

            # Fetch names of storage groups
            self.storageGroupNames = self.config.list_sections()
            self.storageGroupNames.remove(_MAIN_CONFIG_SECTION)
        except BaseException:
            Log("Load config failed. %s %s" %
                (sys.exc_info()[0], sys.exc_info()[1]))
            return False
        return True

    def RPC_StartLiveArchive(self, groupName, sourceFile,
                             timestamp=None, copier=False):
        """Create a 'live' archive of the source file in the specified archive group"""
        sourceFile = os.path.abspath(sourceFile)
        group = self.storageGroups[groupName]
        if not os.path.exists(sourceFile):
            raise ValueError("Source file %s does not exist" % (sourceFile,))
        group.cmdQueue.put(
            ("startLiveArchive", (sourceFile, timestamp, copier)))
        return "startLiveArchive command queued for group %s" % (groupName,)

    def RPC_GetLiveArchiveFileName(self, groupName, sourceFile):
        try:
            group = self.storageGroups[groupName]
            return (True, os.path.abspath(
                group.liveArchiveDict[sourceFile].destPathName))
        except BaseException:
            return (False, sourceFile)

    def RPC_StopLiveArchive(self, groupName, sourceFile, copier=False):
        """
        Stop a previously started 'live' archive of the source file in the
        specified archive group
        """
        sourceFile = os.path.abspath(sourceFile)
        group = self.storageGroups[groupName]
        group.cmdQueue.put(("stopLiveArchive", (sourceFile, copier)))
        return "stopLiveArchive command queued for group %s" % (groupName,)

    def RPC_ArchiveFile(self, groupName, sourceFile,
                        removeOriginal=True, timestamp=None):
        """
        Archive the file SourceFile according to the rules of the storage group
        groupName. If removeOriginal is true, the source file is deleted when
        archival is done. The archive time is the current time, unless
        an explicit timestamp is specified.
        """
        sourceFile = os.path.abspath(sourceFile)
        group = self.storageGroups[groupName]
        if not os.path.exists(sourceFile):
            raise ValueError("Source file %s does not exist" % (sourceFile,))
        group.cmdQueue.put(
            ("archiveData", (sourceFile, removeOriginal, timestamp)))
        return "archiveFile command queued for group %s" % (groupName,)


def HandleCommandSwitches():
    shortOpts = ''
    longOpts = ["ini="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError as data:
        print "%s %r" % (data, data)
        sys.exit(1)

    # assemble a dictionary where the keys are the switches and values are
    # switch args...
    options = {}
    for o, a in switches:
        options[o] = a
    configFile = ""
    if "--ini" in options:
        configFile = os.path.join(CONFIG_DIR, options["--ini"])
        print "Config file specified at command line: %s" % configFile

    return (configFile)


def main():
    my_instance = SingleInstance(APP_NAME)
    if my_instance.alreadyrunning():
        Log("Instance of %s already running" % APP_NAME, Level=2)
    else:
        try:
            # Get and handle the command line options...
            configFile = HandleCommandSwitches()
            ar = Archiver(configFile)
            Log("%s started" % APP_NAME, Level=1)
            ar.startServer()
        except Exception as e:
            LogExc("Unhandled exception in %s: %s" % (APP_NAME, e), Level=3)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                Log("Restart request to supervisor sent", Level=0)
            else:
                Log("Restart request to supervisor not sent", Level=2)


if __name__ == "__main__":
    main()
