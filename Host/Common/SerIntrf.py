from ctypes import windll, c_int
import serial
import time

class TimeoutError(Exception):
    pass

class SerIntrf(object):
    def __init__(self,port,baudrate=9600,timeout=1,xonxoff=1):
        # port = 0 means port = "COM1"
        self.ser = serial.Serial(port=port,baudrate=baudrate,timeout=timeout,xonxoff=xonxoff)

    def open(self):
        # Win7 throws an exception if try to open port that is already open
        # or close an already closed port, so must check the state first.
        # Same logic also works on WinXP.
        if not self.ser.isOpen():
            self.ser.open()

    def close(self):
        if self.ser.isOpen():
            self.ser.close()

    def flush(self):
        self.ser.flushInput()

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

