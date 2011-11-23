from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import time
import datetime

# When started, this program creates a file with the same columns as the original, one line at a time

dataFile = 'data/Modified FCDS2003-20111116-060310Z-DataLog_User_Minimal.dat';
liveFile = time.strftime('static/datalog/ZZZ-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())

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
    time.sleep(0.05)
    
CloseHandle(handle)
ip.close()    
