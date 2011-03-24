"""
File name: IntegrationTool.py
Purpose: Software tool used for Integration Station and Instrument Performance Verification

File History:
    2010-04-12 Alex  Created
"""

import wx
import sys
import os
import shutil
import time
import subprocess
from configobj import ConfigObj
from xmlrpclib import ServerProxy
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER

FreqConverter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                "IntegrationTool", IsDontCareConnection = False)
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, "IntegrationTool")

ANALY_INFO_LIST = ["Name", "Warm Box", "WLM", "Laser(s)", "Hot Box", "Cavity"]
TEST_LIST = ["Write Instrument Name", "Make Integration INI Files", "Calibrate WB Laser/WLM", 
             "Update Laser/WLM EEPROM", "Create WB Cal Table", "Run Calibrate System", 
             "Calculate WLM Offset", "Run Threshold Stats", "Run Flow Control", "Write Software Version"]
HOSTEXE_DIR = "C:\Picarro\G2000\HostExe"
INTEGRATION_DIR = "C:\Picarro\G2000\InstrConfig\Integration"
CAL_DIR = "C:\Picarro\G2000\InstrConfig\Calibration\InstrCal"
WARMBOX_CAL = "Beta2000_WarmBoxCal"
HOTBOX_CAL = "Beta2000_HotBoxCal"

LASER_TYPE_DICT = {"1603.2": "CO2", "1651.0": "CH4", "1599.6": "iCO2", "1392.0": "iH2O", 
                   "1567.9": "CO", "1527.0": "NH3", "1554.7": "iH2O", "1521.1": "C2H2",
                   "1658.7": "CH4"}

ANALYZER_TYPE_INDEX = {"HBDS":0, "CFADS":1, "CFBDS":1, "CFDDS":1, "CFEDS":1, "CFFDS":6, "CBDS":2, "CHADS":2, "CFKADS":3, "CFKBDS":3, "AEDS":4, "CKADS":5}
ALL_SCHEMES = [
              { "O18"      : r"C:\Picarro\G2000\InstrConfig\Schemes\HBDSxx_Fixed_Peak18O.sch",
                "Baseline" : r"C:\Picarro\G2000\InstrConfig\Schemes\HBDSxx_Baseline.sch",
                "O16"      : r"C:\Picarro\G2000\InstrConfig\Schemes\HBDSxx_Fixed_Peak16O.sch",
                "dH"       : r"C:\Picarro\G2000\InstrConfig\Schemes\HBDSxx_Fixed_PeakD.sch"
              },
              { "CO2_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CO2_BL.sch",
                "CH4_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CH4_BL.sch", 
                "CO2_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CO2_PK.sch",
                "CH4_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CH4_PK.sch"
              },
              { "Baseline": r"C:\Picarro\G2000\InstrConfig\Schemes\CBDSxx_Baseline.sch",
                "C12Peak":  r"C:\Picarro\G2000\InstrConfig\Schemes\CBDSxx_C12Peak.sch",
                "C13Peak":  r"C:\Picarro\G2000\InstrConfig\Schemes\CBDSxx_C13Peak.sch"
              },
              { "CO2_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CO2_BL.sch",
                "CH4_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CH4_BL.sch", 
                "CO_BL"    : r"C:\Picarro\G2000\InstrConfig\Schemes\CO_BL.sch",
                "CO2_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CO2_PK.sch",
                "CH4_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CH4_PK.sch", 
                "CO_PK"    : r"C:\Picarro\G2000\InstrConfig\Schemes\CO_PK.sch"
              },
              {
                "NH3_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\NH3_BL.sch",
                "NH3_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\NH3_PK.sch"
              },
              { "CO2_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CO2_BL.sch",
                "CO_BL"    : r"C:\Picarro\G2000\InstrConfig\Schemes\CO_BL.sch", 
                "CO2_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CO2_PK.sch",
                "CO_PK"    : r"C:\Picarro\G2000\InstrConfig\Schemes\CO_PK.sch"
              },
              { "CH4_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CH4_BL.sch", 
                "CH4_PK"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CH4_PK.sch", 
                "CO2_BL"   : r"C:\Picarro\G2000\InstrConfig\Schemes\CBDSxx_Baseline.sch",
                "C12Peak"  : r"C:\Picarro\G2000\InstrConfig\Schemes\CBDSxx_C12Peak.sch",
                "C13Peak"  : r"C:\Picarro\G2000\InstrConfig\Schemes\CBDSxx_C13Peak.sch"
              },
             ]
             
