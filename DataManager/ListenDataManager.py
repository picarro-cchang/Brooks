# Diagnostic to listen to data manager broadcasts

import sys
if "../Common" not in sys.path: sys.path.append("../Common")
import Listener
import Queue
import SharedTypes
import StringPickler
import time

fp = open(time.strftime("DataManagerListener_%Y%m%d_%H%M%S.txt", time.localtime()),"w")

def logFunc(msg):
    msg = "Listener %s: %s" % (time.ctime(time.time),msg)
    print msg
    print >> fp, msg
    
class DataManagerListener(object):
    def __init__(self):
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject, retry = True, logFunc = logFunc)

if __name__ == "__main__":
    dml = DataManagerListener()
    maxDelay = 0
    lastTime = time.time()
    interval = 5
    numPoints = 0
    try:
        while True:
            obj = dml.queue.get()
            # print "%s" % (obj,)
            now = time.time()
            delay = now-obj['time']
            if now > lastTime + interval:
                msg = "%s: %d %.2f" % (time.ctime(now),numPoints,maxDelay)
                print msg
                print >> fp, msg
                maxDelay = delay
                numPoints = 1
                lastTime += interval
            else:
                maxDelay = max(maxDelay,delay)
                numPoints += 1
    finally:
        fp.close()
        