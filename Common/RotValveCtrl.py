import serial
import time

class TimeoutError(Exception):
    pass

class RotValveCtrl(object):
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

    def getPosition(self):
        try:
            self.sendString("CP")
            cp = self.getLine()
            currPos = cp.split("= ")[-1]
        except:
            currPos = "-1"
        return currPos
        
    def setPosition(self, pos):
        try:
            self.sendString("GO%s" % pos)
        except:
            print "Rotary valve: Failed to send valve position command via serial port\n"

