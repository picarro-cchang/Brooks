#!/usr/bin/python
#
# File Name: Broadcaster.py
# Purpose: Broadcaster is a class which allows multiple clients to connect to a TCP socket and
#  receive data which is broadcasted to all of them. A client may disconnect at any time without
#  affecting the other clients.
#
# Notes:
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-03-10 sze   Removed assert statements
# 07-09-06 sze   Introduced safeLog function
# 08-03-05 sze   Return queue length during put to message Queue
# 08-04-23 sze   Ensure that listen socket is closed when broadcaster thread stops
# 09-10-23 sze   Simplified to do queuing in kernel
import select
import socket
import threading
import sets
import Queue
import array

SOCKET_TIMEOUT = 0.1
MAX_TIMEOUTS = 20

class BroadcastException(Exception):
    "Exception for broadcaster clients"
    pass

class Client(object):
    "Class representing a client which subscribes to the broadcast service"
    def __init__(self,broadcaster,listener):
        """listener is the TCP socket which awaits connections to the broadcaster
        maxlen is the maximum number of characters in the client buffer before a forced disconnection
        """
        sock,address = listener.accept()
        self.socket = sock
        sock.settimeout(SOCKET_TIMEOUT)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,1<<22)
        self.address = address
        self.broadcaster = broadcaster
        self.posInString = 0

    def close(self):
        "Close the client socket"
        self.socket.close()

    def sendString(self,string,fromStart=True):
        """Sends the string, returning True iff all characters were sent"""
        try:
            if fromStart:
                self.done = False
                self.posInString = 0
                self.timeoutCount = 0
            if self.done:
                return True
            numSent = self.socket.send(string[self.posInString:])
            self.posInString += numSent
            self.timeoutCount = 0
            self.done = self.posInString >= len(string)
            return self.done
        except socket.error:
            self.timeoutCount += 1
            if self.timeoutCount > MAX_TIMEOUTS:
                self.broadcaster.addBadClient(self)
                raise BroadcastException("Timeout sending to address %s" % (self.address,))
        except:
            self.broadcaster.addBadClient(self)
            raise BroadcastException("Send error to address %s" % (self.address,))

class Broadcaster(threading.Thread):
    """A thread which can broadcast the same information to a collection of clients which connect
    to the specified port.
    """
    def __init__(self,port,name='Broadcaster',logFunc=None):
        """port is the TCP port for clients to connect to the broadcaster
        name is used to name the thread
        logFunc is called to record logging data from the Broadcaster
        """
        #self.name = name
        self.port = port
        self.clients = {}  # Dictionary of clients (indexed by socket) to which to send out information
        self.sockListen = None
        # Message queue stores strings to be sent before these are transferred to the circular buffer
        self.messageQueue = Queue.Queue(0)

        self._stopevent = threading.Event()
        threading.Thread.__init__(self,name=name)
        self.logFunc = logFunc
        self.setDaemon(True)
        self.start()
        
    def setupSockListen(self):
        self.sockListen = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # self.sockListen.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sockListen.bind(('',self.port))
        self.sockListen.listen(5)
        
    def safeLog(self,msg,*args,**kwargs):
        try:
            if self.logFunc != None: self.logFunc(msg,*args,**kwargs)
        except:
            pass
        
    def send(self,msg):
        """ Send the message to all registered clients. This does not wait for socket transfers
        to complete
        """
        self.messageQueue.put(msg)
        return self.queueSize()
    
    def queueSize(self):
        return self.messageQueue.qsize()
    
    def stop(self,timeout=None):
        """ Used to stop the main loop """
        self._stopevent.set()
        threading.Thread.join(self,timeout)

    def addBadClient(self,client):
        if client not in self.badClients:
            self.badClients.append(client)
        
    def killBadClients(self):
        # Kill bad clients
        for client in self.badClients:
            sock = client.socket
            self.safeLog("%s: Forced disconnection of client at %s" % (self.name,sock.getpeername(),))
            self.__killClient(sock)
        self.badClients = []
        
    def __killClient(self,sock):
        """ Close client socket and remove it from dictionary of clients """
        if sock in self.clients:
            try:
                self.clients[sock].close()
            except:
                pass
            del self.clients[sock]
        else:
            sock.close()
            
    def run(self):
        """ The thread execution function listens for new client connections and sends data to the registered client sockets """
        self.setupSockListen()
        self.errCount = 0 
        self.badClients = []
        try:
            while not self._stopevent.isSet():
                try:
                    self.mainLoop()
                except Exception,e:
                    self.safeLog("Exception in broadcaster: %s" % (e,))
        finally:
            if self.sockListen != None:
                self.sockListen.close()
                self.sockListen = None
                
    def handleInput(self,iw):
        """This handles sockets which have data available to read"""
        for sock in iw:
            # Generate a new client if we get a connection request
            if sock == self.sockListen:
                c = Client(self,sock)
                self.safeLog("%s: Connection from %s" % (self.name,c.address))
                self.clients[c.socket] = c

    def mainLoop(self):
        self.killBadClients()
        # Set up socket lists for select
        # sockListen is the socket for new client connections
        iwtd = [self.sockListen]
        owtd = []
        ewtd = []
        try:
            iw,ow,ew = select.select(iwtd,owtd,ewtd,0.25)
        except:
            # Error from select, deal with dead socket(s)
            for s in sets.Set(iwtd + owtd + ewtd):
                try:
                    select.select([s],[],[],0)
                except:
                    if s == self.sockListen:
                        if self.sockListen != None:
                            self.sockListen.close()
                            self.sockListen = None
                            self.setupSockListen()
                    else:
                        self.__killClient(s)
                        
        self.handleInput(iw)
        while not self.messageQueue.empty():
            s = self.messageQueue.get()
            fromStart = True
            allSent = False
            nLoops = 0
            while not allSent:
                allSent = True
                try:
                    for c in self.clients.values():
                        allSent = allSent and c.sendString(s,fromStart)
                except Exception,e:
                    self.safeLog("%s" % (e,))
                    self.killBadClients()
                fromStart = False
                
if __name__ == "__main__":
    from time import strftime,localtime,sleep
    import ctypes
    import StringPickler
    class MyTime(ctypes.Structure):
        _fields_ = [
        ("year",ctypes.c_int),
        ("month",ctypes.c_int),
        ("day",ctypes.c_int),
        ("hour",ctypes.c_int),
        ("minute",ctypes.c_int),
        ("second",ctypes.c_int),
        ]    
        
    def myLog(msg):
        print msg
    b = Broadcaster(8881,logFunc=myLog)
    m = (MyTime*10000)()
    while True:
        t = localtime()
        for i in range(10000):
            m[i].year = t.tm_year
            m[i].month = t.tm_mon
            m[i].day = t.tm_mday
            m[i].hour = t.tm_hour
            m[i].minute = t.tm_min
            m[i].second = t.tm_sec
        b.send(StringPickler.ObjAsString(m))
        sleep(1.0)
