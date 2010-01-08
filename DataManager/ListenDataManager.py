# Diagnostic to listen to data manager broadcasts

import sys
if "../Common" not in sys.path: sys.path.append("../Common")
import Listener
import Queue
import SharedTypes
import StringPickler
import time

class DataManagerListener(object):
    def __init__(self):
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject, retry = True)

if __name__ == "__main__":
    dml = DataManagerListener()
    while True:
        obj = dml.queue.get()
        # print "%s" % (obj,)
        print "Delay = %s" % (time.time()-obj['time'],)
