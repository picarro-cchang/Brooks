
import string

if __name__ == '__main__':
    from ctypes import *

    print 'ALS-G DLL Test Program'
    print '======================'

    phyDLL = windll.LoadLibrary('ALSG_API.dll')
    phyDLL.alsgGetError.restype = c_short

    bRet = phyDLL.alsgReadInit(c_char_p('parameter.td'))
    print 'alsgReadInit() returns: ', bRet
    if bRet == 0:
        nRet = phyDLL.alsgGetError()
        print 'alsgGetError() returns: ', nRet

    bRet = phyDLL.alsgReadInit(c_char_p('C:\parameter.td'))
    print 'alsgReadInit() returns: ', bRet
    if bRet == 0:
        nRet = phyDLL.alsgGetError()
        print 'alsgGetError() returns: ', nRet
