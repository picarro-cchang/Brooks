from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import time
import datetime

# When started, this program creates a dummy live archive file with only the timestamp, latitude 
#  and longitude columns

#dataFile = 'data/BFADS03-20110609-1014-Data.dat'
dataFile = 'data/CFADS2030-20110919-202411Z-DataLog_User_Minimal.dat'
liveFile = time.strftime('static/datalog/BFADS03-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())
UNIXORIGIN = datetime.datetime(1969,12,31,16,0,0,0) # Pacific standard time

handle = CreateFile(liveFile,GENERIC_WRITE,
                             FILE_SHARE_READ,None,CREATE_ALWAYS,
                             FILE_ATTRIBUTE_NORMAL,0)
if handle == INVALID_HANDLE_VALUE:
    raise RuntimeError('Cannot open live archive file %s' % liveFile)
WriteFile(handle,"%-26s%-26s%-26s%-26s%-26s\r\n" % ("EPOCH_TIME","ALARM_STATUS","GPS_ABS_LONG","GPS_ABS_LAT","CH4"))

ip = open(dataFile,'r')
header = ip.readline().split()
idLong = header.index('LONGITUDE')
idLat = header.index('LATITUDE')
idMethane = header.index('CH4')
idDate = header.index('DATE')
idTime = header.index('TIME')

for line in ip.readlines():
    line = line.split()
    month, day, year = [int(x) for x in line[idDate].split('/')]
    hr, min, sec = [float(x) for x in line[idTime].split(':')]
    now = datetime.datetime.now()
    # Add century which minimizes interval to present
    year += 100*((now.year - year + 50)//100)
    d = datetime.datetime(year,month,day,int(hr),int(min),int(sec),int(1000000*(sec-int(sec))))
    dt = d - UNIXORIGIN
    epochTime = 86400.0*dt.days + dt.seconds + 1.e-6*dt.microseconds
    data = "%-26.3f%-26d%-26.10e%-26.10e%-26.10e\r\n" % (epochTime, 0, float(line[idLong]), \
        float(line[idLat]), float(line[idMethane]))
    WriteFile(handle,data)
    time.sleep(0.25)
    sys.stderr.write('.')
    sys.stderr.flush()
    
CloseHandle(handle)
ip.close()    
