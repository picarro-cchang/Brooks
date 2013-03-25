# adcSender broadcasts the measurements made on the Measurement Computing ADC card via a 0MQ socket

import cPickle
from ctypes import c_int, c_long, c_ulong, c_short, c_ushort, c_void_p, POINTER
from ctypes import byref, create_string_buffer, windll
try:
    import json
except:
    import simplejson as json

import MeasurementComputing.MeasComp as mc
import sys
import time
import traceback
import zmq
from Host.Common.timestamp import getTimestamp

context = zmq.Context()

ADC_CMD_PORT = 5201
ADC_BROADCAST_PORT = 5202

class MCC_Board(object):
    def __init__(self, boardNum):
        self.boardNum = boardNum
        self.cmdSock = context.socket(zmq.REP)
        self.cmdSock.bind("tcp://0.0.0.0:%d" % ADC_CMD_PORT)
        self.broadcastSock = context.socket(zmq.PUB)
        self.broadcastSock.bind("tcp://0.0.0.0:%d" % ADC_BROADCAST_PORT)
        self.terminate = False

    def adcConfigure(self):
        self.bufferLength = 465000
        self.adcGain = mc.BIP10VOLTS
        self.measComp = mc.MeasComp()

        self.adRes = c_int(0)
        self.measComp.cbGetConfig(mc.BOARDINFO,self.boardNum,0,mc.BIADRES,byref(self.adRes))
        print "ADC resolution: ", self.adRes.value
        self.boardType = c_int(0)
        self.measComp.cbGetConfig(mc.BOARDINFO,self.boardNum,0,mc.BIBOARDTYPE,byref(self.boardType))
        print "Board Type: ", self.boardType.value

        self.memHandle = self.measComp.cbWinBufAlloc(self.bufferLength)
        if self.memHandle == 0: raise ValueError("Out of memory")
        self.adcData = (c_ushort*self.bufferLength).from_address(self.memHandle)
        self.adcOptions = mc.CONTINUOUS + mc.CONVERTDATA + mc.BACKGROUND

        self.adcChan = 4
        self.adcLowChan = 0
        self.adcHighChan = self.adcChan-1
        self.adcRate = 100
        self.actualRate = c_int(self.adcRate)

    def adcGetBlock(self):
        self.measComp.cbGetStatus(self.boardNum,byref(self.status),
            byref(self.curCount), byref(self.curIndex), mc.AIFUNCTION)
        count = self.adcChan*(self.curCount.value // self.adcChan)
        index = self.adcChan*(self.curIndex.value // self.adcChan) if self.curIndex.value>0 else 0
        if count - self.lastCount >= self.bufferLength:
            raise RuntimeError("ADC buffer overrun!")
        # ADC data is from lastIndex to curIndex, wrapping at self.bufferLength
        if self.lastIndex <= index:
            x = self.adcData[self.lastIndex:index]
        else:
            x = self.adcData[self.lastIndex:] + self.adcData[:index]
        self.nextAdcRead += 1000*self.adcReadInterval
        npts = len(x)
        if npts>0:
            n = npts//self.adcChan
            self.broadcastSock.send(cPickle.dumps([x[i*self.adcChan:(i+1)*self.adcChan] for i in range(n)]))
        self.totLen += npts
        self.lastIndex = (self.lastIndex + npts) % self.bufferLength
        self.lastCount = (self.lastCount + npts)

    def dioConfigure(self):
        """Configures all digital lines as outputs"""
        self.measComp.cbDConfigPort(self.boardNum,mc.FIRSTPORTA,mc.DIGITALOUT)
        self.measComp.cbDConfigPort(self.boardNum,mc.FIRSTPORTB,mc.DIGITALOUT)

    def run(self):
        self.totLen = 0
        poller = zmq.Poller()
        poller.register(self.cmdSock, zmq.POLLIN)
        self.status = c_short(0)
        self.curCount = c_ulong(0)
        self.curIndex = c_long(0)
        self.lastCount = 0
        self.lastIndex = 0

        while True:
            self.adcReadInterval = min(0.5,0.75*float(self.bufferLength)/(self.adcChan*self.adcRate))
            self.nextAdcRead = getTimestamp() + 1000*self.adcReadInterval
            while True:
                timeout = self.nextAdcRead - getTimestamp()
                socks = {}
                if timeout>0: socks = dict(poller.poll(timeout=timeout))
                # Check for no available sockets, indicating that the timeout occured
                if not socks:
                    self.adcGetBlock()
                elif socks.get(self.cmdSock) == zmq.POLLIN:
                    cmd = json.loads(self.cmdSock.recv())
                    func = cmd["func"]
                    self.input = cmd["args"]
                    try:
                        breakFunc, response = getattr(self,func)(*self.input)
                        self.cmdSock.send(json.dumps(response))
                        if breakFunc: break
                    except Exception, e:
                        self.cmdSock.send(json.dumps({"error":"%s"%e, "traceback":traceback.format_exc()}))
            self.measComp.cbStopBackground(self.boardNum,mc.AIFUNCTION)
            if breakFunc(self): break
        self.cmdSock.close()
        self.broadcastSock.close()

    def start(self):
        """Start data acquisition"""
        def _start(self):
            self.status = c_short(0)
            self.curCount = c_ulong(0)
            self.curIndex = c_long(0)
            self.lastCount = 0
            self.lastIndex = 0
            self.totLen = 0
            self.actualRate.value = self.adcRate
            self.measComp.cbAInScan(self.boardNum,self.adcLowChan,self.adcHighChan,
                self.bufferLength,byref(self.actualRate), self.adcGain, self.memHandle, self.adcOptions)
            return False
        return (_start, {"name": sys._getframe().f_code.co_name, "result": "OK"})

    def stop(self):
        """Stop data acquisition"""
        self.adcGetBlock()
        return (lambda s: False, {"name": sys._getframe().f_code.co_name, "result": "OK"})

    def close(self):
        """Stops acquisition and leaves program"""
        return (lambda s: True, {"name": sys._getframe().f_code.co_name, "result": "OK"})

    def setSampleRate(self, rate):
        self.adcRate = rate
        return (False, {"name": sys._getframe().f_code.co_name, "result": "OK" })

    def getSampleRate(self):
        return (False, {"name": sys._getframe().f_code.co_name, "result": self.actualRate.value })

    def getNumSamples(self):
        return (False, {"name": sys._getframe().f_code.co_name, "result": self.totLen })

    def setDigitalPortA(self,mask):
        self.measComp.cbDOut(self.boardNum,mc.FIRSTPORTA,mask&0xFF)
        return (False, {"name": sys._getframe().f_code.co_name, "result": "OK" })

    def setDigitalPortB(self,mask):
        self.measComp.cbDOut(self.boardNum,mc.FIRSTPORTB,mask&0xFF)
        return (False, {"name": sys._getframe().f_code.co_name, "result": "OK" })

if __name__ == "__main__":
    a = MCC_Board(1)
    a.adcConfigure()
    a.dioConfigure()
    a.run()
