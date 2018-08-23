#!/usr/bin/python
#
# File Name: SafeFile.py
# Purpose:
#   This is a general utility module that provides the SafeFile class.
#
#   This class is to address the following problem: If the pc crashes (or
#   power goes out) in the middle of a write sequence of a file, the file
#   can be left in a half-finished and corrupted state.  For critical
#   configuration or calibration files, this can be a major problem.
#
# Notes:
#   The SafeFile class solves this problem by making sure that all incomplete
#   file saving operations are done in a seaprate temporary file.  Only when
#   the file is completed is the temporary file renamed to the "proper" file
#   name.
#
#   This action is transparent to the user and a SafeFile can be used in place
#   of a normal file object.
#
#   NOTE THAT *NO* FILE CHANGES WILL EVER BE AVAILABLE UNTIL YOU CLOSE THE FILE.
#
# File History:
# 06-04-26 russ  Created first release
# 06-07-21 russ  Added FileExists; Set for use with * imports
# 06-07-27 russ  Fix for strange/intermittent win32 file-locking; Fixes to temp-file handling

import os
import os.path
import shutil #for file copying
from sys import platform as sys_platform
if sys_platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp
from time import sleep

__all__ = ["SafeFile", "FileExists"]

_TEMP_PREFIX = "!Temp!"
_FIRST_TIME_PREFIX = '!FirstWrite!'
MAX_RETRY_DURATION_s = 0.5

class SafeFile(file):
    """A file object replacement that protects against mid-write crashes.

    Use this anywhere you would normally use a file object.

    eg: instead of using:
           fp = open(filename, mode)
        use
           fp = SafeFile(filename, mode)

    IMPORTANT NOTES!!!
      1. If writing/reading a file using SafeFile, you should ALWAYS write/read
         with SafeFile in order for it to work properly in all cases.
      2. If planning to check for the existence of a file that is being used
         with the SafeFile class, the FileExists function should be used instead
         of the typical os.path.exists call.

    """
    def __init__(self, filename, mode='r', bufsize=-1, *args, **kwargs):
        self._Prepare(filename, mode)
        file.__init__(self, self._UsedPath, mode, bufsize, *args, **kwargs)

    def LogFunc(self, ErrMsg, ErrData):
        """Log function called when special cases are encountered.  Should be overridden.
        """
        pass

    def _Prepare(self, filename, mode):
        self._RequestedPath = filename
        self._RequestedDir, self._RequestedFileName = os.path.split(self._RequestedPath)
        self._TempFileName = "%s%s" % (_TEMP_PREFIX, self._RequestedFileName)
        self._TempPath = os.path.join(self._RequestedDir, self._TempFileName)
        firstWritePath = os.path.join(self._RequestedDir, "%s%s" % (_FIRST_TIME_PREFIX, self._RequestedFileName))

        self._UsedPath = "" #tbd later.  This is what the root file object will get.

        #Quickly clean up any incompleted "first time" write...
        if os.path.exists(firstWritePath):
            os.remove(firstWritePath)
            self.LogFunc("Incomplete 'first write' SafeFile found and deleted.", "File = %s" % (firstWritePath,))

        tempExists = os.path.exists(self._TempPath)
        primaryExists = os.path.exists(self._RequestedPath)

        #The goal here is to end up with a _UsedPath that the base file object will work with.
        #When we're done with the object (file closed) we'll deal with the backup stuff.

        if not primaryExists:
            if not tempExists:
                #Neither exist!  This is a fresh start.
                if "r" in mode:
                    #r modes require the file to exist, and it doesn't! Just let the normal file object deal with it...
                    self._UsedPath = self._RequestedPath #This will end up with a standard exception
                    return
                else:
                    #we're doing a first time write or append - this gets a special name...
                    self._UsedPath = firstWritePath
                    return
            else: # No primary, but there is a non-first-write temporary.
                #This should be VERY rare.  This means that the software was stopped in the
                #brief period between temp file completion and renaming to the primary name.
                #(remember that any interrupted first-time writes are obliterated by now)
                #The temp file is the legit, completed, file, so we want to make it so...
                os.rename(self._TempPath, self._RequestedPath) #Turn the temp (a good one) into the primary
                primaryExists = True
                tempExists = False
                self.LogFunc("SafeFile temp file exists without primary - temp renamed as primary.","File = %s" % (self._TempPath,))

        if tempExists:
            os.remove(self._TempPath)

        if primaryExists:
            if ("+" in mode) or ("a" in mode):
                #Either wanting simultaneous read/write, or we are appending to the old one.
                #In either case, we don't want to mess up the main file while doing it,
                #so we need to make sure there is good copy available...
                shutil.copy(self._RequestedPath, self._TempPath)
                self._UsedPath = self._TempPath
            elif "r" in mode:
                #Must be a vanilla read (since we already accounted for the + mode)...
                self._UsedPath = self._RequestedPath
            elif "w" in mode:
                #We are writing a new version of the file from scratch... we want to
                #write to the temp location...
                self._UsedPath = self._TempPath
        # At this point we are nicely abstracted.  On return, the creator will have
        # a file object pointed where we want it pointed.  Until the file is closed,
        # all management is simply with the file object.

    def close(self):
        if self._UsedPath != self._RequestedPath:
            #We must be writing to the file.  We want to close it, then get it
            #transferred to the primary location.
            file.close(self) #the base class closure
            #clear a spot...
            if os.path.exists(self._RequestedPath): os.remove(self._RequestedPath)
            #Now we want to transform our "temporary" file into the primary...
            #Note - if the system crashes here (between remove and rename) the temp
            #file is legit.  The recovery logic for this is handled in self._Prepare.
            #Also - there is a very strange/intermittent os error where the rename
            #attempt fails due to "permission denied".  Seems to be a weird file
            #locking thing... maybe with virus scanning or google desktop?  The retry
            #loop gets around this.
            startTime = TimeStamp()
            while 1:
                try:
                    os.rename(self._UsedPath, self._RequestedPath)
                    break
                except OSError:
                    if (TimeStamp() - startTime) > MAX_RETRY_DURATION_s:
                        raise
                    else:
                        self.LogFunc("OSError trapped when trying to rename tempory file to primary.",
                                     dict(File = self._TempPath))
                        sleep(0)
                        pass

def FileExists(FilePath):
    """Checks if the indicated file (or its SafeFile temporary instance) exists.

    Returns true if the file exists, false if not.

    This should be used in place of os.path.exists when dealing with SafeFiles
    in order to properly detect the temporary instance of a file that can exist
    during a particularily unfortunately timed shutdown.

    """
    pathExists = os.path.exists(FilePath)
    if pathExists:
        return True
    else:
        fDir, fName = os.path.split(FilePath)
        if not fName:
            return False
        else:
            tempPath = os.path.join(fDir, "%s%s" % (_TEMP_PREFIX, fName))
            return os.path.exists(tempPath)

if __name__ == "__main__":
    testpath = r"c:\SafeFileTest.txt"
    if os.path.exists(testpath):
        os.remove(testpath)

    try:
        fp = SafeFile(testpath,"r")
    except Exception, E:
        print E

    fp = SafeFile(testpath, "w")
    fp.write("Line 1\n")
    fp.close()

    fp = SafeFile(testpath, "a")
    fp.write("Line 2\n")
    fp.flush()
    fp.close()

    fp = SafeFile(testpath, "r+")
    print fp.read()
    fp.close()
    del fp
    if os.path.exists(testpath):
        os.remove(testpath)