#!/usr/bin/python
#
# File Name: Broadcaster.py
# Purpose: Broadcaster is a class which allows multiple clients to connect to a TCP socket and
#  receive data which is broadcasted to all of them. A client may disconnect at any time without
#  affecting the other clients. A buffer is established when each client connects, and contains
#  the data which the client has not yet received. If this buffer exceeds a certain length, the
#  connection to that client is automatically closed.
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
import select
import socket
import threading
import sets
import Queue
import array

class BroadcastException(Exception):
    "Exception for broadcaster clients"
    pass

class Client(object):
    "Class representing a client which subscribes to the broadcast service"
    def __init__(self,broadcaster,listener):
        """listener is the TCP socket which awaits connections to the broadcaster
        maxlen is the maximum number of characters in the client buffer before a forced disconnection
        """
        socket,address = listener.accept()
        self.socket = socket
        self.address = address
        self.broadcaster = broadcaster
        # On initialization, the client's "readPosition" is set to the place where the broadcaster
        #  is going to write new data.
        self.readPosition = self.broadcaster.writePosition
    def close(self):
        "Close the client socket"
        self.socket.close()
    def sendCurrent(self):
        "Send as much data as possible to the socket and update the buffer. Returns number of bytes sent"
        nSent = 0
        endPointer =  self.broadcaster.writePosition
        if self.readPosition == endPointer:
            return nSent # no data to send
        elif self.readPosition < endPointer: # Data are contiguous
            n = self.socket.send(self.broadcaster.circularBuffer[self.readPosition:endPointer].tostring())
            if n<=0:
                raise BroadcastException,"socket.send returns non-positive count"
            self.readPosition += n
            nSent += n
        else: # Data are in two pieces
            n = self.socket.send(self.broadcaster.circularBuffer[self.readPosition:self.broadcaster.circularBufferLength].tostring())
            if n<=0:
                raise BroadcastException,"socket.send returns non-positive count"
            self.readPosition += n
            nSent += n
            if self.readPosition == self.broadcaster.circularBufferLength:
                self.readPosition = 0
                if self.readPosition == endPointer:
                    return nSent # no more data to send
                n = self.socket.send(self.broadcaster.circularBuffer[:endPointer].tostring())
                if n<=0:
                    raise BroadcastException,"socket.send returns non-positive count"
                self.readPosition += n
                nSent += n
        return nSent

