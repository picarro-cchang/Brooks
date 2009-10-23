from ctypes import windll, c_int
import serial
import time

class TimeoutError(Exception):
    pass

class DriverError(Exception):
    pass

class IbaseDio(object):
    def __init__(self):
        DLL_Path = ["ib_wdt.dll"]
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

class Autosampler(object):
    def __init__(self):
        self.ser = serial.Serial(None,baudrate=9600,timeout=1,xonxoff=1)
        self.dio = IbaseDio()
    def open(self):
        self.ser.port = 0
        self.ser.open()
        self.dio.installDriver()
        if not self.dio.isDioAvailable(0):
            self.dio.removeDriver()
            raise DriverError("No DIO driver installed for SBC")            
        self.dio.setDioInputMask(0x0F)
        self.dio.setDioOutputMask(0xF0)
        self.dio.shadow = 0xF0
        self.dio.setDioOutput(self.dio.shadow)
    def setControl(self,line,value):
        "Sets the value of control line (1-4) to specified value (0 or 1)"
        mask = 1<<(3+line)
        self.dio.shadow &= ~mask
        if value: self.dio.shadow |= mask
        self.dio.setDioOutput(self.dio.shadow)
    def getControl(self,line):
        "Gets the value of control line (1-4)"
        mask = 1<<(3+line)
        return 0 != (self.dio.shadow & mask)
    def getStatus(self,line):
        "Gets the value of status line (1-4)"
        mask = 1<<(line-1)
        return 0 != (self.dio.getDioInput(0) & mask)
    def sendString(self,str):
        self.ser.write(str + "\r")
    def getLine(self):
        line = []
        while True:
            ch = self.ser.read()
            if not ch:
                raise TimeoutError
            if ch != '\r':
                line.append(ch)
            else:
                return "".join(line)
    def getLines(self):
        lines = []
        while True:
            try:
                lines.append(self.getLine())
            except TimeoutError:
                return "\n".join(lines)
    def flush(self):
        self.ser.flushInput()
    def close(self):
        # Deassert signals on close
        self.dio.shadow = 0xF0
        self.dio.setDioOutput(self.dio.shadow)
        self.ser.close()
        self.dio.removeDriver()
    def initialize(self):
        self.open()
    def assertStart(self):
        self.setControl(2,0)
    def deassertStart(self):
        self.setControl(2,1)
    def assertInject(self):
        self.setControl(1,0)
    def deassertInject(self):
        self.setControl(1,1)
    def getInjected(self):
        return not self.getStatus(1)
    def getLog(self):
        self.sendString("GET_LOG")
        return self.getLines()

