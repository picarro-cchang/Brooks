# Remote listener for ringdown results via ZMQ

from Host.autogen import interface
from Host.Common import SharedTypes
from optparse import OptionParser
import zmq

BROADCAST_PORT_RDRESULTS_ZMQ = 45030

class RdResultsListener(object):
    def __init__(self, ipAddr, port):
        self.context = zmq.Context()
        self.listenSock = self.context.socket(zmq.SUB)
        self.listenSock.connect("tcp://%s:%d" % (ipAddr, port))
        self.listenSock.setsockopt(zmq.SUBSCRIBE, "")

    def run(self):
        poller = zmq.Poller()
        poller.register(self.listenSock, zmq.POLLIN)
        try:
            while True:
                socks = dict(poller.poll())
                if socks.get(self.listenSock) == zmq.POLLIN:
                    obj = interface.RingdownEntryType.from_buffer_copy(self.listenSock.recv())
                    so = "%s" % SharedTypes.ctypesToDict(obj)
                    if len(so) > 75:
                        so = so[:75] + "..."
                    print so
        finally:  # Get here on keyboard interrupt or other termination
            self.listenSock.close()
            self.context.term()


def main():
    parser = OptionParser()
    parser.add_option("-a", dest="ipAddr", default="127.0.0.1",
        help="IP address of analyzer (def: 127.0.0.1)")
    parser.add_option("-p", dest="port", default=BROADCAST_PORT_RDRESULTS_ZMQ,
        help="Ringdown results rebroadcaster port (def: %d)" % BROADCAST_PORT_RDRESULTS_ZMQ)
    (options, args) = parser.parse_args()
    dml = RdResultsListener(options.ipAddr, options.port)
    dml.run()

if __name__ == "__main__":
    main()