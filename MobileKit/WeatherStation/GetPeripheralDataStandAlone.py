# Get Peripheral Data listens to the output of the data manager and filters out information 
#  which came from the peripherals

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
import os
import socket
import urllib

HOST = 'localhost:5200'

class RestCallError(Exception):
    pass

class RestCallTimeout(Exception):
    pass
    
def restCall(host, callUrl, method, params={}):
    conn = httplib.HTTPConnection(host)
    url = callUrl + '/' + method
    try:
        conn.request("GET","%s?%s" % (url,urllib.urlencode(params)))
        r = conn.getresponse()
        if not r.reason == 'OK':
            raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
        else:
            return json.loads(r.read()).get("result",{})
    except socket.timeout:
        raise RestCallTimeout(traceback.format_exc())
    finally:
        conn.close()

def registerImage(name,when):
    return restCall(HOST,'/rest','newImage',{'name':name,'when':when})

def getImagePath():
    try:
        return restCall(HOST,'/rest','getImagePath')['path']
    except:
        return None
        
def renderFigure(fig,name):
    when = int(time.time())
    canvas = FigureCanvas(fig)
    fp = open(os.path.join(getImagePath(),'%s/%d.png'%(name,when)),'wb')
    canvas.print_figure(fp,facecolor='w',edgecolor='w',format='png')
    fp.close()
    try:
        registerImage(name,when)
    except:
        print traceback.format_exc()
    
def line2Dict(line,header):
    result = {}
    if line:
        vals = line.split()
        if len(vals) == len(header): 
            for col,val in zip(header,vals):
                result[col] = float(val)
    return result
    
class GetPeripheralData(object):
    def __init__(self):
        self.doneFlag = False
        self.gpsQueue = Queue.Queue(1000)
        self.wsQueue = Queue.Queue(1000)
        self.scriptEnviron = dict(
            SENSORLIST=[self.gpsQueue,self.wsQueue],
            RENDER_FIGURE=renderFigure,
            DONE=self.done,
            WRITEOUTPUT=self.writeOutput)
        self.scriptFile = "periphProcessorFindWind.py"
        sourceString = file(self.scriptFile,"r").read().strip()
        sourceString = sourceString.replace("\r\n","\n")
        self.scriptCode = compile(sourceString, self.scriptFile, "exec") #providing path accurately allows debugging of script
        self.op = file("windStats.txt","w",0)
        print >>self.op, "%-20s%-20s%-20s%-20s" % ("EPOCH_TIME","WIND_N","WIND_E","WIND_DIR_SDEV")
        
        # Get the contents of the GPS and WS files
        self.setFiles(r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\WindTests20120222\GPSWS\FCDS2006-20120222-231108Z-DataLog_GPS_Raw.dat",
                      r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\WindTests20120222\GPSWS\FCDS2006-20120222-231108Z-DataLog_WS_Raw.dat")

    def setFiles(self, gpsFile, wsFile):
        self.hGps = getSlice(gpsFile,0,1)[0].line.split()
        self.hWs = getSlice(wsFile,0,1)[0].line.split()
        self.itGps = getSliceIter(gpsFile,1)
        self.itWs = getSliceIter(wsFile,1)
        
    def runScript(self):
        try:
            exec self.scriptCode in self.scriptEnviron
        except Exception:
            print "Exception in PeriphDataProcessorScript"
            print traceback.format_exc()   
            sys.exit(1)
            
    def run(self):
        self.scriptThread = threading.Thread(target=self.runScript)
        self.scriptThread.setDaemon(True)
        self.scriptThread.start()
        
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
        self.scriptThread.join()
        print "PeripDataProcessorScript terminated"
        self.op.close()
        
    def done(self):
        return self.doneFlag and self.gpsQueue.qsize() == 0 and self.wsQueue.qsize() == 0 
        
    def stop(self):
        self.dmListener.stop()
    
    def writeOutput(self,ts,dataList):
        print "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],(180.0/pi)*dataList[2])
        print >> self.op, "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],dataList[2])
        
if __name__ == "__main__":
    dm = GetPeripheralData()
    dm.run()
