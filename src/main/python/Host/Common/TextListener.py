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
# 14-06-29 sze   Use 0MQ PUB-SUB protocol instead of TCP Sockets

import zmq
import Queue
import threading
import time
import traceback

class TextListener(threading.Thread):
    """ Listener object which allows access to line-oriented text broadcasts via INET sockets """
    def __init__(self, queue, port, streamFilter=None, notify=None, retry=False, name = "Listener", logFunc = None):
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

        threading.Thread.__init__(self,name=name)
        self._stopevent = threading.Event()
        self.data = ""
        self.queue = queue
        self.port = port
        self.streamFilter = streamFilter
        self.name = name
        self.logFunc = logFunc
        self.notify = notify
        self.retry = retry

        self.zmqContext = zmq.Context()
        self.socket = None    
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
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        self.zmqContext.term()
        self.zmqContext = None
        threading.Thread.join(self,timeout)
        
    def run(self):
        poller = None
        while not self._stopevent.isSet():
            try:
                if self.socket is None:
                    try:
                        poller = zmq.Poller()
                        self.socket = self.zmqContext.socket(zmq.SUB)
                        self.socket.connect ("tcp://localhost:%s" % self.port)
                        self.socket.setsockopt(zmq.SUBSCRIBE, "")
                        poller.register(self.socket, zmq.POLLIN)
                        self.safeLog("Connection made by %s to port %d." % (self.name,self.port))
                    except Exception:
                        self.socket = None
                        if self.notify is not None:
                            msg = "Attempt to connect port %d by %s failed." % (self.port, self.name)
                            self.safeLog(msg,Level=2)
                            self.notify(msg)
                        time.sleep(1.0)
                        if self.retry: continue
                        else: return
                    self.data = ""
                try:
                    socks = dict(poller.poll(timeout=1000))
                    if socks.get(self.socket) == zmq.POLLIN:
                        self.data += self.socket.recv()
                except Exception,e: # Error accessing or reading from socket
                    self.safeLog("Error accessing or reading from port %d by %s. Error: %s." % (self.port,self.name,e),Level=3)
                    if self.socket != None:
                        self.socket.close()
                        self.socket = None
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
                self.safeLog("Communication from %s to port %d disconnected." % (self.name,self.port),Verbose=traceback.format_exc(),Level=2)
                if self.socket != None:
                    self.socket.close()
                    self.socket = None
                if self.retry:
                    if self.notify is not None: self.notify(e)
                    continue
                else:
                    if self.notify is not None:
                        self.notify(e)
                        return
                    else: raise

if __name__ == "__main__":
    def myNotify(e):
        print "Notification: %s" % (e,)

    def myLogger(s):
        print "Log: %s" % (s,)

    queue = Queue.Queue(0)
    port = 8881
    listener = TextListener(queue,port,retry=True,notify=myNotify,name="Test Listener",logFunc=myLogger)

    while listener.isAlive():
        try:
            result = queue.get(timeout=0.5)
            print result
        except Queue.Empty:
            continue

    print "Listener terminated"
                    