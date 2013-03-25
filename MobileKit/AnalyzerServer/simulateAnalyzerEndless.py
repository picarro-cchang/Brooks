from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import os
import time
import datetime

# When started, this program creates a file with the same columns as the original, one line at a time

UNIXORIGIN = datetime.datetime(1969,12,31,16,0,0,0) # Pacific standard time

def run(dataFile, speedFactor=1.0):
    while True:
        analyzerId = os.path.basename(dataFile).split("-")[0]
        liveFile = time.strftime('C:/UserData/AnalyzerServer/ZZZ-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())
        print "\nNew live flie: %s" % liveFile
        handle = CreateFile(liveFile,GENERIC_WRITE,
                                     FILE_SHARE_READ,None,CREATE_ALWAYS,
                                     FILE_ATTRIBUTE_NORMAL,0)
        if handle == INVALID_HANDLE_VALUE:
            raise RuntimeError('Cannot open live archive file %s' % liveFile)

        ip = open(dataFile,'r')
        headerline = ip.readline()
        WriteFile(handle,headerline.replace("\n","\r\n"))
        header = headerline.split()
        idEpochTime = header.index('EPOCH_TIME')
        lastEpochTime = None
        for line in ip.readlines():
            epochTime = float(line.split()[idEpochTime])
            if not lastEpochTime:    
                timeInterval = 0.25
            else:
                timeInterval = epochTime - lastEpochTime
            lastEpochTime = epochTime
            
            WriteFile(handle,line.replace("\n","\r\n"))
            sys.stderr.write('.')
            sys.stderr.flush()
            time.sleep(timeInterval/speedFactor)
            
        CloseHandle(handle)
        ip.close()    

HELP_STRING = \
""" Usage:

simulateAnalyzerEndless.py <FILENAME> [<SPEED FACTOR, default = 1.0>]
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print HELP_STRING
        sys.exit()
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    data_dir = os.path.join(AppDir,'static/datalog') # local Analyzer data location
    dataFile = sys.argv[1]
    if len(sys.argv) > 2:
        speedFactor = float(sys.argv[2])
    else:
        speedFactor = 1.0
    run(dataFile, speedFactor)