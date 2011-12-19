from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import time
import datetime

# When started, this program creates a file with the same columns as the original, one line at a time

dataFile = 'data/FCDS2003-20111210-015706Z-DataLog_User_Minimal.dat'
# dataFile = 'data/FCDS2003-20111213-234606Z-DataLog_User_Minimal.dat'
# dataFile = 'data/FCDS2003-20111215-013558Z-DataLog_User_Minimal.dat'
liveFile = time.strftime('C:/UserData/AnalyzerServer/ZZZ-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())

handle = CreateFile(liveFile,GENERIC_WRITE,
                             FILE_SHARE_READ,None,CREATE_ALWAYS,
                             FILE_ATTRIBUTE_NORMAL,0)
if handle == INVALID_HANDLE_VALUE:
    raise RuntimeError('Cannot open live archive file %s' % liveFile)

ip = open(dataFile,'r')
for line in ip:
    WriteFile(handle,line.replace("\n","\r\n"))
    sys.stderr.write('.')
    sys.stderr.flush()
    time.sleep(0.1)
    
CloseHandle(handle)
ip.close()    
