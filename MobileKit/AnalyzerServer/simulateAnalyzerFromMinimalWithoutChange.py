from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,INVALID_HANDLE_VALUE
import sys
import time
import datetime

# When started, this program creates a file with the same columns as the original, one line at a time

# dataFile = 'data/Demo_FCDS2003-20111206-032437Z-DataLog_User_Minimal.dat'
# dataFile = 'data/FCDS2003-20120202-231310Z-DataLog_User_Minimal.dat'
# dataFile = r'R:\crd_G2000\FCDS\1061-FCDS2003\Data_20120113\AnalyzerServer\FCDS2003-20120113-221530Z-DataLog_User_Minimal.dat'
# dataFile = r'C:\UserData\AnalyzerServer\FCDS2006-20120323-020431Z-DataLog_User_Minimal.dat'
# dataFile = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120215\DAT\FCDS2003-20120215-235259Z-DataLog_User_Minimal.dat'
# dataFile = r'C:\Picarro\Eclipse\Sending Files To P3\Example\TEST6543-20120720-204922Z-DataLog_User_Minimal.dat'

# dataFile = r'C:\UserData\AnalyzerServer\tests\FDDS2008-20120904-143417Z-DataLog_User_Minimal.dat'
dataFile = r'C:\Users\dsteele\Documents\Locator\Data\FDDS2018-20121001-211337Z-DataLog_User_Minimal.dat'
# liveFile = r'C:\UserData\AnalyzerServer\FDDS2018-20121001-210025Z-DataLog_Sensor_Minimal.dat'
liveFile = time.strftime('C:/UserData/AnalyzerServer/ZZZ-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())

handle = CreateFile(liveFile,GENERIC_WRITE,
                             FILE_SHARE_READ,None,CREATE_ALWAYS,
                             FILE_ATTRIBUTE_NORMAL,0)
if handle == INVALID_HANDLE_VALUE:
    raise RuntimeError('Cannot open live archive file %s' % liveFile)

ip = open(dataFile,'r')
nlines = 3
wait = .6
for i,line in enumerate(ip):
    WriteFile(handle,line.replace("\n","\r\n"))
    sys.stderr.write('.')
    sys.stderr.flush()
    if i%nlines == 0: time.sleep(wait)
    
CloseHandle(handle)
ip.close()    
