# Utility to rebroadcast a data manager stream via a ZMQ socket to another
#  computer via TCP/IP

from Host.autogen import interface
from Host.Common import Listener, SharedTypes
import Queue
import zmq

BROADCAST_PORT_RDRESULTS_ZMQ = 45030

class RdResultsRebroadcaster(object):
    def __init__(self):
        self.context = zmq.Context()
        self.broadcastSock = self.context.socket(zmq.PUB)
        self.broadcastSock.bind("tcp://0.0.0.0:%d" % BROADCAST_PORT_RDRESULTS_ZMQ)
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_RDRESULTS,
                                          interface.RingdownEntryType, retry=True)

    def run(self):
        try:
            while True:
                obj = self.queue.get()
                self.broadcastSock.send(bytearray(obj))
        finally:  # Get here on keyboard interrupt or other termination
            self.broadcastSock.close()
            self.context.term()
            self.listener.stop()

if __name__ == "__main__":
    rdr = RdResultsRebroadcaster()
    rdr.run()