# Model code
# We have a REQ socket for 
# We have a PUB socket that broadcasts information about the model, which any subscribers may use (e.g. to display information about the model state)

try:
    import json
except:
    import simplejson as json

import math
import time
import zmq
context = zmq.Context()

CMD_PORT = 5101
BROADCAST_PORT = 5102
 
class View(object):
    def __init__(self):
        self.cmdSock = context.socket(zmq.REQ)
        self.cmdSock.connect("tcp://127.0.0.1:%d" % CMD_PORT)
        self.broadcastSock = context.socket(zmq.SUB)
        self.broadcastSock.connect("tcp://127.0.0.1:%d" % BROADCAST_PORT)
        self.broadcastSock.setsockopt(zmq.SUBSCRIBE, "")
    
    def run(self):
        poller = zmq.Poller()
        poller.register(self.broadcastSock, zmq.POLLIN)
        while True:
            socks = dict(poller.poll())
            if socks.get(self.broadcastSock) == zmq.POLLIN:
                data = self.broadcastSock.recv()
                print data
        self.cmdSock.close()
        self.broadcastSock.close()

if __name__ == "__main__":
    v = View()
    v.run()