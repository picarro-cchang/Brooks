# Get Peripheral Data listens to the output of the data manager and filters out information 
#  which came from the peripherals

import os
import Queue
import sys
import wx
import threading
import time
import traceback
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from math import pi
from Host.Common.LineCacheMmap import getSlice, getSliceIter
from Host.Common import StringPickler
from Host.Common import timestamp
from GetPeripheralDataFrame import GetPeripheralDataFrame

try:
    import simplejson as json
except:
    import json
import httplib
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
    
class GetPeripheralDataWithGui(GetPeripheralDataFrame):
    def __init__(self, *args, **kwds):
        self.scriptFile = "periphProcessorFindWindInst.py"
        sourceString = file(self.scriptFile,"r").read().strip()
        sourceString = sourceString.replace("\r\n","\n")
        self.scriptCode = compile(sourceString, self.scriptFile, "exec") #providing path accurately allows debugging of script
        self.defaultGpsWsPath = None
        self.gpsFile = None
        self.wsFile = None
        self.outputDir = os.getcwd()
        self.outFile = os.path.join(self.outputDir, "windStats.txt")
        GetPeripheralDataFrame.__init__(self, *args, **kwds)
        self.bindEvents()
        
        # Get the contents of the GPS and WS files
        #self.setFiles(r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\WindTests20120222\GPSWS\FCDS2006-20120222-231108Z-DataLog_GPS_Raw.dat",
        #              r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\WindTests20120222\GPSWS\FCDS2006-20120222-231108Z-DataLog_WS_Raw.dat")

    def bindEvents(self):       
        self.Bind(wx.EVT_MENU, self.onLoadFileGpsMenu, self.iLoadFileGps)
        self.Bind(wx.EVT_MENU, self.onLoadFileWsMenu, self.iLoadFileWs)
        self.Bind(wx.EVT_MENU, self.onOutFileMenu, self.iOutFile)
        self.Bind(wx.EVT_BUTTON, self.onProcButton, self.procButton)              
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.closeButton) 
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrlMsg) 
        
    def runScript(self):
        try:
            exec self.scriptCode in self.scriptEnviron
        except Exception:
            print "Exception in PeriphDataProcessorScript"
            print traceback.format_exc()   
            sys.exit(1)
            
    def run(self):
        self.doneFlag = False
        self.gpsQueue = Queue.Queue(1000)
        self.wsQueue = Queue.Queue(1000)
        self.scriptEnviron = dict(
            SENSORLIST=[self.gpsQueue,self.wsQueue],
            RENDER_FIGURE=renderFigure,
            DONE=self.done,
            WRITEOUTPUT=self.writeOutput)
        
        self.scriptThread = threading.Thread(target=self.runScript)
        self.scriptThread.setDaemon(True)
        self.scriptThread.start()
        
        self.textCtrlMsg.Clear()
        self.textCtrlMsg.WriteText("Loading GPS and WS files...\n")
        self.loadFiles()
        
        if os.path.isfile(self.outFile):
            os.remove(self.outFile)
        self.op = file(self.outFile,"w",0)
        print >>self.op, "%-20s%-20s%-20s%-20s" % ("EPOCH_TIME","WIND_N","WIND_E","WIND_DIR_SDEV")
        
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
        self.textCtrlMsg.WriteText("Conversion Completed:\n")
        self.textCtrlMsg.WriteText("file:%s\n" % os.path.abspath(self.outFile))
        
    def done(self):
        return self.doneFlag and self.gpsQueue.qsize() == 0 and self.wsQueue.qsize() == 0 
        
    def stop(self):
        self.dmListener.stop()
    
    def writeOutput(self,ts,dataList):
        # print "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],(180.0/pi)*dataList[2])
        print >> self.op, "%-20.3f%-20.10f%-20.10f%-20.10f" % (timestamp.unixTime(ts),dataList[0],dataList[1],dataList[2])
      
      
    # Functions for GUI
    def onProcButton(self, event):
        self.enableAll(False)
        try:
            self.run()
        except Exception:
            self.textCtrlMsg.WriteText(traceback.format_exc())
        finally:
            self.enableAll(True)
        
    def onCloseButton(self, evt):
        sys.exit(0)
        self.Destroy()
        
    def onOverUrl(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlMsg.GetRange(event.GetURLStart()+5, event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()
            
    def onOutFileMenu(self, event):
        d = wx.FileDialog(self, "Select Output file", 
                         self.outputDir, self.outFile, wildcard = "*.txt", style=wx.OPEN)
        if d.ShowModal() == wx.ID_OK:
            self.outFile = d.GetPath()
            self.outputDir = os.path.dirname(self.outFile)
            d.Destroy()
        else:
            d.Destroy()
        self.textCtrlMsg.WriteText("%s selected\n" % self.outFile)
            
    def onLoadFileGpsMenu(self, event):
        if not self.defaultGpsWsPath:
            self.defaultGpsWsPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select GPS file...",
                            self.defaultGpsWsPath, wildcard = "*GPS*.dat", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.gpsFile = dlg.GetPath()
            self.outFile = os.path.join(self.outputDir, "windStats-%s.txt" % ("-".join(os.path.basename(self.gpsFile).split("-")[:3]),))
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultGpsWsPath = dlg.GetDirectory()
        self.textCtrlMsg.Clear()
        self.textCtrlMsg.WriteText("%s selected\n" % self.gpsFile)

    def onLoadFileWsMenu(self, event):
        if not self.defaultGpsWsPath:
            self.defaultGpsWsPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select WS file...",
                            self.defaultGpsWsPath, wildcard = "*WS*.dat", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.wsFile = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultGpsWsPath = dlg.GetDirectory()
        self.textCtrlMsg.WriteText("%s selected\n" % self.wsFile)
        
    def loadFiles(self):
        self.hGps = getSlice(self.gpsFile,0,1)[0].line.split()
        self.hWs = getSlice(self.wsFile,0,1)[0].line.split()
        self.itGps = getSliceIter(self.gpsFile,1)
        self.itWs = getSliceIter(self.wsFile,1)
        
    def enableAll(self, onFlag):
        self.iLoadFileGps.Enable(onFlag)
        self.iLoadFileWs.Enable(onFlag)
        self.procButton.Enable(onFlag)
        self.closeButton.Enable(onFlag)
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = GetPeripheralDataWithGui(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
