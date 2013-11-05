#!/usr/bin/python
#
"""
File Name: ListenToPeriphZmq.py
Purpose: Remote listener for peripheral data via ZMQ

File History:
    2013-09-05 sze  Initial version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""

from Host.autogen import interface
from Host.Common import SharedTypes, StringPickler
from optparse import OptionParser
import zmq

BROADCAST_PORT_PERIPH_ZMQ = 45065


class PeriphZmqListener(object):

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
                    data = self.listenSock.recv()
                    so = "%s" % StringPickler.UnPackArbitraryObject(data)[0]
                    # if len(so) > 75:
                    #     so = so[:75] + "..."
                    print so
        finally:  # Get here on keyboard interrupt or other termination
            self.listenSock.close()
            self.context.term()


def main():
    parser = OptionParser()
    parser.add_option("-a", dest="ipAddr", default="127.0.0.1",
                      help="IP address of analyzer (def: 127.0.0.1)")
    parser.add_option("-p", dest="port", default=BROADCAST_PORT_PERIPH_ZMQ,
                      help="Peripheral rebroadcaster port (def: %d)" % BROADCAST_PORT_PERIPH_ZMQ)
    (options, args) = parser.parse_args()
    pzl = PeriphZmqListener(options.ipAddr, options.port)
    pzl.run()

if __name__ == "__main__":
    main()
