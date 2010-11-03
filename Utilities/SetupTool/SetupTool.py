#!/usr/bin/python
#
# File Name: SetupTool.py
# Purpose: Tool to set up Picarro analyzer
#
# File History:
# 2010-09-27 alex  Created

import sys
import os
import stat
import wx
import getopt
import time
from numpy import *
from matplotlib import pyplot
from matplotlib.artist import *
from CustomConfigObj import CustomConfigObj
from SetupToolFrame import SetupToolFrame

TRANSLATE_TABLE = {"valveSequencer": "Valve Sequencer MPV", "commandInterface": "Command Interface", 
                   "dataManager": "Data Streaming", "coordinator": "Coordinator"}

class SetupTool(SetupToolFrame):
    def __init__(self, setupToolIni, *args, **kwds):       
        self.setupCP = CustomConfigObj(setupToolIni, list_values = True)
        self.appConfigPath = self.setupCP.get("Setup", "appConfigPath")
        
        dataLoggerDir = os.path.join(self.appConfigPath, "DataLogger")
        dataMgrDir = os.path.join(self.appConfigPath, "DataManager")
        cmdDir = os.path.join(self.appConfigPath, "CommandInterface")
        valveDir = os.path.join(self.appConfigPath, "ValveSequencer")
        remoteAccessDir = os.path.join(self.appConfigPath, "Utilities")
        quickGuiDir = os.path.join(self.appConfigPath, "QuickGui")
        coordinatorDir = os.path.join(self.appConfigPath, "Coordinator")
        
        self.pageAppDict = {0: ["dataLogger"], 1: ["dataManager", "valveSequencer", "commandInterface", "coordinator"],
                            2: ["remoteAccess"], 3:["quickGui"]}
        self.appIniDirDict = {"dataLogger": dataLoggerDir, "dataManager": dataMgrDir,
                              "valveSequencer": valveDir, "commandInterface": cmdDir,
                              "remoteAccess": remoteAccessDir, "quickGui": quickGuiDir,
                              "coordinator": coordinatorDir}

        comPortList = self.setupCP.get("Setup", "comPortList")
        self.coordinatorPortList = self.setupCP.get("Setup", "coordinatorPortList")
        self.modeList = self.setupCP.list_sections()
        self.modeList.remove("Setup")
        SetupToolFrame.__init__(self, comPortList, *args, **kwds)

        self.onModeComboBox(None)

        self.bindEvents()

    def bindEvents(self):
        self.Bind(wx.EVT_COMBOBOX, self.onModeComboBox, self.comboBoxMode)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApply)    
        self.Bind(wx.EVT_BUTTON, self.onExitButton, self.buttonExit)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def onApplyButton(self, event):
        page = self.nb.GetSelection()
        self.pages[page].apply()
            
    def onModeComboBox(self, event):
        if event:
            eventObj = event.GetEventObject()
        else:
            eventObj = self.comboBoxMode
        self.mode = eventObj.GetValue()
        self.SetTitle("Picarro Analyzer Setup Options (%s)" % self.mode)
        self.setIni()
        for page in range(len(self.pages)):
            self.pages[page].showCurValues()
 
    def setIni(self):
        for page in range(len(self.pages)):
            iniList = []
            for app in self.pageAppDict[page]:
                iniName = self.setupCP[self.mode][app]
                iniPath = self.getIniPath(app, iniName)
                iniList.append(iniPath)
            self.pages[page].setIni(iniList)
            
            comment = ""
            for app in self.pageAppDict[page]:
                iniName = self.setupCP[self.mode][app]
                if iniName in self.modeList:
                    if page == 1:
                        if app != "coordinator":
                            self.pages[page].enable(self.pageAppDict[page].index(app), False)
                        else:
                            for i in range(len(self.coordinatorPortList)):
                                self.pages[page].enable(3+i, False)
                        comment += "* %s controlled by %s Mode\n" % (TRANSLATE_TABLE[app], iniName)
                    else:
                        self.pages[page].enable(False)
                        comment = "* Controlled by %s Mode" % iniName
                else:
                    if page == 1:
                        if app != "coordinator":
                            self.pages[page].enable(self.pageAppDict[page].index(app), True)
                        else:
                            for i in range(len(self.coordinatorPortList)):
                                self.pages[page].enable(3+i, True)
                    else:
                        self.pages[page].enable(True)
            self.pages[page].setComment(comment)
            
    def getIniPath(self, app, iniName):
        if iniName in self.modeList:
            if self.setupCP[iniName][app] in self.modeList:
                raise Exception, "Invalid configuration specified"
            iniPath = self.getIniPath(app, self.setupCP[iniName][app])
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
