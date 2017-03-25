# FileManager
# 
# This class is designed to make creating, closing, and writing to Picarro
# output files easier.
# It is designed to:
#       * Create files with a properly formatted[1] name.
#       * Put the file in the correct date formatted directory.
#       * Create date formatted paths as needed.
#       * Maintain a persistent file handle.
#       * Close the file if a time criteria is met.
#       * Compress and/or move the closed file as needed.
#       * Keep the directory clean by deleting orphaned/empty files.
#
# Outside this class, the API should be simple, just instantiate,
# accept data to write, and close if the analyzer is shutting down or
# there is a state change that requires starting a new file.  Internally
# this class will keep track of the current open file so the external
# code doesn't have to manipulate file handles.
#
# [1]   File names must be unique in a given directory.  Filenames should
#       have an embedded date and incremented counter so that it is easy to 
#       spot missing files and the order of the files is obvious. Example
#
#       AMADS_DAT_20170222_0000.txt
#       AMADS_DAT_20170222_0001.txt
#       AMADS_DAT_20170222_0003.txt
#
#       Key:    AMADS - analyzer type, 5 chars
#               DAT - dat file, 3 chars
#               20170222 - file created Feb 02, 2017, 8 chars
#               0000 - file counter, 0000 is the 1stfile, 0001 is 2nd, etc. 4 chars
#               txt - file is plain text, 3 chars extension
#
#       File types: DAT - standard user dat file
#                   PDT - private (Picarro only) dat file
#                   RDF - ringdown file
#                   HLT - long-term health & alarm data
#                   LOG - diagnostics log
#

import gzip
import zipfile
import bz2
import os
import errno
import glob
import re
import time
import pprint
import signal
import threading
import subprocess32
from datetime import datetime, date


