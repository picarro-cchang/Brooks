#!/usr/bin/python
#
# File Name: TextListener.py
# Purpose: TextListener is used to subscribe to line oriented broadcasts (i.e. separated by \n),
#  optionally calling a "filter" function on the data, and then optionally placing it in a queue.
#
# Notes: For ctypes object broadcasts, use Listener.py
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-01-04 sze   Trap empty string from socket recv
# 07-10-22 sze   Add a name and logFunc parameters to constructor so that we can log connections by name

import select
import socket
import time
from Queue import Queue
import threading

class TextListener(threading.Thread):
    """ Listener object which allows access to line-oriented text broadcasts via INET sockets """
    def __init__(self,queue,port,streamFilter=None,notify=None,retry=False, name = "Listener", logFunc = None):
        """ Create a listener running in a new daemonic thread which subscribes to broadcasts at
    the specified "port".  The broadcast consists of lines ending with "\n".

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
     """
        self.sock = None
        self._stopevent = threading.Event()
        self.queue = queue
        self.port = port
        self.streamFilter = streamFilter
        self.name = name
        self.logFunc = logFunc
        self.notify = notify
        self.retry = retry
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start()

    def safeLog(self,msg):
        try:
            if self.logFunc != None: self.logFunc(msg)
        except:
            pass

    def stop(self,timeout=None):
        """ Used to stop the main loop """
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
                        time.sleep(1)
                        self.sock = None
                        self.safeLog("Connection by %s to port %d failed." % (self.name,self.port),Level=2)
                        raise Exception("Cannot subscribe to broadcast stream")
                    self.data = ''
                try:
                    [iw,ow,ew] = select.select([self.sock],[],[],1.0)
                    if iw == []:
                        continue # Timeout => no (more) data available
                    r = self.sock.recv(1600)
                    if len(r) == 0: raise Exception, "Null data invalid"
                    self.data += r
                except: # Error accessing or reading from socket
                    self.safeLog("Connection by %s to port %d throws error %s." % (self.name,self.port,e),Level=3)
                    if self.sock != None:
                        self.sock.close()
                        self.sock = None
                    continue
                nlPos = self.data.find("\n")
                while nlPos > 0:
                    result = self.data[:nlPos]
                    if self.streamFilter is not None:
                        e = self.streamFilter(result)
                    else:
                        e = result
                    if e is not None and self.queue is not None:
                        self.queue.put(e)
                    self.data = self.data[nlPos+1:]
                    nlPos = self.data.find("\n")
            except Exception,e:
                self.safeLog("Connection by %s to port %d broken." % (self.name,self.port),Level=2)
                if self.retry:
                    if self.notify is not None: self.notify(e)
                    continue
                else:
                    if self.notify is not None:
                        self.notify(e)
                        return
                    else: raise
