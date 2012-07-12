from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import os
import time
import datetime

# When started, this program creates a dummy live archive file with only the timestamp, latitude 
#  and longitude columns

UNIXORIGIN = datetime.datetime(1969,12,31,16,0,0,0) # Pacific standard time

def run(dataFile, speedFactor=1.0):
    while True:
        analyzerId = os.path.basename(dataFile).split("-")[0]
        liveFile = ('static/datalog/Z_%s' % analyzerId) + time.strftime('-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())
        print "\nNew live flie: %s" % liveFile
        handle = CreateFile(liveFile,GENERIC_WRITE,
                                     FILE_SHARE_READ,None,CREATE_ALWAYS,
                                     FILE_ATTRIBUTE_NORMAL,0)
        if handle == INVALID_HANDLE_VALUE:
            raise RuntimeError('Cannot open live archive file %s' % liveFile)
        WriteFile(handle,"%-26s%-26s%-26s%-26s%-26s%-26s%-26s%-26s\r\n" % ("EPOCH_TIME","ALARM_STATUS","GPS_ABS_LONG","GPS_ABS_LAT","CH4","ValveMask","INST_STATUS","GPS_FIT"))

        ip = open(dataFile,'r')
        header = ip.readline().split()
        idLong = header.index('GPS_ABS_LONG')
        idLat = header.index('GPS_ABS_LAT')
        idMethane = header.index('CH4')
        idEpochTime = header.index('EPOCH_TIME')
        idInstStatus = header.index('INST_STATUS')
        idGPSFit = header.index('GPS_FIT')
        lastEpochTime = None
        for line in ip.readlines():
            line = line.split()
            epochTime = float(line[idEpochTime])
            data = "%-26.3f%-26d%-26.10e%-26.10e%-26.10e%-26.10e%-26d%-26d\r\n" % (epochTime, 0, float(line[idLong]), \
                float(line[idLat]), float(line[idMethane]), 0, int(line[idInstStatus]), int(float(line[idGPSFit])))
            
            if not lastEpochTime:    
                timeInterval = 0.25
            else:
                timeInterval = epochTime - lastEpochTime
            lastEpochTime = epochTime
            
            while True:
                time.sleep(timeInterval/speedFactor)
                try:
                    WriteFile(handle,data)
                    break
                except:
                    pass
            sys.stderr.write('.')
            sys.stderr.flush()
            
        CloseHandle(handle)
        ip.close()    

HELP_STRING = \
""" Usage:

simulateAnalyzerFromMinimalEndless.py <FILENAME> [<SPEED FACTOR, default = 1.0>]
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