class OutputFile:

    # Compression options (in enum style)
    NoCompression, Gzip, Zip, Bzip2 = range(4)

    def __init__(self,
            analyzerType,
            newFileInterval = 3600, # 3600 seconds i.e. 1 hour
            fileType = "DAT",
            fileCounter=0000,
            fileExtension="txt",
            zipType = "NoCompression"
            ):
        self._rootPathName = "/Picarro"

        self._fileHandle = None
        self._requestCloseFile = False
        self._stopWatch = None # file timer thread
        self._dateStopWatch = None

        # Keep track if we wrote data to the current file.  When we close, delete the 
        # file if we haven't written any data so that we don't pollute the file system
        # with empty files.  This can happen if we are repeatedly starting and stopping
        # the code before the system starts measuring.
        self._wroteToFile = False

        # Keep track if this object was started.  Starting will init the directory,
        # file, and stop watch and must only be run once otherwise we'll have unattached
        # open file handles.
        self._startMethodNotCalled = True

        # File name components
        self._newFileInterval = newFileInterval
        self._analyzerType = analyzerType
        self._fileType = fileType
        self._fileDate = ""
        self._fileCounter = fileCounter
        self._fileExtension = fileExtension

        self._zipType = None
        if "gzip" == zipType.lower():
            self._zipType = OutputFile.Gzip
        elif "zip" == zipType.lower():
            self._zipType = OutputFile.Zip
        elif "bzip2" == zipType.lower():
            self._zipType = OutputFile.Bzip2
        else:
            self._zipType = OutputFile.NoCompression

        self._debugMode = False

        # Path to the currently open file, set when the file is created
        self._currentDatePath = ""
        self._currentOpenFileName = ""

    def getSettings(self):
        """
        Get ini settings.

        TBD. I don't know if it will read directly from an ini file or get settings
        from a config tool that parses ini files.
        """
        #print("Analyzer Type: %s" % self._analyzerType)
        #print("File Type: %s" % self._fileType)
        #print("File Date: %s" % self._fileDate)

    def start(self):
        """
        Create the destination directories and files. Start the new file stop watch.
        This is not done in the init because there maybe a lengthy analyzer initialization
        where there is no data to write.
        """
        if self._startMethodNotCalled:
            self.makeDirs()
            self.openNewFile()
            self._stopWatch = IntervalTimer(self._newFileInterval, "NewFileTimer", self.closeFileAndOpenANewOne)
            self._stopWatch.start()
        return

    def stop(self):
        """
        Stop the new file timer and close (and compress) the output file.
        """
        self._stopWatch.stop()
        time.sleep(2.0)
        self.closeFile()
        return

    def isRunning(self):
        return self._stopWatch.is_alive()

    def closeFileAndOpenANewOne(self):
        """
        Wrap file closing and opening into a single callback function for a file timer.
        """
        self.closeFile()
        self.openNewFile()
        return

    def openNewFile(self):
        self.makeDirs()
        self._currentDatePath = self.getNewDatePath()
        self._currentOpenFileName = self.getNewFileName()
        fn = os.path.join(self._currentDatePath, self._currentOpenFileName)
        self._fileHandle = open(fn,"w")
        self._requestCloseFile = False
        return

    def closeFile(self):
        """
        Close the open output file.
        If useGzip is True, make a gzip'd copy in place and
        delete the uncompressed original.
        """
        txtFile = self._fileHandle.name
        self._fileHandle.close()
        if self._wroteToFile:
            if self._zipType == OutputFile.Gzip:
                subprocess32.Popen(["gzip", txtFile])
            if self._zipType == OutputFile.Bzip2:
                subprocess32.Popen(["bzip2", txtFile])
            if self._zipType == OutputFile.Zip:
                subprocess32.Popen(["zip", "-mj", txtFile+".zip", txtFile])
        else:
            os.remove(txtFile)
        self._wroteToFile = False
        self._requestCloseFile = False
        return

    def getDateNow(self):
        """
        Return the current date in YYYYMMDD format.
        The timezone is the local (system) setting.
        """
        dateStr = date.today().strftime("%Y%m%d")
        if(self._debugMode):
            dateStr = self._fileDate #self._testDate
        return dateStr

    def getNewDatePath(self):
        """
        Determine the date path name based upon the current time.
        """
        return os.path.join(self._rootPathName, self.getDateNow())

    def makeDirs(self):
        """
        Recursively make directories as needed.
        """
        # If the directory already exists the code will thrown
        # a EEXIST error.  See the Python errno module and
        # the "errno" Linux man page.  We ignore this exception
        # and throw anything else up to the parent.
        try:
            os.makedirs(self.getNewDatePath())
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        return

    def makeFileName(self, counter):
        """
        Given a number between 0 and 9999, make a  correctly formatted file
        name based upon the analyzer and file types set at initialization.
        Example: AMADS_DAT_20170223_0015.txt

        If counter is not a valid int, it is inserted unmodified so that one
        could generate a regexp ready string.
        Example: makeFileName('????') returns AMADS_DAT_20170223_????.txt
        """
        self._fileDate = self.getDateNow()
        cnt = counter
        try:
            cnt = int(counter)
        except:
            pass

        if(cnt >= 0 and cnt <= 9999):
            rootName = '_'.join([self._analyzerType,
                                self._fileType,
                                self._fileDate,
                                str(cnt).zfill(4)
                                ])
        # else do a literal substitution for wildcard matches
        else:
            rootName = '_'.join([self._analyzerType,
                                self._fileType,
                                self._fileDate,
                                counter
                                ])
        return rootName + '.' + self._fileExtension

    def getFileCounter(self, path, which = 0):
        """
        Examine the files in the directory defined by 'path' and determine
        the counter to apply to the next file to be created.

        'which' determines this method returns the counter for the oldest
        file in the path, the newest (or current), or the next (newest + 1).
        The default is to return the next file counter for new file creation.

        which = 0 : next
        which = 1 : newest
        which = 2 : oldest
        """

        # If there are no file in the path, start with file '0000'
        nextCounter = 0

        # '*' allows matching to filenames that have a compression extension
        # such as '.gz.'
        generalFileName = self.makeFileName('[0-9][0-9][0-9][0-9]') + "*"
        fileList = glob.glob(os.path.join(path, generalFileName))

        # If one or more valid counters are found, return the max + 1
        # as a zero padded 4 character string.
        # If no matches are found, we start with the first file '0000'.
        #
        myRegExp = r"(\d{4})\." + self._fileExtension
        counterList = [ int(re.search(myRegExp, x).group(1)) for x in fileList]
        if counterList:
            if 0 == which:
                nextCounter = max(counterList) + 1
            elif 1 == which:
                nextCounter = max(counterList)
            elif 2 == which:
                nextCounter = min(counterList)
            else:
                print("Error in FileManager::getFileCounter")
        return str(nextCounter).zfill(4)

    def getNewFileName(self):
        """
        Create a file name. Search the current target directory for name
        clashes.  Increment the file counter until there is no clash.
        """
        newFileName = ""
        newCounter = self.getFileCounter(self._currentDatePath)
        newFileName = self.makeFileName(newCounter)
        return newFileName

    def writeData(self,data):
        """
        Assume 'data' is a formatted string single line output.
        The format is set in <need class names here>.

        Return the number of characters written.
        Errors are not handled here since we may want to code to continue even if
        file writes fail.  This may happen when the disk is full.
        """
        rtn = 0
        try:
            self._fileHandle.write(data)
            rtn = len(data)
        except Exception as e:
            pass
        if rtn:
            self._wroteToFile = True
        return rtn

    # === Unit Test Code ===========================================================================
    #
    def setTestEnvironment(self):
        """
        Setup debug mode which includes setting a local path for file writes and
        a starting date.  The date is advanced manually in the test code.
        """
        self._debugMode = True
        self._fileDate = "20170201"
        self._rootPathName = "./"

    def runTest0(self, msg = "", numOfWrites = 86400, writeDelay = 1.0, incrementDateAfterNWrites = -1):
        """
        Create a date directory. Open a new file and write some data to it.

        msg: Text appended to each written line of data.

        numOfWrites: The number of times to write to the file.

        writeDelay: The time in seconds between each write.

        incrementDateAfternWrites: If 0 or greater, while the current file is open,
            increment the date variable so that upon the next file open is in a new
            directory.  Until the current is closed, all writes should be to that
            current file even if the date variable has advanced to a later date.

        """
        self.makeDirs()
        self.openNewFile()
        for x in xrange(0,numOfWrites):
            print("Writing to %s with 2 sec delay" % self._currentOpenFileName)
            self.writeData("%s\tTest Data from runTest0() %s\n" % (str(datetime.now()), msg))
            if incrementDateAfterNWrites == x:
                dateAsInt = int(self._fileDate) + 1
                self._fileDate = str(dateAsInt)
                self.writeData("Date just incremented to %s\n" % dateAsInt)
            time.sleep(writeDelay)
        self.closeFile()
        return

    def runTest1(self, msg = ""):
        """
        Repeat single file creation several times to verify that the counter
        is being incremented correctly.
        """
        for x in range(0,5):
            self.runTest0(msg = "Invoked by runTest1()")
        return

    def runTest2(self, msg = ""):
        """
        Delete the oldest file in the path.
        Create a new file and verify that the counter continues the series
        so that file order is maintained.
        """
        fn = self.makeFileName(self.getFileCounter(self._currentDatePath, 2))
        fileToDelete = os.path.join(self._currentDatePath, fn)

        # Try to remove any file that matches the fileToDelete with a
        # possible extension.  This will try to delete the gzip'd version
        # of the file if it exists.
        for fn in glob.glob(fileToDelete + "*"):
            try:
                os.remove(fn)
            except:
                pass
        self.runTest0(msg = "Invoked by runTest2()")
        return

    def runTest3(self, msg = ""):
        """
        Test date change while a file is open and creating new files in the new
        directory.
        """
        for x in range(0,10):
            if 5 == x:
                self.runTest0(msg = "Invoked by runTest3(), advancing date", incrementDateAfterNWrites = 2)
            else:
                self.runTest0(msg = "Invoked by runTest3()")
        return

    def runTest4(self, msg = ""):
        """
        Simulate a constant data stream with a timer creating and closing files every
        60 seconds.  Every 5 minutes increment the date to test directory creation
        and resetting the file counter.

        This will write 1499 lines of data which is 7 directories of files.
        """

        # Kick off with the initial file and start the clocks.
        self.makeDirs()
        self.openNewFile()
        self._stopWatch = IntervalTimer(60, "NewFileTimer", self.closeFileAndOpenANewOne)
        self._stopWatch.start()
        self._dateStopWatch = IntervalTimer(60*5, "DateIncTimer", self.testFuncIncrementDate)
        self._dateStopWatch.start()
        msg = ""
        for i in xrange(0,1500):
            if not self._stopWatch.is_alive():
                break
            self.writeData("%s->%s\tTest Data from runTest4() %s\n" % (str(i), str(datetime.now()), msg))
            time.sleep(1.0)
        self._stopWatch.stop()
        self._dateStopWatch.stop()
        return

    def testFuncIncrementDate(self):
        dateAsInt = int(self._fileDate) + 1
        self._fileDate = str(dateAsInt)

    def testFuncSigintHandler(self, signum, frame):
        """
        For ^C
        """
        self._stopWatch.stop()
        self._dateStopWatch.stop()

