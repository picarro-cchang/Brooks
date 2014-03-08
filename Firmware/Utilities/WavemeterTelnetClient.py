import socket
import sys
import time

PORT = 23

class WavemeterTelnetClient(object):
    def __init__(self,server,timeout):
        self.server = server
        self.string = ""
        self.tlast = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server, PORT))
        self.sock.settimeout(timeout)
        data = ""
        while True:
            try:
                data += self.sock.recv(1024)
            except socket.timeout:
                break
                
    def Close(self):
        self.sock.close()
        
    def PutString(self,string):
        self.sock.sendall(string)
        
    def GetString(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not len(data): break
                self.string += data
                self.tlast = time.time()
                if "\n" in self.string:
                    result = self.string.replace("\r","")
                    self.string = ""
                    self.tlast = None
                    return result
            except socket.timeout:
                print "Socket timeout"
                result = self.string
                self.string = ""
                self.tlast = None
                return result
                
if __name__ == "__main__":
    # N.B. The leading \n sent to the Burleigh seems to clean out some buffer
    #  It is also useful to start Hyperterminal on the Burleigh wavemeters and
    #  to set this up with the correct COM settings in order to get it to talk
    ser = "10.100.2.98"
    reply = WavemeterTelnetClient(ser,1.0)
    reply.PutString("\n*IDN?\n")
    while True:
        s = reply.GetString()
        if s != "": break
    print "First string: %s" % s
    reply.PutString("\n:READ:FREQ?\n")
    while True:
        s = reply.GetString()
        if s != "": break
    print "First string: %s" % s
    reply.Close()
