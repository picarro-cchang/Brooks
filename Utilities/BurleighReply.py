import serial
import time

class BurleighReply(object):
    def __init__(self,ser,interchar_timeout):
        self.ser = ser
        self.interchar_timeout = interchar_timeout
        self.string = ""
        self.tlast = None

    def GetString(self):
        while True:
            ch = self.ser.read()
#      print "ch: >%s<" % ch
            if ch == "": break
            if ch == "\r": continue
            self.string = self.string + ch
            self.tlast = time.clock()
            if ch == "\n":
                result = self.string
                self.string = ""
                self.tlast = None
                return result
        if self.tlast!=None and time.clock()-self.tlast > self.interchar_timeout:
            result = self.string
            self.string = ""
            self.tlast = None
            return result
        return ""

if __name__ == "__main__":
    # N.B. The leading \n sent to the Burleigh seems to clean out some buffer
    #  It is also useful to start Hyperterminal on the Burleigh wavemeters and
    #  to set this up with the correct COM settings in order to get it to talk
    ser = serial.Serial(0,19200,timeout=0)
    reply = BurleighReply(ser,0.5)
    ser.write("\n*IDN?\n")
    while True:
        s = reply.GetString()
        if s != "": break
    print "First string: %s" % (list(s),)
    while True:
        s = reply.GetString()
        if s != "": break
    print "Second string: %s" % (list(s),)
    ser.write("\n:READ:SCAL:WAV?\n")
    while True:
        s = reply.GetString()
        if s != "": break
    print "First string: %s" % (list(s),)
    ser.write("\n:READ:SCAL:FREQ?\n")
    while True:
        s = reply.GetString()
        if s != "": break
    print "First string: %s" % (list(s),)
#    ser.write("\n:READ:FREQ?\n")
#    while True:
#        s = reply.GetString()
#        if s != "": break
#    print "Second string: %s" % (list(s),)

#  ser.close()
