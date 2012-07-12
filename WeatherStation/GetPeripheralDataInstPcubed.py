# GetPeripheralDataInstPcubed gets weather station and GPS data from P3 and writes 
#  out a wind statistics file with the help of a script file

import os
from configobj import ConfigObj
import Queue
import sys
import threading
import time
import traceback
from math import pi
from Host.Common import StringPickler
from Host.Common import timestamp

try:
    import simplejson as json
except:
    import json
import httplib
import socket
import urllib
import getFromP3 as gp3
    
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
        self.scriptFile = "periphProcessorFindWindInst3.py"
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
        varList = {'ANALYZER':'analyzer','START_ETM':'startEtm',
                   'END_ETM':'endEtm','STATSAVG':'statsAvg',
                   'WIND_FILE':'outFile', # Full path to wind file
                   'ANEMDELAY':'anemDelay','COMPASSDELAY':'compassDelay',
                   'DISTFROMAXLE':'distFromAxle','SPEEDFACTOR':'speedFactor'}
        
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
            
            self.startEtm = float(self.startEtm)
            self.endEtm = float(self.endEtm)
            self.statsAvg = int(self.statsAvg)
            self.anemDelay = float(self.anemDelay)
            self.speedFactor = float(self.speedFactor)
            self.compassDelay = float(self.compassDelay)
            self.distFromAxle = float(self.distFromAxle)
            self._run()
            
    def _run(self):
        self.doneFlag = False
        self.gpsQueue = Queue.Queue(10000)
        self.wsQueue  = Queue.Queue(10000)
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
        self.op = file(self.outFile,"w",0)
        print >>self.op, "%-20s%-20s%-20s%-20s%-20s" % ("EPOCH_TIME","WIND_N","WIND_E","WIND_DIR_SDEV","CAR_SPEED")
        
        p3 = gp3.P3_Accessor(self.analyzer)
        gpsSource = gp3.P3_Source(p3.genGpsData,endEtm=self.endEtm,limit=5000)
        wsSource  = gp3.P3_Source(p3.genWsData,endEtm=self.endEtm,limit=5000)
        syncSource = gp3.SyncSource([gpsSource,wsSource],[0.0,0.0],interval=1.0,startEtm=self.startEtm)
        for d in syncSource.generator():
            if d is None:
                print "Awaiting data"
                time.sleep(1.0)
            else:
                etm,data = d
                ts = int(timestamp.unixTimeToTimestamp(etm))
                while True:
                    try:
                        self.gpsQueue.put((ts,data[0]))
                        break
                    except Queue.Full:
                        time.sleep(1.0)
                while True:
                    try:
                        self.wsQueue.put((ts,data[1]))
                        break
                    except Queue.Full:
                        time.sleep(1.0)
        self.gpsQueue.put(None)
        self.wsQueue.put(None)
        print "Waiting for PeripDataProcessorScript to terminate"
        self.scriptThread.join()
        print "PeripDataProcessorScript terminated"
        self.op.close()
        print "Output file:%s" % os.path.abspath(self.outFile)
        
    def done(self):
        return self.doneFlag and self.gpsQueue.qsize() == 0 and self.wsQueue.qsize() == 0 
    
    def writeOutput(self,ts,dataList):
        # print "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],(180.0/pi)*dataList[2])
        print >> self.op, "%-20.3f%-20.10f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],dataList[2],dataList[3])
                
if __name__ == "__main__":
    if len(sys.argv)<2:
        print 'Please specify INI file as argument to script'
    app = GetPeripheralDataBatch(sys.argv[1])
    app.run()