class IntervalTimer(threading.Thread):
    """
    IntervalTimer is a non-blocking timer that runs a callback function
    every n seconds.  If no callback function is defined the timer 'pings'
    for debugging purposes.
    """
    def __init__(self, n, timerName = "", callback = None):
        threading.Thread.__init__(self)
        self._n = n
        self._keepRunning = True
        self._callback = callback
        self._timerName = timerName

    def run(self):
        while self._keepRunning and self._n > 0:
            for _ in xrange(0,self._n):
                if self._keepRunning:
                    time.sleep(1.0)
            if self._keepRunning:
                if self._callback:
                    self._callback()
                else:
                    print("Ping from timer %s", self._timerName)
        return

    def stop(self):
        self._keepRunning = False


def UnitTest(ofObj = None, msg = ""):
    """
    Simulate a constant data stream with a timer creating and closing files every
    60 seconds.  Every 5 minutes increment the date to test directory creation
    and resetting the file counter.

    This will write 1000 lines of data which is 4 directories of files.
    """

    ofObj.start()
    dateIncrementer = IntervalTimer(60*5, "DateIncTimer", ofObj.testFuncIncrementDate)
    dateIncrementer.start()
    for i in xrange(0,1000):
        if not ofObj.isRunning():
            break
        ofObj.writeData("%s->%s\tTest Data from runTest4() %s\n" % (str(i), str(datetime.now()), msg))
        time.sleep(1.0)
    ofObj.stop()
    dateIncrementer.stop()
    return

def main():
    of = OutputFile(newFileInterval=60, analyzerType="AMADS", fileType="DAT")
    of.setTestEnvironment()
    of.getSettings()

    def sigStop(sigNum, frame):
        of.stop()

    signal.signal(signal.SIGINT, sigStop)

    # Create one file
    #of.runTest0()

    # Create three more in the same directory
    #of.runTest1()

    #of.runTest2()

    #of.runTest3()

    #of.runTest4()
    UnitTest(of)

    return

if __name__ == '__main__':
    main()