class Broadcaster(threading.Thread):
    """A thread which can broadcast the same information to a collection of clients which connect
    to the specified port.
    """
    def __init__(self,port,name='Broadcaster',logFunc=None):
        """port is the TCP port for clients to connect to the broadcaster
        name is used to name the thread
        logFunc is called to record logging data from the Broadcaster
        """
        self.name = name
        self.port = port
        self.clients = {}  # Dictionary of clients (indexed by socket) to which to send out information
        self.sockListen = None
        # Message queue stores strings to be sent before these are transferred to the circular buffer
        self.messageQueue = Queue.Queue(0)
        # Circular buffer is used by clients to get strings to send to the output socket
        self.circularBufferLength = 65536
        self.circularBuffer = array.array('c',self.circularBufferLength*'\0')
        self.writePosition = 0
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
    def killBadClients(self):
        # Kill bad clients
        for client in self.badClients:
            sock = client.socket
            self.safeLog("%s: Forced disconnection of client at %s" % (self.name,sock.getpeername(),))
            self.__killClient(sock)
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
    def handleInput(self,iw):
        """This handles sockets which have data available to read"""
        for sock in iw:
            # Generate a new client if we get a connection request
            if sock == self.sockListen:
                c = Client(self,sock)
                self.safeLog("%s: Connection from %s" % (self.name,c.address))
                self.clients[c.socket] = c
            else:
                # Ignore input from clients by continually reading and discarding their data
                try:
                    data = sock.recv(1024)
                    if len(data) <= 0:
                        raise Exception
                except:
                    self.safeLog("%s: Client at %s disconnected" % (self.name,sock.getpeername(),))
                    self.__killClient(sock)
    def handleOutput(self,ow):
        # Iterate through clients which are connected, sending as much as each will allow
        for sock in ow:
            try:
                self.clients[sock].sendCurrent()
            except Exception,e:
                self.safeLog("%s: Client at %s disconnected, exception %s" % (self.name,sock.getpeername(),e))
                self.__killClient(sock)
    def updateClientInfo(self):
        # Update circularBuffer using strings from queue and find bad clients. This function runs until the queue
        #  has been emptied out.
        # The data are placed in self.circularBuffer. self.writePosition is the tail of the buffer where new data
        #  are added.The circular buffer must be big enough to contain the data that have banked up in the queue
        #  since the last time this function was called. Otherwise, all clients need to be disconnected.
        #
        #  Each client has a readPosition pointer indicating what data have already been sent to that client.
        #  If during the process of putting data onto the circular buffer, the writePosition catches up with the
        #  readPosition pointer of a client, this means that the client has been overrun and must be disconnected.
        #
        startPosition = self.writePosition
        nBytes = 0
        while not self.messageQueue.empty():
            msg = self.messageQueue.get()
            nBytes += len(msg)
            if nBytes >= self.circularBufferLength:
                self.safeLog("Broadcast message overflows circular buffer. All clients disconnected.")
                break # Overflow error, all clients must be disconnected
            if self.writePosition+len(msg) >= self.circularBufferLength:
                nFirst = self.circularBufferLength-self.writePosition
                nSecond = len(msg) - nFirst
                self.circularBuffer[self.writePosition:] = array.array('c',msg[:nFirst])
                self.circularBuffer[:nSecond] = array.array('c',msg[nFirst:])
                self.writePosition = nSecond
            else:
                self.circularBuffer[self.writePosition:self.writePosition+len(msg)] = array.array('c',msg)
                self.writePosition = self.writePosition+len(msg)

        badClients = []
        if nBytes < self.circularBufferLength:
            # Work out if any clients have been overrun
            for client in self.clients.values():
                if self.writePosition > startPosition:
                    if self.writePosition >= client.readPosition > startPosition:
                        self.safeLog("Client [%s] buffer overrun." % (client.socket.getpeername(),))
                        badClients.append(client)
                elif self.writePosition < startPosition:
                    if client.readPosition > startPosition or client.readPosition <= self.writePosition:
                        self.safeLog("Client [%s] buffer overrun." % (client.socket.getpeername(),))
                        badClients.append(client)
        else:
            badClients = self.clients.values()
            self.writePosition = 0

        return badClients
    def restartAll(self):
        try:
            badClients = self.clients.values()
            self.killBadClients()
            self.writePosition = 0
            if self.sockListen != None:
                self.sockListen.close()
                self.sockListen = None
            self.setupSockListen()
        except Exception,e:
            self.safeLog("Exception %s during restartAll, ignoring" % (e,))
            pass
    def run(self):
        """ The thread execution function listens for new client connections and sends data to the registered client sockets """
        self.setupSockListen()
        try:
            self.badClients = []
            while not self._stopevent.isSet():
                try:
                    self.mainLoop()
                except Exception,e:
                    self.safeLog("Exception in broadcaster: %s" % (e,))
                    self.restartAll()
        finally:
            if self.sockListen != None:
                self.sockListen.close()
                self.sockListen = None

    def mainLoop(self):
        self.killBadClients()
        # Set up socket lists for select
        # sockListen is the socket for new client connections
        # self.clients.keys are the current clients who may be sending information (such info is ignored)
        iwtd = [self.sockListen] + self.clients.keys()
        # Only consider clients for whom we have data to write
        owtd = [csock for csock in self.clients.keys() if self.clients[csock].readPosition != self.writePosition]
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
        self.handleOutput(ow)
        # Empty out the input queue into the circular buffer and kick off those clients who have become overrun
        self.badClients = self.updateClientInfo()

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
    m = MyTime()
    while True:
        t = localtime()
        m.year = t.tm_year
        m.month = t.tm_mon
        m.day = t.tm_mday
        m.hour = t.tm_hour
        m.minute = t.tm_min
        m.second = t.tm_sec
        b.send(StringPickler.ObjAsString(m))
        sleep(1.0)
