import serial
import time

class KeithleyReply(object):
    def __init__(self,ser,interchar_timeout):
        self.ser = ser
        self.interchar_timeout = interchar_timeout
        self.string = ""
        self.tlast = None

    def fetch(self):
        while True:
            ch = self.ser.read()
            if ch == "": break
            if ch == "\r": continue
            self.string = self.string + ch
            self.tlast = time.time()
            if ch == "\n":
                result = self.string
                self.string = ""
                self.tlast = None
                return result
        if self.tlast!=None and time.time()-self.tlast > self.interchar_timeout:
            result = self.string
            self.string = ""
            self.tlast = None
            return result
        return ""

    def getString(self):
        while True:
            s = self.fetch()
            if s != "": return s

    def sendString(self,string):
        self.ser.write(string + "\r")

    def ask(self,string):
        self.sendString(string)
        return self.getString()

if __name__ == "__main__":
    ser = serial.Serial(0,9600,timeout=0)
    keithley = KeithleyReply(ser,0.5)
    print keithley.ask("*IDN?")
    print keithley.ask(":SOURCE:CURRENT:MODE?")
    keithley.sendString(":SOURCE:CURRENT 0.000001")
    print keithley.ask(":MEAS:VOLT:DC?")
    for i in range(10):
        print keithley.ask(":READ?")
        time.sleep(0.5)
    keithley.sendString(":OUTPUT:STATE OFF")
    ser.close()