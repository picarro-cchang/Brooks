import cPickle
import subprocess
import time
import unittest
try:
    import json
except:
    import simplejson as json
import threading
import zmq

ADC_CMD_PORT = 5201
ADC_BROADCAST_PORT = 5202

class TestAdc(unittest.TestCase):
    def setUp(self):
    	self.zmqContext = zmq.Context()
        self.adcSender = subprocess.Popen(["python.exe",r".\adcSender.py"])
        
    def tearDown(self):
        self.adcSender.wait()
        self.zmqContext.term()

    def testGetLength(self):
        cmdSocket = self.zmqContext.socket(zmq.REQ)
        cmdSocket.connect("tcp://127.0.0.1:%d" % ADC_CMD_PORT)
        listenSocket = self.zmqContext.socket(zmq.SUB)
        listenSocket.connect("tcp://127.0.0.1:%d" % ADC_BROADCAST_PORT)
        listenSocket.setsockopt(zmq.SUBSCRIBE, "")

        cmdSocket.send(json.dumps({"func": "getNumSamples", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        cmdSocket.send(json.dumps({"func": "setSampleRate", "args": [1000]}))
        result = json.loads(cmdSocket.recv())
        print result
        time.sleep(2.0)

        print "START"
        cmdSocket.send(json.dumps({"func": "start", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        totLen = 0
        while totLen < 8000:
            data = cPickle.loads(listenSocket.recv())
            totLen += len(data)
            print totLen

        cmdSocket.send(json.dumps({"func": "getSampleRate", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        print "STOP"
        cmdSocket.send(json.dumps({"func": "stop", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        cmdSocket.send(json.dumps({"func": "getNumSamples", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result

        print "START"
        cmdSocket.send(json.dumps({"func": "start", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        totLen = 0
        while totLen < 8000:
            data = cPickle.loads(listenSocket.recv())
            totLen += len(data)
            print totLen
        print "STOP"
        cmdSocket.send(json.dumps({"func": "stop", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        cmdSocket.send(json.dumps({"func": "getNumSamples", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result

        print "CLOSE"
        cmdSocket.send(json.dumps({"func": "close", "args": []}))
        result = json.loads(cmdSocket.recv())
        print result
        cmdSocket.close()     
	pass

if __name__ == '__main__':
    unittest.main()	