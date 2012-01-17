# Update a file opened for shared read access and update it periodically

from win32file import CreateFile, WriteFile, CloseHandle, SetFilePointer, DeleteFile
from win32file import FILE_BEGIN, FILE_END, GENERIC_WRITE, FILE_SHARE_READ
from win32file import CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, INVALID_HANDLE_VALUE
import itertools
import time

pathName1 = 'sharedFile1.txt'
handle = CreateFile(pathName1,GENERIC_WRITE,
                     FILE_SHARE_READ,None,CREATE_ALWAYS,
                     FILE_ATTRIBUTE_NORMAL,0)
if handle == INVALID_HANDLE_VALUE:
    raise RuntimeError('Cannot open file %s' % pathName)

pathName2 = 'sharedFile2.txt'    
fp = open(pathName2,'wb+',0)

try:
    for i in itertools.count(1):
        msg = "This is line %d.\n" % (i,)
        WriteFile(handle,msg)
        fp.write(msg)
        time.sleep(1.0)
finally:
    CloseHandle(handle)
    fp.close()