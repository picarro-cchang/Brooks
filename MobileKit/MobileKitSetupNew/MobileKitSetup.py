#!/usr/bin/python
#
# File Name: MobileKitSetup.py
# Purpose: Setup GUI for Picarro Mobile Kit
#
# File History:
# 2011-09-14 Alex Lee  Created

import sys
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
from MobileKitSetupFrame import MobileKitSetupFrame

DEFAULT_CONFIG_NAME = "MobileKitSetup.ini"
MAX_REST_ERROR_COUNT = 5

OPACITY_DICT = {"25%":"3F", "50%":"7F", "75%":"BF", "100%":"FF"}
OPACITY_LIST = ["25%", "50%", "75%", "100%"]

TIMEOUT = 5.0
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
    
class RestProxy(object):
    # Proxy to make a rest call to a server
    def __init__(self, host):
        self.host = host
    # Attributes are mapped to a function which performs
    #  a GET request to host/rest/attrName
    def __getattr__(self,attrName):
        def dispatch(argsDict):
            url = "rest/%s" % attrName
            #print self.host, "GET","%s?%s" % (url,urllib.urlencode(argsDict))
            conn = httplib.HTTPConnection(self.host)
            try:
                conn.request("GET","%s?%s" % (url,urllib.urlencode(argsDict)))
                r = conn.getresponse()
                if not r.reason == 'OK':
                    raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
                else:
                    return json.loads(r.read()).get("result",{})
            except socket.timeout:
                raise RestCallTimeout(traceback.format_exc())
            finally:
                conn.close()
        return dispatch
   