THRESHOLD_RANGE = [
                   [2000, 20000, 500],
                   [2000, 16383, 1000],
                   [2000, 16000, 500],
                   [2000, 16383, 1000],
                   [2000, 16000, 500],
                   [2000, 16383, 1000],
                   [2000, 16000, 500],
                  ]
                  
# Connect to database
try:
    DB = ServerProxy("http://mfg/xmlrpc/",allow_none=True)
    DB.system.listMethods()
except:
    DB = None

class IntegrationToolFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        #kwds["style"] = wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Picarro Integration Tool")
        self.labelFooter = wx.StaticText(self.panel3, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.panel3.SetBackgroundColour("#85B24A")
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iHelp = wx.Menu()

        self.frameMenubar.Append(self.iHelp,"Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "About Picarro Integration Tool", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)
        
        # Analyzer information section
        self.labelAnalyzer = wx.StaticText(self.panel1, -1, "Analyzer Information", style = wx.ALIGN_CENTER)
        self.labelAnalyzer.SetFont(wx.Font(10, wx.DEFAULT, style = wx.NORMAL,weight = wx.BOLD))
        analyzerChassis = None
        try:
            analyzerChassis = "CHAS2K"+Driver.fetchObject("LOGIC_EEPROM")[0]["Chassis"]
        except:
            pass
            
        try:
            #analyzerChoices = [elem['identifier'] for elem in DB.get_values("Analyzer",dict(status="I"))]
            analyzerChoices = [elem['identifier'] for elem in DB.get_values("chassis2k",dict(status__in = ["I","U"]))]
            analyzerChoices.sort()
            self.comboBoxSelect = wx.ComboBox(self.panel1, -1, choices = analyzerChoices, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
            if analyzerChassis:
                self.comboBoxSelect.SetValue(analyzerChassis)
        except:
            if analyzerChassis:
                analyzerChoices = [analyzerChassis]
                self.comboBoxSelect = wx.ComboBox(self.panel1, -1, choices = analyzerChoices, value = analyzerChassis, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
                #self.comboBoxSelect = wx.ComboBox(self.panel1, -1, value = analyzerChoices[0], choices = analyzerChoices, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
            else:
                raise Exception, "Failed to connect to manufacturing database or read instrument ID from EEPROM"
        self.labelSelect = wx.TextCtrl(self.panel1, -1, "Analyzer", size = (80,-1), style = wx.TE_READONLY|wx.NO_BORDER)
        self.labelSelect.SetBackgroundColour("#E0FFFF")

        self.labelAnalyzerInfoList = []
        self.textCtrlAnalyzerInfoList = []
        for i in range(len(ANALY_INFO_LIST)):
            newLabel = wx.TextCtrl(self.panel1, -1, ANALY_INFO_LIST[i], size = (80,-1), style = wx.TE_READONLY|wx.NO_BORDER)
            newLabel.SetBackgroundColour("#E0FFFF")
            self.labelAnalyzerInfoList.append(newLabel)
            self.textCtrlAnalyzerInfoList.append(wx.TextCtrl(self.panel1, -1, "", size = (250, -1), style = wx.TE_READONLY))

        # Integration test section
        self.labelTest = wx.StaticText(self.panel2, -1, "Integration Test", style = wx.ALIGN_CENTER)
        self.labelTest.SetFont(wx.Font(10, wx.DEFAULT, style = wx.NORMAL,weight = wx.BOLD))

        self.textCtrlIntegration = wx.TextCtrl(self.panel2, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrlIntegration.SetMinSize((350, 150))        
        
        self.testButtonList = []
        for i in range(len(TEST_LIST)):
            newButton = wx.Button(self.panel2, -1, TEST_LIST[i], size = (350, -1))
            newButton.SetBackgroundColour(wx.Colour(237, 228, 199))
            newButton.Enable(False)
            self.testButtonList.append(newButton)

        self.closeButton = wx.Button(self.panel3, wx.ID_CLOSE, "", size = (150, -1))
        self.closeButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)

        sizer_1.Add(self.labelAnalyzer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 10)
        grid_sizer_1 = wx.FlexGridSizer(-1, 2)
        grid_sizer_1.Add(self.labelSelect, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.comboBoxSelect, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        for i in range(len(self.labelAnalyzerInfoList)):
            grid_sizer_1.Add(self.labelAnalyzerInfoList[i], 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
            grid_sizer_1.Add(self.textCtrlAnalyzerInfoList[i], 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1,10))
        self.panel1.SetSizer(sizer_1)
        
        sizer_2.Add(self.labelTest, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 10)
        for i in range(len(TEST_LIST)):
            sizer_2.Add(self.testButtonList[i], 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 10)
        sizer_2.Add(self.textCtrlIntegration, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        self.panel2.SetSizer(sizer_2)

        sizer_3.Add(self.closeButton, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 10)
        sizer_3.Add(self.labelFooter, 0, wx.EXPAND|wx.BOTTOM, 5)
        self.panel3.SetSizer(sizer_3)

        sizer_4.Add(self.panel1, 0, wx.EXPAND, 0)
        sizer_4.Add(self.panel2, 0, wx.EXPAND, 0)
        sizer_4.Add(self.panel3, 0, wx.EXPAND, 0)
        
        self.SetSizer(sizer_4)
        sizer_4.Fit(self)
        self.Layout()

class IntegrationTool(IntegrationToolFrame):
    def __init__(self, *args, **kwds):
        IntegrationToolFrame.__init__(self, *args, **kwds)
        self.wbCalFile = os.path.join(CAL_DIR, WARMBOX_CAL)
        self.wbCalBackup = os.path.join(CAL_DIR, (WARMBOX_CAL+"_Backup"))
        self.wbCalDuplicate = os.path.join(INTEGRATION_DIR, WARMBOX_CAL)
        self.hbCalFile = os.path.join(CAL_DIR, HOTBOX_CAL)
        self.display = ""
        self.analyzer = ""
        self.analyzerType = ""
        self.name = ""
        self.warmbox = ""
        self.wlm = ""
        self.hotbox = ""
        self.cavity = ""
        self.numLasers = 1
        self.laserSerNumDict = {}
        # For example, {1: ("966507", "CO2"), 2: ("916778", "CH4")}
        self.bindEvents()
        self.onSelect(None)
        
    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.closeButton)
        self.Bind(wx.EVT_BUTTON, self.onWriteInstrName, self.testButtonList[0])
        self.Bind(wx.EVT_BUTTON, self.onMakeIniFiles, self.testButtonList[1])
        self.Bind(wx.EVT_BUTTON, self.onLaserWlmCal, self.testButtonList[2])
        self.Bind(wx.EVT_BUTTON, self.onEEPROM, self.testButtonList[3])
        self.Bind(wx.EVT_BUTTON, self.onMakeWbCal, self.testButtonList[4])
        self.Bind(wx.EVT_BUTTON, self.onCalibrateSystem, self.testButtonList[5])
        self.Bind(wx.EVT_BUTTON, self.onWlmOffset, self.testButtonList[6])
        self.Bind(wx.EVT_BUTTON, self.onThresholdStats, self.testButtonList[7])
        self.Bind(wx.EVT_BUTTON, self.onFlowControl, self.testButtonList[8])
        self.Bind(wx.EVT_BUTTON, self.onWriteSoftwareVer, self.testButtonList[9])
        
    def onSelect(self, event):
        self.analyzer = self.comboBoxSelect.GetValue()
        self.analyzerType = "Beta"
        self.showAnalyzerName()
        
        if DB is None:
            # No database connection available
            if os.path.exists(self.wbCalFile+".ini") and os.path.exists(self.hbCalFile+".ini"):
                self.testButtonList[4].Enable(True)
                self.testButtonList[5].Enable(True)
                self.testButtonList[6].Enable(True)
                self.testButtonList[7].Enable(True)
                self.testButtonList[8].Enable(True)
            return

        self.testButtonList[0].Enable(True)
        self.testButtonList[9].Enable(True)

        try:
            self.warmbox = [elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer,type="chassis2k")) 
                            if elem['type'] == 'warmbox2k'][0]            
            self.testButtonList[1].Enable(True)
            self.testButtonList[2].Enable(True)
            self.testButtonList[3].Enable(True)
            self.testButtonList[4].Enable(True)
        except Exception, err:
            #print err
            self.warmbox = "N/A"
            self.testButtonList[1].Enable(False)
            self.testButtonList[2].Enable(False)
            self.testButtonList[3].Enable(False)
            self.testButtonList[4].Enable(False)
        self.textCtrlAnalyzerInfoList[1].SetValue(self.warmbox)
        
        try:
            self.wlm = [elem['identifier'] for elem in DB.get_contents(dict(identifier=self.warmbox,type="warmbox2k")) 
                            if elem['type'] == 'wlm2k'][0]            
        except Exception, err:
            #print err
            self.wlm = "N/A"
        self.textCtrlAnalyzerInfoList[2].SetValue(self.wlm)
        
        try:    
            self.hotbox = [elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer,type="chassis2k")) 
                            if elem['type'] == 'hotbox2k'][0]
            self.testButtonList[5].Enable(True)
            self.testButtonList[6].Enable(True)
            self.testButtonList[7].Enable(True)
            self.testButtonList[8].Enable(True)
        except Exception, err:
            #print err
            self.hotbox = "N/A"
            self.testButtonList[5].Enable(False)
            self.testButtonList[6].Enable(False)
            self.testButtonList[7].Enable(False)
            self.testButtonList[8].Enable(False)
        self.textCtrlAnalyzerInfoList[4].SetValue(self.hotbox)
            
        try:    
            self.cavity = [elem['identifier'] for elem in DB.get_contents(dict(identifier=self.hotbox)) 
                            if elem['type'] == 'cavity'][0]
        except Exception, err:
            #print err
            self.cavity = "N/A"
        self.textCtrlAnalyzerInfoList[5].SetValue(self.cavity)

        # Get laser PCB serial numbers
        self.laserSerNumDict = {}
        laserNumStr = ""
        try:
            self.numLasers = len([elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer,type="chassis2k")) 
                                  if elem['type'] == 'laserpcb2k'])
            for idx in range(self.numLasers):
                laserId = [elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer,type="chassis2k")) 
                            if elem['slot'] == 'Laser%dPcb'%(idx+1)][0]
                laserSerNum, laserTypeKey = DB.get_contents(dict(identifier=laserId,type="laserpcb2k"))[0]["identifier"].split("-")
                laserType = LASER_TYPE_DICT[laserTypeKey]
                self.laserSerNumDict[idx+1] = (laserSerNum, laserType)
                laserSer = laserSerNum+"-"+laserType
                laserNumStr += "%s, "%laserSer
        except Exception, err:
            #print err
            pass
        if laserNumStr != "":
            self.textCtrlAnalyzerInfoList[3].SetValue(laserNumStr[:-2])
        else:
            self.textCtrlAnalyzerInfoList[3].SetValue("N/A")

    def showAnalyzerName(self):
        try:
            analyzerId = Driver.fetchObject("LOGIC_EEPROM")[0]
            self.name = analyzerId["Chassis"] + "-" + analyzerId["Analyzer"] + analyzerId["AnalyzerNum"]
        except:
            self.name = "N/A"
        self.textCtrlAnalyzerInfoList[0].SetValue(self.name)
        
    def onAboutMenu(self, event):
        d = wx.MessageDialog(None, "Integration tool for calibrating and verifying Picarro G2000 instruments\n\nCopyright 1999-2010 Picarro Inc. All rights reserved.\nVersion: 0.01\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.", "About Integration Tool", wx.OK)
        d.ShowModal()
        d.Destroy()

    def onCloseButton(self, event):
        sys.exit(0)
        self.Destroy()

    def onWriteInstrName(self, event):
        info = subprocess.STARTUPINFO()
        subprocess.Popen([os.path.join(HOSTEXE_DIR, "InstrEEPROMAccess.exe")] + ["-d", self.analyzer.split("CHAS2K")[1]], startupinfo=info)
        self.showAnalyzerName()

    def onMakeIniFiles(self, event):
        try:
            wlmEepromCo = ConfigObj(os.path.join(INTEGRATION_DIR, "writeWlmEeprom.ini"), raise_errors=True)
            makeWarmBoxCalCo = ConfigObj(os.path.join(INTEGRATION_DIR, "MakeWarmBoxCalFile.ini"), raise_errors=True)
            makeEepromCalCo = ConfigObj(os.path.join(INTEGRATION_DIR, "MakeCalFromEeproms.ini"), raise_errors=True)
            iniList = ["writeWlmEeprom.ini", "MakeWarmBoxCalFile.ini", "MakeCalFromEeproms.ini"]
        except Exception, err:
            print err             
        for idx in range(self.numLasers):
            laserNum = idx+1
            laserFilename = "Laser_%s_%s" % self.laserSerNumDict[laserNum]
            co = ConfigObj(os.path.join(INTEGRATION_DIR, "MakeWlmFileLaser%d.ini" % laserNum), raise_errors=True)
            co["SETTINGS"]["FILENAME"] = os.path.join(INTEGRATION_DIR, laserFilename)
            co.write()
            co = ConfigObj(os.path.join(INTEGRATION_DIR, "writeLaserEeprom%d.ini" % laserNum), raise_errors=True)
            co["SETTINGS"]["FILENAME"] = os.path.join(INTEGRATION_DIR, laserFilename)
            co["SETTINGS"]["SERIAL"] = self.laserSerNumDict[laserNum][0]
            co.write()
            key = "LASER%d" % laserNum
            wlmEepromCo["FILES"][key] = os.path.join(INTEGRATION_DIR, laserFilename)
            makeWarmBoxCalCo["FILES"][key] = os.path.join(INTEGRATION_DIR, laserFilename)
            iniList = iniList + [("MakeWlmFileLaser%d.ini" % laserNum), ("writeLaserEeprom%d.ini" % laserNum)] 
        wlmEepromCo["SETTINGS"]["SERIAL"] = self.wlm
        makeWarmBoxCalCo["FILES"]["OUTPUT"] = self.wbCalBackup
        makeEepromCalCo["FILES"]["OUTPUT"] = self.wbCalFile
        
        wlmEepromCo.write()
        makeWarmBoxCalCo.write()
        makeEepromCalCo.write()
        
        self.display += "The following INI files are updated:\n"
        for ini in iniList:
            self.display += "%s\n" % ini
        self.textCtrlIntegration.SetValue(self.display) 
        
    def onLaserWlmCal(self, event):
        os.chdir(INTEGRATION_DIR)
        d = wx.MessageDialog(None,"Is Burleigh wavemeter connected?", "Check Burleigh wavemeter", \
        style=wx.YES_NO | wx.ICON_INFORMATION | wx.STAY_ON_TOP | wx.YES_DEFAULT)
        burleighConnected = (d.ShowModal() == wx.ID_YES)
        d.Destroy()
        if not burleighConnected:
            self.display += "Need to connect Burleigh wavemeter first...\n"
            self.textCtrlIntegration.SetValue(self.display)        
            return
        d = wx.TextEntryDialog(None, "Please enter time delay (minutes)", "Set time delay", "0.0")
        getDelay = (d.ShowModal() == wx.ID_OK)
        if getDelay:
            timeDelay = max(0.0, float(d.GetValue()))
            d.Destroy()
        else:
            self.display += "Action cancelled...\n"
            self.textCtrlIntegration.SetValue(self.display)
            d.Destroy()
            return 
        try:
            for idx in range(self.numLasers):
                laserNum = idx+1
                cmd = "%s -w %.1f -c %s" % (os.path.join(HOSTEXE_DIR, "MakeWlmFile1.exe"), timeDelay, "MakeWlmFileLaser%d.ini" % laserNum)
                print cmd
                os.system(cmd)
                self.display += "WLM file for laser %d created.\n" % laserNum
        except Exception, err:
            self.display += "%s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
 
    def onEEPROM(self, event):
        os.chdir(INTEGRATION_DIR)
        try:
            for idx in range(self.numLasers):
                laserNum = idx+1
                cmd = "%s -c %s" % (os.path.join(HOSTEXE_DIR, "WriteLaserEeprom.exe"), "WriteLaserEeprom%d.ini" % laserNum)
                print cmd
                os.system(cmd)
                self.display += "EEPROM for laser %d written.\n" % laserNum
        except Exception, err:
            self.display += "%s\n" % err
        try:
            cmd = "%s -c %s" % (os.path.join(HOSTEXE_DIR, "WriteWlmEeprom.exe"), "WriteWlmEeprom.ini")
            print cmd
            os.system(cmd)
            self.display += "EEPROM for WLM written.\n"  
        except Exception, err:
            self.display += "%s\n" % err           
        try:
            cmd = os.path.join(HOSTEXE_DIR, "DumpEeproms.exe")
            print cmd
            os.system(cmd)
            self.display += "Dump EEPROMs.\n" 
        except Exception, err:
            self.display += "%s\n" % err 
        self.textCtrlIntegration.SetValue(self.display)
            
    def onMakeWbCal(self, event):
        os.chdir(INTEGRATION_DIR)
        try:
            cmd = "%s -c %s" % (os.path.join(HOSTEXE_DIR, "MakeCalFromEeproms.exe"), "MakeCalFromEeproms.ini")
            print cmd
            os.system(cmd)
            self.display += "WB calibration table created from EEPROMs.\n"
        except Exception, err:
            self.display += "%s\n" % err    
        try:
            cmd = "%s -c %s" % (os.path.join(HOSTEXE_DIR, "MakeWarmBoxCalFile.exe"), "MakeWarmBoxCalFile.ini")
            print cmd
            os.system(cmd)
            self.display += ("WB calibration plots created by MakeWarmBoxCalFile.\nCheck %s for plots.\n" % INTEGRATION_DIR)
        except Exception, err:
            self.display += "%s\n" % err
        # Make copy to integration directory
        try:
            shutil.copy2(self.wbCalFile + '.ini', self.wbCalDuplicate + '.ini')
            self.display += "Copying %s to %s...\n" % (self.wbCalFile, self.wbCalDuplicate)
        except Exception, err:
            self.display += "%s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        
    def onCalibrateSystem(self, event):   
        os.chdir(INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile+".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile+".ini")
        iniList = [os.path.abspath(ini) for ini in os.listdir(".") if (ini.startswith("CalibrateSystem") and ini.endswith(".ini"))]
        newDir = time.strftime(INTEGRATION_DIR + "\CalibrateSystem\%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)            
            os.chdir(newDir)
            for ini in iniList:
                cmd = "%s -c %s" % (os.path.join(HOSTEXE_DIR, "CalibrateSystem.exe"), ini)
                print cmd
                os.system(cmd)
            self.display += "Calibrate System finished.\n"
        except Exception, err:
            self.display += "Calibrate System failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(INTEGRATION_DIR)
        
    def onWlmOffset(self, event):
        os.chdir(INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile+".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile+".ini")
        iniList = [os.path.abspath(ini) for ini in os.listdir(".") if (ini.startswith("FindWlmOffset") and ini.endswith(".ini"))]
        newDir = time.strftime(INTEGRATION_DIR + "\FindWlmOffset\%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)
            os.chdir(newDir)
            for ini in iniList:
                cmd = "%s -a -t 2e-4 -c %s" % (os.path.join(HOSTEXE_DIR, "FindWlmOffset.exe"), ini)
                print cmd
                os.system(cmd)
            self.display += "WLM Offset finished.\n"
        except Exception, err:
            self.display += "WLM Offset failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(INTEGRATION_DIR)
        
    def onThresholdStats(self, event):
        os.chdir(INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile+".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile+".ini")
        newDir = time.strftime(INTEGRATION_DIR + "\ThresholdStats\%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)
            os.chdir(newDir)
            analyzerId = Driver.fetchObject("LOGIC_EEPROM")[0]
            instrType = analyzerId["Analyzer"] 
            instrName = instrType + analyzerId["AnalyzerNum"]
            instrIdx = ANALYZER_TYPE_INDEX[instrType]
            schemeDict = ALL_SCHEMES[instrIdx]
            start, end, increment = THRESHOLD_RANGE[instrIdx]
            for schKey in schemeDict:
                schemeFileName = schemeDict[schKey]
                if not os.path.isfile(schemeFileName):
                    raise Exception, "Scheme file does not exist: %s"  % schemeFileName
                print "Running scheme %s" % schemeFileName
                currTime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                exePath = os.path.join(HOSTEXE_DIR, "ThresholdStats.exe")
                cmd = "%s %s %d %d %d %s" % (exePath, (instrName+"_"+schKey), start, end, increment, schemeFileName)
                print cmd
                os.system(cmd)
                print "Finished scheme %s" % schemeFileName
            self.display += "Threshold Stats finished.\n"
        except Exception, err:
            self.display += "Threshold Stats failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(INTEGRATION_DIR)
     
    def onFlowControl(self, event):
        try:
            cmd = os.path.join(HOSTEXE_DIR, "FlowController.exe")
            print cmd
            os.system(cmd)
            self.display += "Flow Control finished.\n"
        except Exception, err:
            self.display += "Flow Control failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)

    def onWriteSoftwareVer(self, event):
        try:
            softwareVer = Driver.allVersions()["host release"]
            reqDict = {"user": "xml_user", "passwd": "skCyrcFHVZecfD", "identifier": self.analyzer, "Analyzer Software Version": softwareVer}
            DB.set_compnent_version(reqDict)
            self.display += "Software version number %s written to database.\n" % softwareVer
        except Exception, err:
            self.display += "Software version number can't be written to database: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = IntegrationTool(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()