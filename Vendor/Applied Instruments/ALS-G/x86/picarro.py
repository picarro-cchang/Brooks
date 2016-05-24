
import string

if __name__ == '__main__':
    from ctypes import *

    print 'ALS-G DLL Test Program'
    print '======================'

    phyDLL = windll.LoadLibrary('ALSG_API.dll')
    phyDLL.alsgGetError.restype = c_short
 
    phyDLL.alsgGetDllVersion.restype = c_double
    lVersion = c_double(0)
    lVersion = phyDLL.alsgGetDllVersion()
    print "ALSG_API.dll Version: ", lVersion

    lReadInit = c_long(0)
    phyDLL.alsgReadInit.restype = c_long
    lReadInit = phyDLL.alsgReadInit(c_char_p(r"Parameter.td"))
    print "ReadInit() returns: ", lReadInit
    if lReadInit==0:
       phyDLL.alsgGetError.restype = c_short
       lError = c_short(0)
       lError = phyDLL.alsgGetError()
       print "alsgGetError() returns: ", lError
       if lError==4:
           nWrite=c_long(0);
           phyDLL.alsgSaveParameterFile.restype = c_long
           nWrite = phyDLL.alsgSaveParameterFile(c_char_p(r"Parameter.td"))
           print 'Older version, update with alsgSaveParameterFile(), returns: ', nWrite
           lReadInit = phyDLL.alsgReadInit(c_char_p(r"Parameter.td"))
           print "Again... ReadInit() returns: ", lReadInit
           

    lConnect = c_short(0)
    lcomport = c_short(3)
    phyDLL.alsgReadInit.restype = c_short
    lConnect = phyDLL.alsgConnect(lcomport)
    print 'alsgConnect() returns: ', lConnect

    lBeep = c_long(0);
    lNoOfBeeps = c_short(1)
    phyDLL.alsgBeep.restype = c_long
    lBeep = phyDLL.alsgBeep(lNoOfBeeps)
    print 'alsgBeep() returns: ', lBeep
	
    lRunInit = c_long(0);
    lDefWashStation = c_short(0)
    phyDLL.alsgRunInit.restype = c_long
    lRunInit = phyDLL.alsgRunInit(lDefWashStation)
    print 'alsgRunInit() returns: ', lRunInit

        
