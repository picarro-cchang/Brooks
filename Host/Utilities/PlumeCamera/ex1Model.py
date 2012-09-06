# Model code
# We have a REQ socket for 
# We have a PUB socket that broadcasts information about the model, which any subscribers may use (e.g. to display information about the model state)

try:
    import json
except:
    import simplejson as json

import math
import time
import traceback
import zmq
context = zmq.Context()

CMD_PORT = 5101
BROADCAST_PORT = 5102
  
class Model(object):
    def __init__(self):
        self.cmdSock = context.socket(zmq.REP)
        self.cmdSock.bind("tcp://0.0.0.0:%d" % CMD_PORT)
        self.broadcastSock = context.socket(zmq.PUB)
        self.broadcastSock.bind("tcp://0.0.0.0:%d" % BROADCAST_PORT)
        self.terminate = False
        self.input = None
        self.output = None
        
    def squareAndStore(self,data):
        self.output = data**2
        return self.output
        
    def run(self):
        t = time.time()
        nextTime = math.ceil(t)
        
        poller = zmq.Poller()
        poller.register(self.cmdSock, zmq.POLLIN)
        while not self.terminate:
            timeout = 1000*(nextTime - time.time())
            socks = {}
            if timeout>0: socks = dict(poller.poll(timeout=timeout))
            # Check for no available sockets, indicating that the timeout occured 
            if not socks:
                print "Broadcasting"
                self.broadcastSock.send("TICK\n" + json.dumps({"time": time.time(), "output": self.output}))
                nextTime += 5.0
            elif socks.get(self.cmdSock) == zmq.POLLIN:
                cmd = json.loads(self.cmdSock.recv())
                func = cmd["func"]
                self.input = cmd["args"]
                try:
                    print getattr(self,func)(*self.input)
                    self.cmdSock.send(json.dumps({"result":"OK"}))
                except Exception, e:
                    self.cmdSock.send(json.dumps({"error":"%s"%e, "traceback":traceback.format_exc()}))
                self.broadcastSock.send("RESULT\n" + json.dumps({"time": time.time(), "output": self.output}))
        self.cmdSock.close()
        self.broadcastSock.close()

if __name__ == "__main__":
    m = Model()
    m.run()
    