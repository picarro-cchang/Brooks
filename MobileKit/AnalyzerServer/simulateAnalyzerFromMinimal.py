from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import time
import datetime

# When started, this program creates a dummy live archive file with only the timestamp, latitude 
#  and longitude columns

#dataFile = 'data/BFADS03-20110609-1014-Data.dat'
dataFile = r'C:\Users\dsteele\Documents\Locator\Data\FDDS2018-20121001-211337Z-DataLog_User_Minimal.dat'
liveFile = time.strftime('c:/UserData/AnalyzerServer/ZZZ-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())
UNIXORIGIN = datetime.datetime(1969,12,31,16,0,0,0) # Pacific standard time

handle = CreateFile(liveFile,GENERIC_WRITE,
                             FILE_SHARE_READ,None,CREATE_ALWAYS,
                             FILE_ATTRIBUTE_NORMAL,0)
if handle == INVALID_HANDLE_VALUE:
    raise RuntimeError('Cannot open live archive file %s' % liveFile)
WriteFile(handle,"%-26s%-26s%-26s%-26s%-26s%-26s\r\n" % ("EPOCH_TIME","ALARM_STATUS","GPS_ABS_LONG","GPS_ABS_LAT","CH4","ValveMask"))

ip = open(dataFile,'r')
header = ip.readline().split()
idLong = header.index('GPS_ABS_LONG')
idLat = header.index('GPS_ABS_LAT')
idMethane = header.index('CH4')
idEpochTime = header.index('EPOCH_TIME')

for line in ip.readlines():
    line = line.split()
    epochTime = float(line[idEpochTime])
    data = "%-26.3f%-26d%-26.10e%-26.10e%-26.10e%-26.10e\r\n" % (epochTime, 0, float(line[idLong]), \
        float(line[idLat]), float(line[idMethane]), 0)
    while True:
        time.sleep(0.25)
        try:
            WriteFile(handle,data)
            break
        except:
            pass
    sys.stderr.write('.')
    sys.stderr.flush()
    
CloseHandle(handle)
ip.close()    
