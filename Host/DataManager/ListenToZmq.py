# Remote listener for data manager via ZMQ
import cPickle
from optparse import OptionParser
import zmq

BROADCAST_PORT_DATA_MANAGER_ZMQ = 45060


class DataManagerListener(object):
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
                    obj = cPickle.loads(self.listenSock.recv())
                    so = str(obj)
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
    parser.add_option("-p", dest="port", default=BROADCAST_PORT_DATA_MANAGER_ZMQ,
        help="Data manager rebroadcaster port (def: %d)" % BROADCAST_PORT_DATA_MANAGER_ZMQ)
    (options, args) = parser.parse_args()
    dml = DataManagerListener(options.ipAddr, options.port)
    dml.run()

if __name__ == "__main__":
    main()