class MobileKitSetup(MobileKitSetupFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = CustomConfigObj(configFile)
        self.setupIniFile = os.path.abspath(configFile)
        self.activeIniFile = self.co.get("Main", "activeIniPath")
        self.inactiveIniFile = self.co.get("Main", "inactiveIniPath")
        self.targetIniFile = self.inactiveIniFile
        if not os.path.isfile(self.targetIniFile):
            self.targetIniFile = self.activeIniFile
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
        MobileKitSetupFrame.__init__(self, concList, *args, **kwds)

        self.bindEvents()
        self.setInit()
        self.restErrorCount = 0
        
        currentPid = self.co.getint("Server", "pid")
        if currentPid in getPidList():
            ipAddr = self.ipCtrl.GetValue()
            cleanIpAddr = ".".join([a.strip() for a in ipAddr.split(".")])
            self.restService = RestProxy("%s:5000" % (cleanIpAddr,))
        else:
            self.restService = None
        statusThread = threading.Thread(target = self._updateStatus)
        statusThread.setDaemon(True)
        statusThread.start()
        
    def _updateStatus(self):
        while True:
            try:
                varList = ["INST_STATUS","GPS_FIT"]
                varList += self.concList
                result = self.restService.getData({'startPos':-1,'varList':json.dumps(varList)})
                if "error" in result:
                    if self.restErrorCount < MAX_REST_ERROR_COUNT:
                        self.restErrorCount += 1
                else:
                    self.restErrorCount = 0
                    instStatus = int(result["INST_STATUS"][-1])
                    gpsFit = int(result["GPS_FIT"][-1])
                    if instStatus == 963:
                        self.sysAlarmView.setStatus(1, 1)
                    else:
                        self.sysAlarmView.setStatus(1, 0)
                    if gpsFit == 0:
                        self.sysAlarmView.setStatus(2, 0)
                    else:
                        self.sysAlarmView.setStatus(2, 1)
                    for i in range(len(self.concList)):
                        conc = self.concList[i]
                        if conc in result:
                            concValue = float(result[conc][-1])
                        else:
                            concValue = 0.0
                        self.textCtrlConc[i].SetValue("%.3f"%concValue)
            except Exception, err:
                print "%r" % err
                if self.restErrorCount < MAX_REST_ERROR_COUNT:
                    self.restErrorCount += 1
            if self.restErrorCount < MAX_REST_ERROR_COUNT:
                self.sysAlarmView.setStatus(0, 1)
            else:
                for i in range(3):
                    self.sysAlarmView.setStatus(i, 0)
            self.sysAlarmView.refreshList()
            time.sleep(2.0)
            
    def setInit(self):
        currentPid = self.co.getint("Server", "pid")
        if currentPid in getPidList():
            self.ipCtrl.Enable(False)
            self.buttonLaunchServer.SetLabel("Stop Mobile Kit Server")
        elif currentPid != -1:
            self.co.set("Server", "pid", "-1")
            self.co.write()
        self.ipCtrl.SetValue(self.co.get("Server", "ipAddr"))
        
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
        self.Bind(wx.EVT_BUTTON, self.onLaunchButton, self.buttonLaunchServer)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApply) 
        self.Bind(wx.EVT_BUTTON, self.onNewRunButton, self.buttonNewRun) 
        self.Bind(wx.EVT_MENU, self.onShutdownMenu, self.iShutdown) 
        for c in self.comboBoxOnOff:
            self.Bind(wx.EVT_COMBOBOX, self.onOnOffCombo, c) 

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

    def onOnOffCombo(self, event):
        eventObj = event.GetEventObject()
        if eventObj.GetValue() == "ON":
            enabled = True
        else:
            enabled = False
        i = self.comboBoxOnOff.index(eventObj)
        self._switchOnOff(i, enabled)
                
    def _switchOnOff(self, i, enabled):
        self.cselLineColor[i].Enable(enabled)
        self.comboBoxLineOpacity[i].Enable(enabled)
        self.cselPolyColor[i].Enable(enabled)
        self.comboBoxPolyOpacity[i].Enable(enabled)
        self.textCtrlBaseline[i].Enable(enabled)
        self.textCtrlScaling[i].Enable(enabled)
        
    def onLaunchButton(self, event):
        currentPid = self.co.getint("Server", "pid")
        if self.buttonLaunchServer.GetLabel() == "Stop Mobile Kit Server":
            if currentPid in getPidList():
                d = wx.MessageDialog(self, "Mobile Kit Server is currently running. Are you sure you want to stop it?", "Stop Mobile Kit Server", wx.ICON_EXCLAMATION|wx.YES_NO|wx.NO_DEFAULT|wx.STAY_ON_TOP)
                if d.ShowModal() != wx.ID_YES:
                    return
                currentProc = psutil.Process(currentPid)
                children = currentProc.get_children()
                for c in children:
                    c.kill()
                currentProc.kill()
            self.co.set("Server", "pid", "-1")
            self.buttonLaunchServer.SetLabel("Launch Mobile Kit Server")
            self.ipCtrl.Enable(True)
        else:
            ipAddr = self.ipCtrl.GetValue()
            serverCode = self.co.get("Server", "serverCode", "C:/Picarro/G2000/AnalyzerViewer/viewServer.py")
            cleanIpAddr = ".".join([a.strip() for a in ipAddr.split(".")])
            print cleanIpAddr
            self.onApplyButton(None)
            
            launchThread = threading.Thread(target = self._launchServer, args = (ipAddr, serverCode, cleanIpAddr))
            launchThread.setDaemon(True)
            launchThread.start()
            
            self.buttonLaunchServer.SetLabel("Stop Mobile Kit Server")
            self.ipCtrl.Enable(False)
            # Establish a new connection
            self.restService = RestProxy("%s:5000" % (cleanIpAddr,))
        self.co.write()
           
    def _launchServer(self, ipAddr, serverCode, cleanIpAddr):
        self.co.set("Server", "ipAddr", ipAddr)
        if os.path.basename(serverCode).split(".")[-1] == "py":
            proc = psutil.Popen(["python.exe", serverCode, "-a", cleanIpAddr, "-c", self.setupIniFile])
        else:
            proc = psutil.Popen([serverCode, "-a", cleanIpAddr, "-c", self.setupIniFile])
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
            
    def onNewRunButton(self, event):
        self.targetConfig.set("SETTINGS", "restart", "1")
        self.targetConfig.write()
        self._copyIniFiles()
            
    def onShutdownMenu(self, event):
        d = wx.MessageDialog(None, "Are you sure you want to shut down the analyzer?\nIt could take up to 30 minutes to restart the analyzer after shutting down.\n\nSelect \"Yes\" to continue.\nSelect \"No\" to cancel this action.",\
                        "Shut Down Analyzer Confirmation", wx.YES_NO|wx.ICON_EXCLAMATION)
        if d.ShowModal() != wx.ID_YES:
            d.Destroy()
            return
        else:
            d.Destroy()
        self.targetConfig.set("SETTINGS", "shutdown", "1")
        self.targetConfig.write()
        self._copyIniFiles()
        
HELP_STRING = \
"""

MobileKitSetup.py [-h] [-c <FILENAME>]

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
    mobileKitApp = SingleInstance("MobileKitSetup")
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
        frame = MobileKitSetup(configFile, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()