import serial
import time

MAX_RETRY_TIMES = 3

class TimeoutError(Exception):
    pass

class RotValveCtrl(object):
    def __init__(self, port):
        # port = 0 means port = "COM1"
        self.port = port
        self.ser = serial.Serial(port=port,baudrate=9600,timeout=1,xonxoff=1, writeTimeout=1.0)

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

    def getPosition(self):
        try:
            self.sendString("CP")
            cp = self.getLine()
            currPos = cp.split("= ")[-1]
        except:
            currPos = "-1"
        return currPos

    def reopen(self):
        self.ser.close()
        self.ser = serial.Serial(port=self.port,baudrate=9600,timeout=1,xonxoff=1, writeTimeout=1.0)
        self.ser.open()

    def setPosition(self, pos):
        retryTimes = 0
        while retryTimes < MAX_RETRY_TIMES:
            try:
                self.sendString("GO%s" % pos)
                return
            except:
                print "Rotary valve: Valve position command failed via serial port. Try again.\n"
                self.reopen()
                retryTimes += 1
                time.sleep(0.5)
        print "Rotary valve: Valve position command failed for %d times.\n" % MAX_RETRY_TIMES
        raise Exception("Rotary valve: Valve position command failed for %d times." % MAX_RETRY_TIMES)