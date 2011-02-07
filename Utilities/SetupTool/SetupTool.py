#!/usr/bin/python
"""
File Name: SetupTool.py
Purpose: Tool to set up Picarro analyzer

File History:
2010-09-27 alex  Created
"""

import sys
import os
import stat
import wx
import getopt
import time
from numpy import *
from matplotlib import pyplot
from matplotlib.artist import *
from SetupToolFrame import SetupToolFrame
from SetupToolPages import printError
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR, RPC_PORT_QUICK_GUI, RPC_PORT_DRIVER

APP_NAME = "SetupTool"

CRDS_QuickGui = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_QUICK_GUI,
                                            APP_NAME,
                                            IsDontCareConnection = False)

CRDS_Supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                         APP_NAME,
                                         IsDontCareConnection = False)
                                         
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                         APP_NAME,
                                         IsDontCareConnection = False)
                                            
TRANSLATE_TABLE = {"dataLogger": "Data Logger", "archiver": "Archiver", "valveSequencer": "Valve Sequencer MPV", 
                   "commandInterface": "Command Interface", "dataManager": "Data Streaming", "coordinator": "Coordinator"}

class SetupTool(SetupToolFrame):
    def __init__(self, setupToolIni, *args, **kwds):       
        self.setupCp = CustomConfigObj(setupToolIni, list_values = True)
        self.appConfigPath = self.setupCp.get("Setup", "appConfigPath")
        try:
            self.clCp =  CustomConfigObj(os.path.join(self.appConfigPath, "Utilities\%s" % self.setupCp.get("Setup", "coordinatorLauncher")))
        except:
            self.clCp = None
        archiverDir = os.path.join(self.appConfigPath, "Archiver")
        dataLoggerDir = os.path.join(self.appConfigPath, "DataLogger")
        dataMgrDir = os.path.join(self.appConfigPath, "DataManager")
        cmdDir = os.path.join(self.appConfigPath, "CommandInterface")
        valveDir = os.path.join(self.appConfigPath, "ValveSequencer")
        remoteAccessDir = os.path.join(self.appConfigPath, "Utilities")
        quickGuiDir = os.path.join(self.appConfigPath, "QuickGui")
        coordinatorDir = os.path.join(self.appConfigPath, "Coordinator")
        
        self.pageAppDict = {0: ["dataLogger", "archiver"], 1: ["dataManager", "valveSequencer", "commandInterface", "coordinator"],
                            2: ["remoteAccess"], 3:["quickGui"], 4:["commandInterface"], 5:["dataManager"]}
        self.appIniDirDict = {"archiver": archiverDir, "dataLogger": dataLoggerDir, "dataManager": dataMgrDir,
                              "valveSequencer": valveDir, "commandInterface": cmdDir,
                              "remoteAccess": remoteAccessDir, "quickGui": quickGuiDir,
                              "coordinator": coordinatorDir}

        comPortList = self.setupCp.get("Setup", "comPortList")
        self._getCoordinatorPathAndPortList()
        self.dataColsFile = self.setupCp.get("Setup", "dataColsFile")
        self.modeList = self.setupCp.list_sections()
        self.modeList.remove("Setup")
        SetupToolFrame.__init__(self, comPortList, CRDS_QuickGui, CRDS_Driver, *args, **kwds)
        self.onModeComboBox(None)
        self.bindEvents()
        self.fullInterface = False

    def _getCoordinatorPathAndPortList(self):
        self.coordinatorPortList = []
        self.coordinatorPathList = []
        if self.clCp == None:
            return
        for coorOpt in [i for i in self.clCp.list_sections() if i != "Main"]:
            coordintaorFile = self.clCp.get(coorOpt, "CoordinatorIni")
            if not os.path.isfile(coordintaorFile):
                coorPath = os.path.join(self.appIniDirDict["coordinator"], coordintaorFile)
            else:
                coorPath = coordintaorFile
            cp = CustomConfigObj(coorPath, list_values = True)
            try:
                for port in cp["SerialPorts"].keys():
                    if port not in self.coordinatorPortList:
                        self.coordinatorPortList.append(port)
                if coorPath not in self.coordinatorPathList:
                    self.coordinatorPathList.append(coorPath)
            except:
                continue
                        
    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_MENU, self.onInterfaceMenu, self.iInterface)
        self.Bind(wx.EVT_COMBOBOX, self.onModeComboBox, self.comboBoxMode)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApply)    
        self.Bind(wx.EVT_BUTTON, self.onExitButton, self.buttonExit)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def onAboutMenu(self, event):
        d = wx.MessageDialog(None, "Software tool to customize Picarro G2000 analyzer\n\nCopyright 1999-2011 Picarro Inc. All rights reserved.\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.", "About Setup Tool", wx.OK)
        d.ShowModal()
        d.Destroy()
        
    def onInterfaceMenu(self, event):
        if not self.fullInterface:
            d = wx.TextEntryDialog(self, 'Service Mode Password: ','Authorization required', '', wx.STAY_ON_TOP|wx.OK|wx.CANCEL|wx.TE_PASSWORD)
            password = "picarro"
            okClicked = d.ShowModal() == wx.ID_OK
            d.Destroy()
            if not okClicked:
                return
            elif d.GetValue() != password:
                printError("Password incorrect.", "Incorrect Password", "Access denied.")
                return
            self.fullInterface = True
        else:
            self.fullInterface = False
        self.updateInterface()

    def updateInterface(self):
        """ Update the GUI based on self.fullInterface."""
        if self.fullInterface:
            self.iSettings.SetLabel(self.idInterface, "Switch to User Mode")
            for pageObj in self.pages:
                pageObj.setFullInterface(True)
        else:
            self.iSettings.SetLabel(self.idInterface, "Switch to Service Mode")
            for pageObj in self.pages:
                pageObj.setFullInterface(False)
            
    def onApplyButton(self, event):
        try:
            if CRDS_Supervisor.CmdFIFO.PingFIFO() == "Ping OK":
                analyzerRunning = True
            else:
                analyzerRunning = False
        except:
            analyzerRunning = False
        if analyzerRunning and not self.fullInterface:
            printError("Analyzer software is currently running.\nPlease stop analyzer software and try to apply configuration changes again.", "Error", "Unapplied changes will be lost if exiting Setup Tool now." )
            return
                
        page = self.nb.GetSelection()
        response = self.pages[page].apply()
        if response:
            d = wx.MessageDialog(None, "Changes on \"%s\" page were successfully applied.   " % self.nb.GetPageText(page), "Changes Applied", wx.STAY_ON_TOP|wx.OK|wx.ICON_INFORMATION)
            d.ShowModal()
            d.Destroy()
        else:
            printError("Failed to apply changes on \"%s\" page." % self.nb.GetPageText(page), "Error", "")
            
        response = self.pages[page].showCurValues()
        if not response:
            printError("Failed to show current configurations on \"%s\" page." % self.nb.GetPageText(page), "Error", "")
            
    def onModeComboBox(self, event):
        if event:
            eventObj = event.GetEventObject()
        else:
            eventObj = self.comboBoxMode
        self.mode = eventObj.GetValue()
        self.SetTitle("Picarro Analyzer Setup Tool (%s)" % self.mode)
        self.setIni()
        for page in range(len(self.pages)):
            response = self.pages[page].showCurValues()
            if not response:
                printError("Failed to show current configurations on \"%s\" page." % self.nb.GetPageText(page), "Error", "")
 
    def setIni(self):
        for page in range(len(self.pages)):
            pageObj = self.pages[page]
            appList = self.pageAppDict[page]
            
            iniList = []
            for app in appList:
                if app != "coordinator":
                    iniName = self.setupCp[self.mode][app]
                    iniPath = self.getIniPath(app, iniName)
                else:
                    iniPath = self.getIniPath(app, None)
                iniList.append(iniPath)
            if page == 0:
                # Add data cols file for data logger page
                iniList.append(self.dataColsFile)
            pageObj.setIni(iniList)
            
            comment = ""
            for app in appList:
                iniName = self.setupCp[self.mode][app]
                if iniName in self.modeList:
                    # Configurations depend on other modes
                    if page == 0:
                        if app == "dataLogger":
                            pageObj.enable([0,1,2], False)
                        else:
                            pageObj.enable([3,4], False)
                        comment += "* %s controlled by %s Mode\n" % (TRANSLATE_TABLE[app], iniName)
                    elif page == 1:
                        if app != "coordinator":
                            pageObj.enable([appList.index(app)], False)
                        else:
                            pageObj.enable(range(3, 3+len(self.coordinatorPortList)), False)
                        comment += "* %s controlled by %s Mode\n" % (TRANSLATE_TABLE[app], iniName)
                    else:
                        pageObj.enable(False)
                        comment = "* Controlled by %s Mode" % iniName
                else:
                    if page == 0:
                        if app == "dataLogger":
                            pageObj.enable([0,1,2], True)
                        else:
                            pageObj.enable([3,4], True)
                    elif page == 1:
                        if app != "coordinator":
                            pageObj.enable([appList.index(app)], True)
                        else:
                            pageObj.enable(range(3, 3+len(self.coordinatorPortList)), True)
                    else:
                        pageObj.enable(True)
            pageObj.setComment(comment)
            
    def getIniPath(self, app, iniName):
        if app == "coordinator":
            return self.coordinatorPathList
        if iniName in self.modeList:
            if self.setupCp[iniName][app] in self.modeList:
                raise Exception, "Invalid configuration specified"
            iniPath = self.getIniPath(app, self.setupCp[iniName][app])
        else:
            if type(iniName) != type([]):
                iniPath = os.path.join(self.appIniDirDict[app], iniName)
            else:
                iniPath = []
                for ini in iniName:
                    iniPath.append(os.path.join(self.appIniDirDict[app], ini))
        return iniPath
                    
    def onExitButton(self, event):
        self.Destroy()
        
    def onClose(self, event):
        sys.exit()
        
        
HELP_STRING = \
"""\
SetupTool [-h] [-c <SetupTool.ini path>]

Where the options can be a combination of the following:
-h                  Print this help.
-c                  Specify the path of SetupTool.ini.
"""
def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'c:h'
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    #Start with option defaults...
    setupToolIni = ".\SetupTool.ini"
    if "-c" in options:
        setupToolIni = options["-c"]
    
    if not os.path.isfile(setupToolIni):
        app = wx.App()
        app.MainLoop()
        dlg = wx.FileDialog(None, "Select SetupTool.ini",
                            os.getcwd(), wildcard = "*.ini", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            setupToolIni = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            
    if not os.path.isfile(setupToolIni):
        print "\nERROR: Valid SetupTool.ini path must be specified!\n"
        print HELP_STRING
        sys.exit(0)
    else:
        print "SetupTool.ini specified: %s" % setupToolIni
        return setupToolIni
        
if __name__ == "__main__":
    setupToolIni = handleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = SetupTool(setupToolIni, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
