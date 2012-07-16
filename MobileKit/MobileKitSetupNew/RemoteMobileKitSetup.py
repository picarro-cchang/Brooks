#!/usr/bin/python
#
# File Name: RemoteMobileKitSetup.py
# Purpose: Setup GUI for Picarro Mobile Kit
#
# File History:
# 2011-09-14 Alex Lee  Created

import sys
sys.path.append(r"..\ViewServer")
import os
import wx
import shutil
import subprocess
import psutil
import win32gui
import threading
import time
import httplib
import urllib
import traceback
import socket
import simplejson as json
from CustomConfigObj import CustomConfigObj
from SingleInstance import SingleInstance
from RemoteMobileKitSetupFrame import RemoteMobileKitSetupFrame
from SecureRestProxy import SecureRestProxy

DEFAULT_CONFIG_NAME = "MobileKitSetup.ini"
MAX_REST_ERROR_COUNT = 5

OPACITY_DICT = {"25%":"3F", "50%":"7F", "75%":"BF", "100%":"FF"}
OPACITY_LIST = ["25%", "50%", "75%", "100%"]

TIMEOUT = 15.0
socket.setdefaulttimeout(TIMEOUT)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

def getPidList():
    return [p.pid for p in psutil.get_process_list()]
   
class RestCallError(Exception):
    pass

class RestCallTimeout(Exception):
    pass
   
def url_join(*args):
    """Join any arbitrary strings into a forward-slash delimited list.
    Do not strip leading / from first element, nor trailing / from last element."""
    if len(args) == 0:
        return ""

    if len(args) == 1:
        return str(args[0])

    else:
        args = [str(arg).replace("\\", "/") for arg in args]

        work = [args[0]]
        for arg in args[1:]:
            if arg.startswith("/"):
                work.append(arg[1:])
            else:
                work.append(arg)

        joined = reduce(os.path.join, work)

    return joined.replace("\\", "/")
    
class RestProxy(object):
    # Proxy to make a rest call to a server
    def __init__(self,host,baseUrl):
        self.host = host
        self.baseUrl = baseUrl
    # Attributes are mapped to a function which performs
    #  a GET request to host/rest/attrName
    def __getattr__(self,attrName):
        def dispatch(argsDict):
            url = "%s/%s" % (self.baseUrl,attrName)
            print self.host, "GET","%s?%s" % (url,urllib.urlencode(argsDict))
            conn = httplib.HTTPConnection(self.host)
            try:
                conn.request("GET","%s?%s" % (url,urllib.urlencode(argsDict)))
                r = conn.getresponse()
                if not r.reason == 'OK':
                    raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
                else:
                    return json.loads(r.read()).get("result",{})
            finally:
                conn.close()
        return dispatch
    
