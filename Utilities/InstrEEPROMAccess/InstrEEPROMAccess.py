"""
File name: InstrEEPROMAccess.py
Purpose: Provides an access to read/write instrument information on EEPROM

File History:
    2010-08-30 Alex  Created
"""

import wx
import sys
import os
import time
import win32gui
from Host.Common import CmdFIFO
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SingleInstance import SingleInstance
from Host.Common.SharedTypes import RPC_PORT_DRIVER

DEFAULT_TYPES = ["AADS", "ADDS", "AEDS", "AFDS", "BADS", "CADS", "CBDS", "CCADS", "CDDS", "CEDS", "CFADS", "CFBDS","CFDDS", "CFEDS", "CFKADS", "CFKBDS", "CHADS", "CKADS", "HBDS"]
# Connect to database
from xmlrpclib import ServerProxy
DB = ServerProxy("http://mfg/xmlrpc/",allow_none=True)

CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "InstrEEPROMAccess")
                  
class InstrEEPROMAccessFrame(wx.Frame):
    def __init__(self, configFile, defaultChassis, *args, **kwds):
        try:
            co = CustomConfigObj(configFile, list_values = True)
            analyzerTypes = co.get("Main", "AnalyzerTypes")
        except:
            analyzerTypes = DEFAULT_TYPES
        try:
            signaturePath = co.get("Main", "SignaturePath", "C:/Picarro/G2000/installerSignature.txt")
        except:
            signaturePath = "C:/Picarro/G2000/installerSignature.txt"
        try:
            sigFd = open(signaturePath, "r")
            self.installerId = sigFd.readline()
            sigFd.close()
        except:
            self.installerId = None
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Instrument EEPROM Access")
        self.labelFooter = wx.StaticText(self.panel3, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.panel3.SetBackgroundColour("#85B24A")
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iHelp = wx.Menu()

        self.frameMenubar.Append(self.iHelp,"Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "About Instrument EEPROM Access", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)
        
        # Read EEPROM information section
        self.labelCurEEPROM = wx.StaticText(self.panel1, -1, "Current Instrument Information in EEPROM", style = wx.ALIGN_CENTER)
        self.labelCurEEPROM.SetFont(wx.Font(10, wx.DEFAULT, style = wx.NORMAL,weight = wx.BOLD))
        try:
            curValDict = CRDS_Driver.fetchLogicEEPROM()[0]
        except Exception, err:
            print err
            curValDict = {"Chassis":"NONE","Analyzer":"NONE","AnalyzerNum":"NONE"}
        self.chassisNum = curValDict["Chassis"]
        self.analyzerType = curValDict["Analyzer"]
        self.analyzerNum = curValDict["AnalyzerNum"]
        
        self.labelCurChassis = wx.StaticText(self.panel1, -1, "Chassis Number", size = (100,-1))
        self.valCurChassis = wx.TextCtrl(self.panel1, -1, self.chassisNum, size = (250, -1), style = wx.TE_READONLY)
        self.valCurChassis.SetBackgroundColour("#FFFF99")
        
        self.labelCurType= wx.StaticText(self.panel1, -1, "Analzyer Type", size = (100,-1))
        self.valCurType = wx.TextCtrl(self.panel1, -1, self.analyzerType, size = (250, -1), style = wx.TE_READONLY)
        self.valCurType.SetBackgroundColour("#FFFF99")
        
        self.labelCurAnalyzer = wx.StaticText(self.panel1, -1, "Analyzer Number", size = (100,-1))
        self.valCurAnalyzer = wx.TextCtrl(self.panel1, -1, self.analyzerNum, size = (250, -1), style = wx.TE_READONLY)
        self.valCurAnalyzer.SetBackgroundColour("#FFFF99")

        # Write EEPROM information section
        self.labelNewEEPROM = wx.StaticText(self.panel2, -1, "Write Instrument Information to EEPROM", style = wx.ALIGN_CENTER)
        self.labelNewEEPROM.SetFont(wx.Font(10, wx.DEFAULT, style = wx.NORMAL,weight = wx.BOLD))
        self.labelNewChassis = wx.StaticText(self.panel2, -1, "Chassis Number", size = (100,-1))
        if defaultChassis == None:
            try:
                chassisChoices = [elem['identifier'].split("CHAS2K")[1] for elem in DB.get_values("chassis2k",dict(status__in = ["I","U"]))]
                chassisChoices.sort()
            except:
                chassisChoices = []
        else:
            chassisChoices = [defaultChassis]
        if self.chassisNum != "NONE":
            if self.chassisNum not in chassisChoices:
                chassisChoices.insert(0, self.chassisNum)
            self.comboBoxChassis = wx.ComboBox(self.panel2, -1, choices = chassisChoices, value = self.chassisNum, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        else:
            self.comboBoxChassis = wx.ComboBox(self.panel2, -1, choices = chassisChoices, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        self.labelNewType = wx.StaticText(self.panel2, -1, "Analyzer Type", size = (100,-1))
        typeChoices = analyzerTypes
        typeChoices.sort()
        if self.analyzerType != "NONE":
            if self.analyzerType not in typeChoices:
                typeChoices.insert(0, self.analyzerType)
            self.comboBoxType = wx.ComboBox(self.panel2, -1, choices = typeChoices, value = self.analyzerType, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        else:
            self.comboBoxType = wx.ComboBox(self.panel2, -1, choices = typeChoices, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        self.labelNewAnalyzer = wx.StaticText(self.panel2, -1, "Analyzer Number", size = (100,-1))
        if self.analyzerNum != "NONE":
            self.textCtrlNewAnalyzer = wx.TextCtrl(self.panel2, -1, self.analyzerNum, size = (250, -1), style = wx.TE_PROCESS_ENTER)
        else:
            self.textCtrlNewAnalyzer = wx.TextCtrl(self.panel2, -1, "", size = (250, -1), style = wx.TE_PROCESS_ENTER)
            
        self.updateButton = wx.Button(self.panel3, -1, "Update EEPROM", size = (130, -1))
        self.updateButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.closeButton = wx.Button(self.panel3, wx.ID_CLOSE, "Close", size = (130, -1))
        self.closeButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        sizer_1.Add(self.labelCurEEPROM, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 10)
        grid_sizer_1 = wx.FlexGridSizer(-1, 2)
        grid_sizer_1.Add(self.labelCurChassis, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.valCurChassis, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.labelCurType, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.valCurType, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.labelCurAnalyzer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.valCurAnalyzer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1,10))
        self.panel1.SetSizer(sizer_1)
        
        sizer_2.Add(self.labelNewEEPROM, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 10)
        grid_sizer_2 = wx.FlexGridSizer(-1, 2)
        grid_sizer_2.Add(self.labelNewChassis, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_2.Add(self.comboBoxChassis, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_2.Add(self.labelNewType, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_2.Add(self.comboBoxType, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_2.Add(self.labelNewAnalyzer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_2.Add(self.textCtrlNewAnalyzer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_2.Add(grid_sizer_2, 0)
        sizer_2.Add((-1,10))
        self.panel2.SetSizer(sizer_2)

        sizer_3.Add((55,-1))
        sizer_3.Add(self.updateButton, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 10)
        sizer_3.Add((25,-1))
        sizer_3.Add(self.closeButton, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 10)
        sizer_4.Add(sizer_3, 0, wx.EXPAND|wx.BOTTOM, 5)
        sizer_4.Add(self.labelFooter, 0, wx.EXPAND|wx.BOTTOM, 5)
        self.panel3.SetSizer(sizer_4)

        sizer_5.Add(self.panel1, 0, wx.EXPAND, 0)
        sizer_5.Add(self.panel2, 0, wx.EXPAND, 0)
        sizer_5.Add(self.panel3, 0, wx.EXPAND, 0)
        
        self.SetSizer(sizer_5)
        sizer_5.Fit(self)
        self.Layout()

class InstrEEPROMAccess(InstrEEPROMAccessFrame):
    def __init__(self, defaultChassis, *args, **kwds):
        InstrEEPROMAccessFrame.__init__(self, defaultChassis, *args, **kwds)
        self.bindEvents()
 
    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.closeButton)
        self.Bind(wx.EVT_BUTTON, self.onUpdateButton, self.updateButton)
        
    def onAboutMenu(self, event):
        d = wx.MessageDialog(None, "Picarro tool to read/write instrument information in EEPROM\n\nCopyright 1999-2010 Picarro Inc. All rights reserved.\nVersion: 0.01\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.", "About Instrument EEPROM Access", wx.OK)
        d.ShowModal()
        d.Destroy()
        
    def onCloseButton(self, event):
        sys.exit(0)
        self.Destroy()
        
    def onUpdateButton(self, event):
        chassisNum = self.comboBoxChassis.GetValue()
        analyzerType = self.comboBoxType.GetValue()
        analyzerNum = self.textCtrlNewAnalyzer.GetValue()
        if (self.installerId != None) and (analyzerType != self.installerId):
            d = wx.MessageDialog(None, "New Analyzer Type (%s) does not match Software Installer ID (%s)\nDo you want to continue?"%\
                (analyzerType,self.installerId), "Mismatching Analyzer Type", wx.YES_NO|wx.ICON_ERROR)
            if d.ShowModal() != wx.ID_YES:
                d.Destroy()
                return
            else:
                d.Destroy()
            
        if len(analyzerNum) != 4:
            d = wx.MessageDialog(None, "Invalid Analyzer Number: %s\nMust be a 4-digit integer." % analyzerNum, "Error", wx.OK|wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
            return
            
        d = wx.MessageDialog(None, "New Chassis Number = %s\nNew Analyzer Type = %s\nNew Analyzer Number = %s\n\nAre you sure you want to change?"%\
            (chassisNum,analyzerType,analyzerNum), "Write EEPROM Confirmation", wx.YES_NO|wx.ICON_EXCLAMATION)
        if d.ShowModal() != wx.ID_YES:
            d.Destroy()
            return
        else:
            d.Destroy()
        try:
            CRDS_Driver.shelveObject("LOGIC_EEPROM",{'Chassis':chassisNum,'Analyzer':analyzerType,'AnalyzerNum':analyzerNum},0)
        except:
            return
        time.sleep(1.0)
        try:
            curValDict = CRDS_Driver.fetchLogicEEPROM()[0]
        except:
            curValDict = {"Chassis":"NONE","Analyzer":"NONE","AnalyzerNum":"NONE"}
        self.chassisNum = curValDict["Chassis"]
        self.analyzerType = curValDict["Analyzer"]
        self.analyzerNum = curValDict["AnalyzerNum"]
        self.valCurChassis.SetValue(self.chassisNum)
        self.valCurType.SetValue(self.analyzerType)
        self.valCurAnalyzer.SetValue(self.analyzerNum)

def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "c:d:", [])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    else:
        configFile = None
        
    if "-d" in options:
        defaultChassis = options["-d"]
        print "Default Chassis: %s" % defaultChassis
    else:
        defaultChassis = None
        
    return configFile, defaultChassis
    
if __name__ == "__main__":
    configFile, defaultChassis = HandleCommandSwitches()
    eepromAccessApp = SingleInstance("InstrEEPROMAccess")
    if eepromAccessApp.alreadyrunning():
        try:
            handle = win32gui.FindWindowEx(0, 0, None, "Instrument EEPROM Access")
            win32gui.SetForegroundWindow(handle)
        except:
            pass
    else:
        app = wx.PySimpleApp()
        wx.InitAllImageHandlers()
        frame = InstrEEPROMAccess(configFile, defaultChassis, None, -1, "")
        app.SetTopWindow(frame)
        frame.Show()
        app.MainLoop()