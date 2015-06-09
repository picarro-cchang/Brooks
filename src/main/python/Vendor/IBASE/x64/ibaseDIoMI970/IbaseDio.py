from ctypes import windll, c_int

class IbaseDio(object):
    def __init__(self):
        DLL_Path = [r"C:\Picarro\G2000\Host\Utilities\ibaseDioMI970\ib_wdt.dll"]
        for p in DLL_Path:        
            try:
                self.dioDLL = windll.LoadLibrary(p)
                break
            except:
                continue
        else:
            raise ValueError("Cannot load iBASE DIO shared library")

        self.installDriver = self.dioDLL.InstallDriver
        self.installDriver.argtypes = []
        self.installDriver.restype  = c_int

        self.removeDriver = self.dioDLL.RemoveDriver
        self.removeDriver.argtypes = []
        self.removeDriver.restype  = c_int

        self.isDioAvailable = self.dioDLL.IsDioAvailable
        self.isDioAvailable.argtypes = [c_int]
        self.isDioAvailable.restype  = c_int

        self.setDioInputMask = self.dioDLL.SetDioInputMask
        self.setDioInputMask.argtypes = [c_int]
        self.setDioInputMask.restype  = c_int

        self.setDioOutputMask = self.dioDLL.SetDioOutputMask
        self.setDioOutputMask.argtypes = [c_int]
        self.setDioOutputMask.restype  = c_int

        self.getDioInput = self.dioDLL.GetDioInput
        self.getDioInput.argtypes = [c_int]
        self.getDioInput.restype  = c_int

        self.setDioOutput = self.dioDLL.SetDioOutput
        self.setDioOutput.argtypes = [c_int]
        self.setDioOutput.restype  = c_int

if __name__ == "__main__":
    dio = IbaseDio()
    try:
        dio.installDriver()
        print "DIO available: %d" % (dio.isDioAvailable(0),)
        dio.setDioInputMask(0x0F)
        dio.setDioOutputMask(0xF0)
        val = 0
        while True:
            dio.setDioOutput(val)
            print "DIO Output: 0x%x, Input: 0x%x" % (val,dio.getDioInput(0),)
            val = raw_input("Enter value to be output, or just press <Enter> to end: ")
            if len(val)==0: break
            val = eval(val)
    finally:
        dio.removeDriver()