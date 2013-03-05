# Get Peripheral Data listens to the output of the data manager and filters out information 
#  which came from the peripherals

import os
from configobj import ConfigObj
import Queue
import sys
import threading
import time
import traceback
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from math import pi
from Host.Common.LineCacheMmap import getSlice, getSliceIter
from Host.Common import StringPickler
from Host.Common import timestamp

try:
    import simplejson as json
except:
    import json
import httplib
import socket
import urllib
    
def line2Dict(line,header):
    result = {}
    if line:
        vals = line.split()
        if len(vals) == len(header): 
            for col,val in zip(header,vals):
                result[col] = float(val)
    return result
    
class GetPeripheralDataBatch(object):
    def __init__(self, iniFile):
        if not os.path.exists(iniFile):
            raise ValueError("Configuration file %s missing" % iniFile)
        self.config = ConfigObj(iniFile)
        self.scriptFile = "ProcessorFindWindInst.py"
        sourceString = file(self.scriptFile,"r").read().strip()
        sourceString = sourceString.replace("\r\n","\n")
        self.scriptCode = compile(sourceString, self.scriptFile, "exec") #providing path accurately allows debugging of script

    def runScript(self):
        try:
            exec self.scriptCode in self.scriptEnviron
        except Exception:
            print "Exception in PeriphDataProcessorScript"
            print traceback.format_exc()   
            sys.exit(1)
            
    def run(self):
        varList = {'GPS_WS_DIR':'gpsWsPath','GPS_FILE':'gpsFile',
                   'WS_FILE':'wsFile','WIND_FILE':'outFile',
                   'STATSAVG':'statsAvg','ANEMDELAY':'anemDelay',
                   'COMPASSDELAY':'compassDelay','DISTFROMAXLE':'distFromAxle',
                   'SPEEDFACTOR':'speedFactor'}
        
        for secName in self.config:
            if secName == 'DEFAULTS': continue
            if 'DEFAULTS' in self.config:
                for v in varList:
                    if v in self.config['DEFAULTS']: 
                        setattr(self,varList[v],self.config['DEFAULTS'][v])
                    else: 
                        setattr(self,varList[v],None)
            for v in varList:
                if v in self.config[secName]: 
                    setattr(self,varList[v],self.config[secName][v])
            self.statsAvg = int(self.statsAvg)
            self.anemDelay = float(self.anemDelay)
            self.speedFactor = float(self.speedFactor)
            self.compassDelay = float(self.compassDelay)
            self.distFromAxle = float(self.distFromAxle)
            self.gpsFile = os.path.join(self.gpsWsPath,self.gpsFile)
            self.wsFile = os.path.join(self.gpsWsPath,self.wsFile)
            self.outFile = os.path.join(self.gpsWsPath,self.outFile)
            self._run()
            
    def _run(self):
        self.doneFlag = False
        self.gpsQueue = Queue.Queue(1000)
        self.wsQueue  = Queue.Queue(1000)
        self.scriptEnviron = dict(
            SENSORLIST=[self.gpsQueue,self.wsQueue],
            DONE=self.done,
            PARAMS={'STATSAVG':self.statsAvg,'ANEMDELAY':self.anemDelay,
                    'COMPASSDELAY':self.compassDelay,'DISTFROMAXLE':self.distFromAxle,
                    'SPEEDFACTOR':self.speedFactor},
            WRITEOUTPUT=self.writeOutput)
       
        self.scriptThread = threading.Thread(target=self.runScript)
        self.scriptThread.setDaemon(True)
        self.scriptThread.start()
        print "Processing %s and %s" % (self.gpsFile,self.wsFile)
        self.loadFiles()
        self.op = file(self.outFile,"w",0)
        print >>self.op, "%-20s%-20s%-20s%-20s%-20s" % ("EPOCH_TIME","WIND_N","WIND_E","WIND_DIR_SDEV","CAR_SPEED")
        
        while True:
            try:
                # Get GPS
                lGps = self.itGps.next()
                dGps = line2Dict(lGps.line, self.hGps)
                ts = int(timestamp.unixTimeToTimestamp(dGps['EPOCH_TIME']))
                self.gpsQueue.put((ts, dGps))
                # Get WS
                lWs = self.itWs.next()
                dWs = line2Dict(lWs.line, self.hWs)
                ts = int(timestamp.unixTimeToTimestamp(dWs['EPOCH_TIME']))
                self.wsQueue.put((ts, dWs))
            except StopIteration,e:
                self.gpsQueue.put(None)
                self.wsQueue.put(None)
                print "Out of data"
                break
                
        print "Waiting for PeripDataProcessorScript to terminate"
        self.doneFlag = True
        self.scriptThread.join()
        print "PeripDataProcessorScript terminated"
        self.op.close()
        print "Output file:%s" % os.path.abspath(self.outFile)
        
    def done(self):
        return self.doneFlag and (self.gpsQueue.qsize() == 0 or self.wsQueue.qsize() == 0)
    
    def writeOutput(self,ts,dataList):
        windN = dataList[0]
        windE = dataList[1]
        stdDevDeg = dataList[2]
        vCarN = dataList[3]
        vCarE = dataList[4]
        vCar = abs(vCarN+1j*vCarE)
        print >> self.op, "%-20.3f%-20.10f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),windN,windE,stdDevDeg,vCar)
        
    def loadFiles(self):
        self.hGps = getSlice(self.gpsFile,0,1)[0].line.split()
        self.hWs = getSlice(self.wsFile,0,1)[0].line.split()
        self.itGps = getSliceIter(self.gpsFile,1)
        self.itWs = getSliceIter(self.wsFile,1)
        
if __name__ == "__main__":
    if len(sys.argv)<2:
        print 'Please specify INI file as argument to script'
    app = GetPeripheralDataBatch(sys.argv[1])
    app.run()
