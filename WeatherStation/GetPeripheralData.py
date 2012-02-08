# Get Peripheral Data listens to the output of the data manager and filters out information 
#  which came from the peripherals

import Queue
import sys
import threading
import time
import traceback
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER
from Host.Common.Listener import Listener
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from math import pi

try:
    import simplejson as json
except:
    import json
import httplib
import os
import socket
import urllib

HOST = 'localhost:5200'
# Dummy address for debugging
BROADCAST_PORT_DATA_MANAGER = 40500

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
        
def Log(msg):
    print msg
    
class DataManagerOutput(object):
    def __init__(self):
        self.doneFlag = False
        self.dmQueue = Queue.Queue(0)
        self.gpsQueue = Queue.Queue(100)
        self.wsQueue = Queue.Queue(100)
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
        
    def listen(self):
        self.dmListener = Listener(self.dmQueue,
                                    BROADCAST_PORT_DATA_MANAGER,
                                    StringPickler.ArbitraryObject,
                                    retry = True,
                                    name = "DataManagerOutput Listener",
                                    logFunc = Log)
                                    
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
            output = self.dmQueue.get()
            if isinstance(output,Exception):
                self.doneFlag = True
                break
            elif output['source'] == 'parseGPS':
                ts = int(timestamp.unixTimeToTimestamp(output['time']))
                self.gpsQueue.put((ts,output['data']))
            elif output['source'] == 'parseWeatherStation':
                ts = int(timestamp.unixTimeToTimestamp(output['time']))
                self.wsQueue.put((ts,output['data']))
        print "Waiting for PeripDataProcessorScript to terminate"
        self.scriptThread.join()
        
    def done(self):
        return self.doneFlag and self.gpsQueue.qsize() == 0 and self.wsQueue.qsize() == 0 
        
    def stop(self):
        self.dmListener.stop()
    
    def writeOutput(self,ts,dataList):
        # print "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],(180.0/pi)*dataList[2])
        print >> self.op, "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],dataList[2])
        
if __name__ == "__main__":
    dm = DataManagerOutput()
    dm.listen()
    dm.run()
