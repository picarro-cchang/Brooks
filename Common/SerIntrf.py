from ctypes import windll, c_int
import serial
import time

class TimeoutError(Exception):
    pass

class SerIntrf(object):
    def __init__(self, port):
        # port = 0 means port = "COM1"
        self.ser = serial.Serial(port=port,baudrate=9600,timeout=1,xonxoff=1)

    def open(self):
        self.ser.open()

    def close(self):
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



