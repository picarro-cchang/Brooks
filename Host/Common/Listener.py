#!/usr/bin/python
#
# File Name: Listener.py
# Purpose: Listener is used to subscribe to a broadcast, optionally calling a "filter"
#  function on the data, and then optionally placing it in a queue. The objects sent by the
#  broadcast are assumed to be string pickled instances of some ctypes class.
#
# Notes: For text broadcasts, use TextListener.py
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-01-04 sze   Trap empty string from socket recv
# 06-10-30 russ  Arbitrary object serialization support
# 07-10-22 sze   Add a name and logFunc parameters to constructor so that we can log connections by name
# 07-11-24 sze   If an error occurs in the processing (filtering) of a packet, break the connection and retry
#                   (if this is requested)
import select
import socket
import Queue
import Host.Common.StringPickler as StringPickler
import ctypes
import threading
import time
import traceback

class Listener(threading.Thread):
    """ Listener object which allows access to broadcasts via INET sockets """
    def __init__(self, queue, port, elementType, streamFilter = None, notify = None, retry = False, name = "Listener", logFunc = None):
        """ Create a listener running in a new daemonic thread which subscribes to broadcasts at
        the specified "port". The broadcast consists of entries of type "elementType" (a subclass of
        ctypes.Structure)

        As elements arrive, they may be processed by the streamFilter function, and the results
        placed on a queue (an instance of Queue.Queue). Either of these parameters may be set to None.
        If the streamFilter is None, the entire entry is forwarded for queueing. If the queue is None,
        the data are discarded after calling streamFilter.

        The streamFilter function executes in the context of the Listener thread. It may be used to
        execute arbitrary code although it is primarily intended to be a filter which extracts the desired
        data from the elements and queues it for the main thread. By returning None nothing is queued, thus
        allowing data to be discarded.

        Information placed on the queue may be processed by a thread (usually the main thread) which gets
        from the queue. If all the processing can be done in the listener thread, the queue may be set to
        None.

        The parameters "notify" and "retry" control how errors which occur within the thread (including within
        the streamFilter) are handled. "notify" is a function or None, while "retry" is a boolean.

        notify is None,      retry == False: An exception kills the thread, and is raised
        notify is not None , retry == False: An exception invokes notify(exception_object) and kills the thread
        notify is None,      retry == True:  An exception is ignored, and processing continues
        notify is not None,  retry == True:  An exception invokes notify(exception_object) and processing continues

        A common exception occurs if the listener cannot contact the broadcaster. By setting retry=True, the
        listener will wait until the broadcaster restarts.

        The parameters "name" and "logFunc" are useful for debugging. Mesages from this module are sent by calling
        "logFunc", passing a string which includes "name". If "logFunc" is set to None, no logging takes place.
        """
        threading.Thread.__init__(self,name=name)
        self.sock = None
        self._stopevent = threading.Event()
        self.data = ""
        self.queue = queue
        self.port = port
        self.streamFilter = streamFilter
        self.elementType = elementType
        self.IsArbitraryObject = False
        self.name = name
        self.logFunc = logFunc
        self.notify = notify
        self.retry = retry

        try:
            if StringPickler.ArbitraryObject in self.elementType.__mro__:
                self.IsArbitraryObject = True
        except:
            pass
        if not self.IsArbitraryObject:
            self.recordLength = ctypes.sizeof(self.elementType)
        self.setDaemon(True)
        self.start()

    def safeLog(self,msg,*args,**kwargs):
        try:
            if self.logFunc != None: self.logFunc(msg,*args,**kwargs)
        except:
            pass

    def stop(self,timeout=None):
        """ Used to stop the main loop.
        This blocks until the thread completes execution of its .run() implementation.
        """
        self._stopevent.set()
        threading.Thread.join(self,timeout)

    def run(self):
        while not self._stopevent.isSet():
            try:
                if self.sock is None:
                    self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    try:
                        self.sock.connect(("localhost",self.port))
                        self.safeLog("Connection made by %s to port %d from %s." % (self.name,self.port,self.sock.getsockname()))
                    except Exception:
                        self.sock = None
                        if self.notify is not None:
                            msg = "Attempt to connect port %d by %s failed." % (self.port, self.name)
                            self.safeLog(msg,Level=2)
                            self.notify(msg)
                        time.sleep(1)
                        if self.retry: continue
                        else: return
                    self.data = ''
                try:
                    [iw,ow,ew] = select.select([self.sock],[],[],1.0)
                    if iw == []:
                        continue # Timeout => no (more) data available
                    r = self.sock.recv(1600)
                    if len(r) == 0: raise Exception, "Null data invalid"
                    self.data += r
                except Exception,e: # Error accessing or reading from socket
                    self.safeLog("Error accessing or reading from port %d by %s. Error: %s." % (self.port,self.name,e),Level=3)
                    if self.sock != None:
                        self.sock.close()
                        self.sock = None
                    continue
                #endtry
                # All received bytes are now appended to self.data
                if self.IsArbitraryObject:
                    self._ProcessArbitraryObjectStream()
                else:
                    self._ProcessCtypesStream()
            except Exception,e:
                self.safeLog("Communication from %s to port %d disconnected." % (self.name,self.port),Verbose=traceback.format_exc(),Level=2)
                if self.sock != None:
                    self.sock.close()
                    self.sock = None
                if self.retry:
                    if self.notify is not None: self.notify(e)
                    continue
                else:
                    if self.notify is not None:
                        self.notify(e)
                        return
                    else: raise
                #endif
            #endtry
        #endwhile

    def _ProcessArbitraryObjectStream(self):
        while 1:
            try:
                obj, residual = StringPickler.UnPackArbitraryObject(self.data)
                if self.streamFilter is not None:
                    obj = self.streamFilter(obj)
                if obj is not None and self.queue is not None:
                    self.queue.put(obj)
                self.data = residual
            except StringPickler.IncompletePacket:
                #All objects have been stripped out.  Get out of the loop to get more data...
                break
            except StringPickler.ChecksumErr:
                raise
            except StringPickler.BadDataBlock:
                raise
            except StringPickler.InvalidHeader:
                raise

    def _ProcessCtypesStream(self):
        while len(self.data) >= self.recordLength:
            result = StringPickler.StringAsObject(self.data[0:self.recordLength],self.elementType)
            if self.streamFilter is not None:
                e = self.streamFilter(result)
            else:
                e = result
            if e is not None and self.queue is not None:
                self.queue.put(e)
            self.data = self.data[self.recordLength:]
        #endwhile

if __name__ == "__main__":
    import ctypes
    import Host.Common.StringPickler as StringPickler

    class MyTime(ctypes.Structure):
        _fields_ = [
        ("year",ctypes.c_int),
        ("month",ctypes.c_int),
        ("day",ctypes.c_int),
        ("hour",ctypes.c_int),
        ("minute",ctypes.c_int),
        ("second",ctypes.c_int),
        ]

    def myNotify(e):
        print "Notification: %s" % (e,)

    def myLogger(s):
        print "Log: %s" % (s,)

    def myFilter(m):
        assert isinstance(m,MyTime*10000)
        return m

    queue = Queue.Queue(0)
    port = 8881
    listener = Listener(queue,port,MyTime*10000,myFilter,retry=True,notify=myNotify,name="Test Listener",logFunc=myLogger)

    while listener.isAlive():
        try:
            result = queue.get(timeout=0.5)
            h,m,s = result[0].hour,result[0].minute,result[0].second
            print "Time is %02d:%02d:%02d" % (h,m,s)
        except Queue.Empty:
            continue

    print "Listener terminated"