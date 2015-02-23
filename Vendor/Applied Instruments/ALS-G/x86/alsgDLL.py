
import string

if __name__ == '__main__':
    from ctypes import *

    print 'ALS-G DLL Test Program'
    print '======================'

    phyDLL = windll.LoadLibrary('ALSG_API.dll')
    
    phyDLL.alsgReadInit.restype = c_bool
    phyDLL.alsgSaveParameterFile.restype = c_bool
    phyDLL.alsgGetError.restype = c_short
    phyDLL.alsgGetDllVersion.restype = c_double

    print 'alsgGetDllVersion() returns: ', phyDLL.alsgGetDllVersion()
    
    status = phyDLL.alsgReadInit(c_char_p(r'c:\ProgramData\Picarro_Training\Parameter.td'))
    print 'alsgReadInit() returns: ', status
    if status == 0:
        err_code = phyDLL.alsgGetError()
        print 'alsgGetError() returns: ', err_code
        if err_code == 4:
            status = phyDLL.alsgSaveParameterFile(c_char_p(r'c:\ProgramData\Picarro_Training\Parameter.td'))
            print 'alsgSaveParameterFile() returns: ', status
            if status == 0:
                err_code = phyDLL.alsgGetError()
                print 'alsgGetError() returns: ', err_code

    raw_input('Press <Enter> to finish')