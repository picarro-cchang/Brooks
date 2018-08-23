# Utility to rebroadcast a data manager stream via a ZMQ socket to another
#  computer via TCP/IP

import cPickle
from Host.Common import Listener, SharedTypes, StringPickler
import Queue
import zmq

BROADCAST_PORT_DATA_MANAGER_ZMQ = 45060


class DataManagerRebroadcaster(object):
    def __init__(self):
        self.context = zmq.Context()
        self.broadcastSock = self.context.socket(zmq.PUB)
        self.broadcastSock.bind("tcp://0.0.0.0:%d" % BROADCAST_PORT_DATA_MANAGER_ZMQ)
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject, retry=True)

    def run(self):
        try:
            while True:
                obj = self.queue.get()
                so = str(obj)
                if len(so) > 75:
                    so = so[:75] + "..."
                print so
                self.broadcastSock.send(cPickle.dumps(obj))
        finally:  # Get here on keyboard interrupt or other termination
            self.broadcastSock.close()
            self.context.term()
            self.listener.stop()

if __name__ == "__main__":
    dmr = DataManagerRebroadcaster()
    dmr.run()