#!/usr/bin/env python
import socket
import sys
import Queue
import threading
import struct
from numpy import *
from collections import deque
from matplotlib import pyplot 
from parserFunc import *
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_PERIPH_INTRF

APP_NAME = "Sensor Interpolator"
APP_DESCRIPTION = "Socket client and interpolator"
__version__ = 1.0
MAX_SENSOR_QUEUE_SIZE = 2000

HOST = 'localhost'
PORT = 5193
#PORT = 8037

NUM_CHANNELS = 4
PARSER = [parseAnemometer, parseDefault, parseDefault, parseDefault]
DATALABELS = [["Anemometer_ux", "Anemometer_uy", "Anemometer_uz", "Anemometer_c"],[],[],[]]
     
class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
            print "RpcServer exited and no longer serving."
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            print "Exception raised when calling exit function at exit of RPC server."
     
def linInterp(pPair, tPair, t):
    try:
        dtime = tPair[1] - tPair[0]
        if dtime == 0:
            return 0.5*(pPair[0] + pPair[1])
        else:
            return ((t-tPair[0])*pPair[1] + (tPair[1]-t)*pPair[0]) / dtime
    except:
        return None
        
class PeriphIntrf(object):
    def __init__(self):
        self.queue = Queue.Queue(0)
        self.sock = None
        self.getThread = None
        self.sensorList = []
        for port in range(NUM_CHANNELS):
            self.sensorList.append(deque())
        self.sensorLock = threading.Lock()
        self._shutdownRequested = False
        self.connect()
        self.startSocketThread()
        self.startStateMachineThread()
        self.startServer()
        
    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_PERIPH_INTRF),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)
        self.rpcServer.register_function(self.getDataByTime)
        self.rpcServer.register_function(self.selectDataByTime)
        # Start the rpc server on another thread...
        #self.rpcThread = RpcServerThread(self.rpcServer, self.shutdown)
        self.rpcServer.serve_forever()
        
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            raise
            
    def getFromSocket(self):
        try:
            while not self._shutdownRequested:
                data = self.sock.recv(1024)
                if len(data)>0:
                    for c in data: 
                        self.queue.put(c)
        finally:
            self.sock.close()

    def sensorStateMachine(self):
        state = "SYNC1"
        value = 0
        counter = 0
        while not self._shutdownRequested:
            try:
                c = self.queue.get(timeout=1.0)
            except Queue.Empty:
                continue
            if state == "SYNC1":
                if ord(c) == 0x5A: state = "SYNC2"
            elif state == "SYNC2":
                if ord(c) == 0xA5: 
                    value, counter, maxcount = 0, 0, 8
                    state = "TIMESTAMP"
                else:
                    state = "SYNC1"
            elif state == "TIMESTAMP":
                value += ord(c)<<(8*counter)
                counter += 1
                if counter == maxcount:
                    ts = value
                    state = "PORT"
            elif state == "PORT":
                port = ord(c)
                value, counter, maxcount = 0, 0, 2
                state = "BYTECOUNT"
            elif state == "BYTECOUNT":
                value += ord(c)<<(8*counter)
                counter += 1
                if counter == maxcount:
                    print ts, port, value
                    counter, maxcount = 0, value
                    newStr = ""
                    state = "DATA"
            elif state == "DATA":
                newStr += c
                if c not in ['\r','\n']: 
                    pass
                    #sys.stdout.write(c)
                counter += 1
                if counter >= maxcount:
                    #sys.stdout.write('\n')
                    # Store in sensorList
                    self.sensorLock.acquire()
                    try:
                        # print ts, ["%02x"%ord(c) for c in newStr]
                        self.sensorList[port].append((ts, PARSER[port](newStr)))
                        if len(self.sensorList[port]) > MAX_SENSOR_QUEUE_SIZE:
                            self.sensorList[port].popleft()
                    except Exception, err:
                        print "%r" % (err,)
                    finally:
                        self.sensorLock.release()
                    state = "SYNC1"

    def startSocketThread(self):
        appThread = threading.Thread(target = self.getFromSocket)
        appThread.setDaemon(True)
        appThread.start()
        
    def startStateMachineThread(self):
        appThread = threading.Thread(target = self.sensorStateMachine)
        appThread.setDaemon(True)
        appThread.start()
        
    def run(self):
        self.connect()
        self.startSocketThread()
        self.startStateMachineThread()
         
    def selectDataByTime(self, requestTime):
        sensorDataList = [[[], []]]*NUM_CHANNELS
        self.sensorLock.acquire()
        try:
            for port in range(NUM_CHANNELS):
                lastVal = (None, [])
                for idx in range(len(self.sensorList[port])):
                    (ts, valList) = self.sensorList[port][idx]
                    if len(valList) > 0:
                        if ts >= requestTime:
                            # Save a list of [[time0, time1], [(val00, val01), (val10, val11), (val20, val21), ...]]
                            sensorDataList[port] = [[lastVal[0], ts], zip(lastVal[1], valList)]
                            break
                        else:
                            lastVal = (ts, valList)
        except Exception, err:
            print "%r" % (err,)
        finally:
            self.sensorLock.release()
        return sensorDataList
        
    def getDataByTime(self, requestTime, dataList):
        sensorDataList = self.selectDataByTime(requestTime)
        interpDict = {}
        for port in range(NUM_CHANNELS):
            timeDataLists = sensorDataList[port]
            for dataIdx in range(len(timeDataLists[1])):
                interpDict[DATALABELS[port][dataIdx]] = linInterp(timeDataLists[1][dataIdx], timeDataLists[0], requestTime)
        retList = []
        for data in dataList:
            try:
                retList.append(interpDict[data])
            except:
                retList.append(None)
        return retList
        
    def shutdown(self):
        self._shutdownRequested = True
        
if __name__ == "__main__":
    r = PeriphIntrf()