class RemoteMobileKitSetup(RemoteMobileKitSetupFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = CustomConfigObj(configFile)
        self.setupIniFile = os.path.abspath(configFile)
        self.activeIniFile = self.co.get("Main", "activeIniPath")
        self.inactiveIniFile = self.co.get("Main", "inactiveIniPath")
        if os.path.isfile(self.activeIniFile):
            self.targetIniFile = self.activeIniFile
        else:
            self.targetIniFile = self.inactiveIniFile
        if not os.path.isfile(self.targetIniFile):
            d = wx.MessageDialog(None, "Mobile Kit INI file not found", "Error", wx.ICON_ERROR|wx.STAY_ON_TOP)
            d.ShowModal()
            return
        try:
            self.targetConfig = CustomConfigObj(self.targetIniFile)
        except Exception, err:
            print err
            d = wx.MessageDialog(None, "Error in Mobile Kit INI file: %r" % err, "Error", wx.ICON_ERROR|wx.STAY_ON_TOP)
            d.ShowModal()
            return
            
        concList = self.targetConfig.list_sections()
        concList.remove("SETTINGS")
        RemoteMobileKitSetupFrame.__init__(self, concList, *args, **kwds)
            
        self.bindEvents()
        self.setInit()

        # Set up REST service
        if self.secure:
            self.restService = SecureRestProxy("https://"+self.csp_url, self.svc, 
                                               "https://"+self.ticket_url, self.identity, self.psys)
        else:
            urlcomp = self.url.split("/",1)
            host = urlcomp[0]
            restUrl = "/"
            if len(urlcomp)>1: restUrl += urlcomp[1]
            self.restService = RestProxy(host,restUrl)
        
        self.analyzerList = []
        self.nameList = []
        self.alogList = []
        
        # Set the analyzer list
        self.getAnalyzerList()
        self.analyzerCtrl.Clear()
        for name in self.analyzerList: 
            self.analyzerCtrl.Append(name) 
            
        statusThread = threading.Thread(target = self._updateStatus)
        statusThread.setDaemon(True)
        statusThread.start()
        
    def _updateStatus(self):
        while True:
            try:
                alog = self.getAlog()
                if alog:
                    result = self.restService.getData({'alog':alog, 'startPos':-1, 'varList':json.dumps(self.concList)})
                    if "error" in result:
                        pass
                    else:
                        for i in range(len(self.concList)):
                            conc = self.concList[i]
                            if conc in result:
                                concValue = float(result[conc][-1])
                            else:
                                concValue = 0.0
                            self.textCtrlConc[i].SetValue("%.3f"%concValue)
            except:
                print traceback.format_exc()
            time.sleep(2.0)

    def getAnalyzerList(self):
        try:
            self.analyzerList = self.restService.getAnalyzerList({})["analyzerList"]
        except Exception:
            print traceback.format_exc()
        
    def getDataList(self, analyzer):
        try:
            dataList = self.restService.getDatLogList({"analyzer":analyzer})["logList"]
            self.alogList = [d["alog"] for d in dataList]
            self.nameList = [d["name"] for d in dataList]
        except Exception:
            print traceback.format_exc()
            
    def getAlog(self):
        name = self.dataCtrl.GetValue()
        try:
            alog = self.alogList[self.nameList.index(name)]
        except ValueError:
            alog = ''
        return alog
        
    def setInit(self):
        # Start view server
        self.secure = int(self.co.get("Server", "secure", 0))
        if self.secure:
            self.csp_url = self.co.get("Server", "csp_url", "dev.picarro.com/node")
            self.ticket_url = self.co.get("Server", "ticket_url", "dev.picarro.com/node/rest/sec/dummy/1.0/Admin")
            self.identity = self.co.get("Server","identity")
            self.psys = self.co.get("Server","sys")
            self.svc = "gdu"
        else:
            self.url = self.co.get("Server", "url", "p3.picarro.com/dev")
            
        self.stopViewServer()
        self.startViewServer()
        
        # Graphical Properties
        for i in range(len(self.concList)):
            opacSel, colorCode = self._convertKML2Color(self.targetConfig.get(self.concList[i], "line_color"))
            self.cselLineColor[i].SetValue(colorCode)
            self.comboBoxLineOpacity[i].SetValue(opacSel)
            opacSel, colorCode = self._convertKML2Color(self.targetConfig.get(self.concList[i], "poly_color"))
            self.cselPolyColor[i].SetValue(colorCode)
            self.comboBoxPolyOpacity[i].SetValue(opacSel)
            self.textCtrlBaseline[i].SetValue(self.targetConfig.get(self.concList[i], "offset"))
            self.textCtrlScaling[i].SetValue(self.targetConfig.get(self.concList[i], "scale"))
            if self.targetConfig.getint(self.concList[i], "enabled"):
                self.comboBoxOnOff[i].SetValue("ON")
                self._switchOnOff(i, True)
            else:
                self.comboBoxOnOff[i].SetValue("OFF")
                self._switchOnOff(i, False)
        
    def bindEvents(self):
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_BUTTON, self.onOKButton, self.buttonApplyTop)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApplyBottom) 
        for c in self.comboBoxOnOff:
            self.Bind(wx.EVT_COMBOBOX, self.onOnOffCombo, c) 

        self.Bind(wx.EVT_COMBOBOX, self.onAnalyzerCtrl, self.analyzerCtrl)
        
    def _convertColor2KML(self, colorTuple, opacity):
        [r,g,b] = [hex(c).upper()[2:].zfill(2) for c in colorTuple]
        return opacity+b+g+r

    def _convertKML2Color(self, KMLColor):
        opacSel = OPACITY_LIST[eval("0x%s" % KMLColor[:2])/64]
        b = eval("0x%s" % KMLColor[2:4])
        g = eval("0x%s" % KMLColor[4:6])
        r = eval("0x%s" % KMLColor[6:8])
        colorCode = (r, g, b) 
        return opacSel, colorCode
        
    def _copyIniFiles(self):
        try:
            shutil.copy2(self.targetIniFile, self.activeIniFile)
        except:
            pass
        try:
            shutil.copy2(self.targetIniFile, self.inactiveIniFile)
        except:
            pass

    def onOKButton(self, event):
        name = self.dataCtrl.GetValue()
        alog = self.alogList[self.nameList.index(name)]
        self.targetConfig.set("SETTINGS", "alog", alog)
        self.targetConfig.write()
        self._copyIniFiles()
        
    def onOnOffCombo(self, event):
        eventObj = event.GetEventObject()
        if eventObj.GetValue() == "ON":
            enabled = True
        else:
            enabled = False
        i = self.comboBoxOnOff.index(eventObj)
        self._switchOnOff(i, enabled)

    def onAnalyzerCtrl(self, event):
        eventObj = event.GetEventObject()
        analyzer = eventObj.GetValue()
        self.getDataList(analyzer)
        self.dataCtrl.Clear()
        for name in self.nameList: 
            self.dataCtrl.Append(name) 

        
    def onClose(self, event):
        self.stopViewServer()
        self.Destroy()
    
    def _switchOnOff(self, i, enabled):
        self.cselLineColor[i].Enable(enabled)
        self.comboBoxLineOpacity[i].Enable(enabled)
        self.cselPolyColor[i].Enable(enabled)
        self.comboBoxPolyOpacity[i].Enable(enabled)
        self.textCtrlBaseline[i].Enable(enabled)
        self.textCtrlScaling[i].Enable(enabled)
        
    def stopViewServer(self):
        currentPid = self.co.getint("Server", "pid")
        if currentPid in getPidList():
            currentProc = psutil.Process(currentPid)
            children = currentProc.get_children()
            for c in children:
                c.kill()
            currentProc.kill()
        self.co.set("Server", "pid", "-1")
        self.co.write()

    def startViewServer(self):
        serverCode = self.co.get("Server", "serverCode", "C:/Picarro/G2000/AnalyzerViewer/viewServer.py")
        launchThread = threading.Thread(target = self._launchServer, args = (serverCode,))
        launchThread.setDaemon(True)
        launchThread.start()

    def _launchServer(self, serverCode):
        if os.path.basename(serverCode).split(".")[-1] == "py":
            if self.secure:
                proc = psutil.Popen(["python.exe", serverCode, "-s",
                                     "--svc=%s" % self.svc, 
                                     "--csp-url=%s" % self.csp_url,
                                     "--ticket-url=%s" % self.ticket_url,
                                     "--identity=%s" % self.identity,
                                     "--sys=%s" % self.psys,
                                     "--config=%s" % self.setupIniFile])
            else:
                proc = psutil.Popen(["python.exe", serverCode, "-u", self.url, "-c", self.setupIniFile])
        else:
            if self.secure:
                proc = psutil.Popen([serverCode, "-s",
                                     "--svc=%s" % self.svc,
                                     "--csp-url=%s" % self.csp_url,
                                     "--ticket-url=%s" % self.ticket_url,
                                     "--identity=%s" % self.identity,
                                     "--sys=%s" % self.psys,
                                     "--config=%s" % self.setupIniFile])
            else:
                proc = psutil.Popen([serverCode, "-u", self.url, "-c", self.setupIniFile])
        self.co.set("Server", "pid", proc.pid)
        self.co.write()
        
    def onApplyButton(self, event):
        # Graphical Properties
        for i in range(len(self.concList)):
            lineColor = self._convertColor2KML(self.cselLineColor[i].GetValue(), OPACITY_DICT[self.comboBoxLineOpacity[i].GetValue()])
            polyColor = self._convertColor2KML(self.cselPolyColor[i].GetValue(), OPACITY_DICT[self.comboBoxPolyOpacity[i].GetValue()])
            scale = float(self.textCtrlScaling[i].GetValue())
            offset = float(self.textCtrlBaseline[i].GetValue())
            if (self.comboBoxOnOff[i].GetValue() == "ON"):
                enabled = "1"
            else:
                enabled = "0"
            self.targetConfig.set(self.concList[i], "line_color", lineColor)
            self.targetConfig.set(self.concList[i], "poly_color", polyColor)
            self.targetConfig.set(self.concList[i], "scale", scale)
            self.targetConfig.set(self.concList[i], "offset", offset)
            self.targetConfig.set(self.concList[i], "enabled", enabled)
        
        if not os.path.isfile(self.activeIniFile):
            self.targetConfig.set("SETTINGS", "restart", "0")
            self.targetConfig.set("SETTINGS", "shutdown", "0")
            
        self.targetConfig.write()
        self._copyIniFiles()
            
        
HELP_STRING = \
"""

RemoteMobileKitSetup.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        
    return configFile
    
if __name__ == "__main__":
    mobileKitApp = SingleInstance("RemoteMobileKitSetup")
    if mobileKitApp.alreadyrunning():
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Mobile Kit Setup")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        configFile= HandleCommandSwitches()
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = RemoteMobileKitSetup(configFile, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()