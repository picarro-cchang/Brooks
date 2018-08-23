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
# 14-06-29 sze   Use 0MQ PUB-SUB protocol instead of TCP Sockets
import zmq
import time

class Broadcaster(object):
    def __init__(self, port, name='Broadcaster', logFunc=None, sendHwm=500):
        self.name = name
        self.port = port
        self.logFunc = logFunc
        self.zmqContext = zmq.Context()
        self.publisher = self.zmqContext.socket(zmq.PUB)
        # Prevent publisher overflow from slow subscribers
        self.publisher.setsockopt(zmq.SNDHWM, sendHwm)
        self.publisher.bind("tcp://*:%s" % port)

    def send(self,msg):
        self.publisher.send(msg)
        
    def stop(self):
        self.publisher.close()
        self.publisher = None
        self.zmqContext.term()
        self.zmqContext = None
                
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
    b = Broadcaster(8881,logFunc=myLog,sendHwm=10)
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
