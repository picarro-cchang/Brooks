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
import threading
import getopt
import traceback
from configobj import ConfigObj
from xmlrpclib import ServerProxy
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER

if hasattr(sys, "frozen"):  #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

DEFAULT_CONFIG_NAME = "IntegrationTool.ini"

FreqConverter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                           "IntegrationTool",
                                           IsDontCareConnection=False)
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, "IntegrationTool")

ANALY_INFO_LIST = ["Name", "Warm Box", "WLM", "Laser(s)", "Hot Box", "Cavity"]
TEST_LIST = [
    "Write Instrument Name", "Make Integration INI Files", "Calibrate WB Laser/WLM", "Update Laser/WLM EEPROM",
    "Create WB Cal Table", "Run Calibrate FSR", "Run Calibrate System", "Calculate WLM Offset", "Run Threshold Stats",
    "Run Flow Control", "Write Software Version"
]

# Connect to database
try:
    #http://user:pass@host:port/path
    DB = ServerProxy("http://mfgteam:PridJaHop4@mfg.picarro.com/xmlrpc/", allow_none=True)
    DB.system.listMethods()
except:
    DB = None


class IntegrationToolFrame(wx.Frame):
    def __init__(self, configFile, *args, **kwds):
        #kwds["style"] = wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL | wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL | wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL | wx.ALWAYS_SHOW_SB)
        self.SetTitle("Picarro Integration Tool")
        self.labelFooter = wx.StaticText(self.panel3,
                                         -1,
                                         "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0],
                                         style=wx.ALIGN_CENTER)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.panel3.SetBackgroundColour("#85B24A")

        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iHelp = wx.Menu()

        self.frameMenubar.Append(self.iHelp, "Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "About Picarro Integration Tool", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)

        # Analyzer information section
        self.labelAnalyzer = wx.StaticText(self.panel1, -1, "Analyzer Information", style=wx.ALIGN_CENTER)
        self.labelAnalyzer.SetFont(wx.Font(10, wx.DEFAULT, style=wx.NORMAL, weight=wx.BOLD))
        if not os.path.exists(configFile):
            raise Exception("Config file not found: %s" % configFile)
        cp = CustomConfigObj(configFile)
        chassis_type = cp.get('Main', 'CHASSIS_TYPE')
        analyzerChassis = None
        try:
            analyzerChassis = chassis_type + Driver.fetchObject("LOGIC_EEPROM")[0]["Chassis"]
        except:
            # If we can't read the EEPROM assume we are running a simulator and put
            # a dummy name so the application will start.
            print('unable to get chassis information from EEPROM, please update EEPROM and relaunch')
            analyzerChassis = "SIMULATOR_MODE"
        if analyzerChassis:
            analyzerChoices = [analyzerChassis]
            self.comboBoxSelect = wx.ComboBox(self.panel1,
                                              -1,
                                              choices=analyzerChoices,
                                              value=analyzerChassis,
                                              size=(250, -1),
                                              style=wx.CB_READONLY | wx.CB_DROPDOWN)
                #self.comboBoxSelect = wx.ComboBox(self.panel1, -1, value = analyzerChoices[0], choices = analyzerChoices, size = (250, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        else:
            raise Exception, "Failed to read instrument ID from EEPROM"
        self.labelSelect = wx.TextCtrl(self.panel1, -1, "Analyzer", size=(80, -1), style=wx.TE_READONLY | wx.NO_BORDER)
        self.labelSelect.SetBackgroundColour("#E0FFFF")

        self.labelAnalyzerInfoList = []
        self.textCtrlAnalyzerInfoList = []
        for i in range(len(ANALY_INFO_LIST)):
            newLabel = wx.TextCtrl(self.panel1, -1, ANALY_INFO_LIST[i], size=(80, -1), style=wx.TE_READONLY | wx.NO_BORDER)
            newLabel.SetBackgroundColour("#E0FFFF")
            self.labelAnalyzerInfoList.append(newLabel)
            self.textCtrlAnalyzerInfoList.append(wx.TextCtrl(self.panel1, -1, "", size=(250, -1), style=wx.TE_READONLY))

        # Integration test section
        self.labelTest = wx.StaticText(self.panel2, -1, "Integration Test", style=wx.ALIGN_CENTER)
        self.labelTest.SetFont(wx.Font(10, wx.DEFAULT, style=wx.NORMAL, weight=wx.BOLD))

        self.textCtrlIntegration = wx.TextCtrl(self.panel2,
                                               -1,
                                               "",
                                               style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_AUTO_URL | wx.TE_RICH)
        self.textCtrlIntegration.SetMinSize((350, 150))

        self.testButtonList = []
        for i in range(len(TEST_LIST)):
            newButton = wx.Button(self.panel2, -1, TEST_LIST[i], size=(350, -1))
            newButton.SetBackgroundColour(wx.Colour(237, 228, 199))
            newButton.Enable(False)
            self.testButtonList.append(newButton)

        self.closeButton = wx.Button(self.panel3, wx.ID_CLOSE, "", size=(150, -1))
        self.closeButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.__do_layout()

    def __do_layout(self):
        """
        Set the layout with analyzer information widgets on the top left,
        launch buttons for configuration apps on the right, and the close
        button in its own panel on the bottom spanning the width of the window.

        The original layout was all vertically stacked but it doesn't fit
        on smaller displays.
        """
        sizer_1 = wx.BoxSizer(wx.VERTICAL)  # sizer for analyzer information fields
        sizer_2 = wx.BoxSizer(wx.VERTICAL)  # sizer for code launchers
        sizer_3 = wx.BoxSizer(wx.VERTICAL)  # sizer for close button
        sizer_4 = wx.GridBagSizer(2, 2)

        sizer_1.Add(self.labelAnalyzer, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER, 10)
        grid_sizer_1 = wx.FlexGridSizer(0, 2)
        grid_sizer_1.Add(self.labelSelect, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.comboBoxSelect, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
        for i in range(len(self.labelAnalyzerInfoList)):
            grid_sizer_1.Add(self.labelAnalyzerInfoList[i], 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
            grid_sizer_1.Add(self.textCtrlAnalyzerInfoList[i], 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1, 10))
        self.panel1.SetSizer(sizer_1)

        sizer_2.Add(self.labelTest, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER, 10)
        for i in range(len(TEST_LIST)):
            sizer_2.Add(self.testButtonList[i], 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER, 10)
        sizer_2.Add(self.textCtrlIntegration, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        self.panel2.SetSizer(sizer_2)

        sizer_3.Add(self.closeButton, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        sizer_3.Add(self.labelFooter, 0, wx.EXPAND | wx.BOTTOM, 5)
        self.panel3.SetSizer(sizer_3)

        sizer_4.Add(self.panel1, pos=(0, 0), flag=wx.EXPAND)
        sizer_4.Add(self.panel2, pos=(0, 1), flag=wx.EXPAND)
        sizer_4.Add(self.panel3, pos=(1, 0), span=(1, 2), flag=wx.EXPAND)

        self.SetSizer(sizer_4)
        sizer_4.Fit(self)
        self.Layout()


class IntegrationTool(IntegrationToolFrame):
    def __init__(self, configFile, *args, **kwds):
        IntegrationToolFrame.__init__(self, configFile, *args, **kwds)
        if not os.path.exists(configFile):
            raise Exception("Config file not found: %s" % configFile)
        else:
            self.cp = CustomConfigObj(configFile)
            self.LaserTypeDict = self.cp["LASER_TYPE_DICT"]
            for aType in self.cp["THRESHOLD_STATS_SCHEMES"]:
                for sName in self.cp["THRESHOLD_STATS_SCHEMES"][aType]:
                    newStr = r"%s" % self.cp["THRESHOLD_STATS_SCHEMES"][aType][sName]
                    self.cp["THRESHOLD_STATS_SCHEMES"][aType][sName] = newStr
            self.allSchemes = self.cp["THRESHOLD_STATS_SCHEMES"]
            WARMBOX_CAL = self.cp.get("Main", "WARMBOX_CAL")
            WARMBOX_CAL_ACTIVE = self.cp.get("Main", "WARMBOX_CAL_ACTIVE")
            HOTBOX_CAL = self.cp.get("Main", "HOTBOX_CAL")
            HOTBOX_CAL_ACTIVE = self.cp.get("Main", "HOTBOX_CAL_ACTIVE")
            CAL_DIR = self.cp.get("Main", "INSTR_CAL_DIR")
            self.INTEGRATION_DIR = self.cp.get("Main", "INTEGRATION_DIR")
            self.wbCalFile = os.path.join(CAL_DIR, WARMBOX_CAL)
            self.wbCalBackup = os.path.join(CAL_DIR, (WARMBOX_CAL + "_Backup"))
            self.wbCalDuplicate = os.path.join(self.INTEGRATION_DIR, WARMBOX_CAL)
            self.wbCalActive = os.path.join(CAL_DIR, WARMBOX_CAL_ACTIVE)
            self.hbCalFile = os.path.join(CAL_DIR, HOTBOX_CAL)
            self.hbCalActive = os.path.join(CAL_DIR, HOTBOX_CAL_ACTIVE)

            self.textCtrlIntegration.SetValue("Config file specified at command line: %s" % configFile)
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
        self.Bind(wx.EVT_BUTTON, self.onCalibrateFSR, self.testButtonList[5])
        self.Bind(wx.EVT_BUTTON, self.onCalibrateSystem, self.testButtonList[6])
        self.Bind(wx.EVT_BUTTON, self.onWlmOffset, self.testButtonList[7])
        self.Bind(wx.EVT_BUTTON, self.onThresholdStats, self.testButtonList[8])
        self.Bind(wx.EVT_BUTTON, self.onFlowControl, self.testButtonList[9])
        self.Bind(wx.EVT_BUTTON, self.onWriteSoftwareVer, self.testButtonList[10])

    def onSelect(self, event):
        self.analyzer = self.comboBoxSelect.GetValue()
        self.analyzerType = "Beta"
        self.showAnalyzerName()

        if DB is None:
            # No database connection available
            if os.path.exists(self.wbCalFile + ".ini") and os.path.exists(self.hbCalFile + ".ini"):
                self.testButtonList[4].Enable(True)
                self.testButtonList[5].Enable(True)
                self.testButtonList[6].Enable(True)
                self.testButtonList[7].Enable(True)
                self.testButtonList[8].Enable(True)
                self.testButtonList[9].Enable(True)
            return

        self.testButtonList[0].Enable(True)
        self.testButtonList[10].Enable(True)

        try:
            self.warmbox = [
                elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer))
                if 'warmbox' in elem['type']
            ][0]
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
            self.wlm = [
                elem['identifier'] for elem in DB.get_contents(dict(identifier=self.warmbox))
                if 'wlm' in elem['type']
            ][0]
        except Exception, err:
            #print err
            self.wlm = "N/A"
        self.textCtrlAnalyzerInfoList[2].SetValue(self.wlm)

        try:
            self.hotbox = [
                elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer))
                if 'hotbox' in elem['type']
            ][0]
            self.testButtonList[5].Enable(True)
            self.testButtonList[6].Enable(True)
            self.testButtonList[7].Enable(True)
            self.testButtonList[8].Enable(True)
            self.testButtonList[9].Enable(True)
        except Exception, err:
            #print err
            self.hotbox = "N/A"
            self.testButtonList[5].Enable(False)
            self.testButtonList[6].Enable(False)
            self.testButtonList[7].Enable(False)
            self.testButtonList[8].Enable(False)
            self.testButtonList[9].Enable(False)
        self.textCtrlAnalyzerInfoList[4].SetValue(self.hotbox)

        try:
            self.cavity = [
                elem['identifier'] for elem in DB.get_contents(dict(identifier=self.hotbox)) if elem['type'] == 'cavity'
            ][0]
        except Exception, err:
            #print err
            self.cavity = "N/A"
        self.textCtrlAnalyzerInfoList[5].SetValue(self.cavity)

        # Get laser PCB serial numbers
        self.laserSerNumDict = {}
        laserNumStr = ""

        try:
            self.numLasers = len([
                elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer))
                if 'laser' in elem['type']
            ])
            for idx in range(self.numLasers):
                laserId = [
                    elem['identifier'] for elem in DB.get_contents(dict(identifier=self.analyzer))
                    if 'Laser' in elem['slot']
                ][idx]
                laserSerNum, laserTypeKey = DB.get_contents(dict(identifier=laserId))[0]["identifier"].split("-")
                laserType = self.LaserTypeDict[laserTypeKey]
                self.laserSerNumDict[idx + 1] = (laserSerNum, laserType)
                laserSer = laserSerNum + "-" + laserType
                laserNumStr += "%s, " % laserSer
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
        msg = "Integration tool for calibrating and verifying Picarro G2000 instruments\n\n" + \
            "Copyright 1999-%d Picarro Inc. All rights reserved.\n" % time.localtime()[0] + \
            "Version: 0.01\nThe copyright of this computer program belongs to Picarro Inc.\n" + \
            "Any reproduction or distribution of this program requires permission from Picarro Inc."
        d = wx.MessageDialog(None, msg, "About Integration Tool", wx.OK)
        d.ShowModal()
        d.Destroy()

    def onCloseButton(self, event):
        sys.exit(0)
        self.Destroy()

    def onWriteInstrName(self, event):
        os.chdir(self.INTEGRATION_DIR)
        try:
            info = subprocess.STARTUPINFO()
        except:
            info = None
        executable = self.cp.get("InstrEEPROMAccess", "Executable")
        args = self.cp.get("InstrEEPROMAccess", "LaunchArgs")
        command_list = executable.split() + args.split()
        print(command_list)
        #commandList = executable.split() + args.split() + ["-d", self.analyzer.split("CHAS2K")[1]]
        subprocess.Popen(command_list, startupinfo=info)
        self.showAnalyzerName()

    def onMakeIniFiles(self, event):
        try:
            writeWlmEeprom_ini = self.cp.get("MakeIniFiles", "writeWlmEeprom_ini")
            makeWarmBoxCalFile_ini = self.cp.get("MakeIniFiles", "MakeWarmBoxCalFile_ini")
            makeCalFromEeproms_ini = self.cp.get("MakeIniFiles", "MakeCalFromEeproms_ini")
            wlmEepromCo = ConfigObj(os.path.join(self.INTEGRATION_DIR, writeWlmEeprom_ini), raise_errors=True)
            makeWarmBoxCalCo = ConfigObj(os.path.join(self.INTEGRATION_DIR, makeWarmBoxCalFile_ini), raise_errors=True)
            makeEepromCalCo = ConfigObj(os.path.join(self.INTEGRATION_DIR, makeCalFromEeproms_ini), raise_errors=True)
            iniList = [writeWlmEeprom_ini, makeWarmBoxCalFile_ini, makeCalFromEeproms_ini]
        except Exception, err:
            print err
        for idx in range(self.numLasers):
            laserNum = idx + 1
            laserFilename = "Laser_%s_%s" % self.laserSerNumDict[laserNum]
            co = ConfigObj(os.path.join(self.INTEGRATION_DIR, "MakeWlmFileLaser%d.ini" % laserNum), raise_errors=True)
            co["SETTINGS"]["FILENAME"] = os.path.join(self.INTEGRATION_DIR, laserFilename)
            co.write()
            co = ConfigObj(os.path.join(self.INTEGRATION_DIR, "writeLaserEeprom%d.ini" % laserNum), raise_errors=True)
            co["SETTINGS"]["FILENAME"] = os.path.join(self.INTEGRATION_DIR, laserFilename)
            co["SETTINGS"]["SERIAL"] = self.laserSerNumDict[laserNum][0]
            co.write()
            key = "LASER%d" % laserNum
            wlmEepromCo["FILES"][key] = os.path.join(self.INTEGRATION_DIR, laserFilename)
            makeWarmBoxCalCo["FILES"][key] = os.path.join(self.INTEGRATION_DIR, laserFilename)
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

        newThread = threading.Thread(target=self._onLaserWlmCal, args=(timeDelay, ))
        newThread.setDaemon(True)
        newThread.start()

    def _onLaserWlmCal(self, timeDelay):
        os.chdir(self.INTEGRATION_DIR)
        executable = self.cp.get("MakeWlmFile1", "Executable")
        iniFile = self.cp.get("MakeWlmFile1", "ConfigFileBase")
        try:
            for idx in range(self.numLasers):
                laserNum = idx + 1
                cmd = executable.split() + ["-w", "%.1f" % timeDelay, "-c", "%s%d.ini" % (iniFile, laserNum)]
                print " ".join(cmd)
                subprocess.Popen(cmd).wait()
                self.display += "WLM file for laser %d created\n" % laserNum
        except Exception, err:
            self.display += "%s\n" % err
        self.textCtrlIntegration.SetValue(self.display)

    def onEEPROM(self, event):
        newThread = threading.Thread(target=self._onEEPROM)
        newThread.setDaemon(True)
        newThread.start()

    def _onEEPROM(self):
        # Need to use blocking calls to serialize the events
        os.chdir(self.INTEGRATION_DIR)
        executable = self.cp.get("UpdateEEPROM", "WriteLaserEeprom_Executable")
        iniFile = self.cp.get("UpdateEEPROM", "WriteLaserEeprom_ConfigFileBase")
        try:
            for idx in range(self.numLasers):
                laserNum = idx + 1
                cmd = executable.split() + ["-c", "%s%d.ini" % (iniFile, laserNum)]
                print " ".join(cmd)
                subprocess.Popen(cmd).wait()
                self.display += "EEPROM for laser %d written.\n" % laserNum
        except Exception, err:
            self.display += "%s\n" % err
        try:
            executable = self.cp.get("UpdateEEPROM", "WriteWlmEeprom_Executable")
            args = self.cp.get("UpdateEEPROM", "WriteWlmEeprom_LaunchArgs")
            cmd = executable.split() + args.split()
            print " ".join(cmd)
            subprocess.Popen(cmd).wait()
            self.display += "EEPROM for WLM written.\n"
        except Exception, err:
            self.display += "%s\n" % err
        try:
            executable = self.cp.get("UpdateEEPROM", "DumpEeproms_Executable")
            print executable
            subprocess.Popen(executable.split()).wait()
            self.display += "Dump EEPROMs.\n"
        except Exception, err:
            self.display += "%s\n" % err
        self.textCtrlIntegration.SetValue(self.display)

    def onMakeWbCal(self, event):
        newThread = threading.Thread(target=self._onMakeWbCal)
        newThread.setDaemon(True)
        newThread.start()

    def _onMakeWbCal(self):
        os.chdir(self.INTEGRATION_DIR)
        try:
            executable = self.cp.get("MakeWbCal", "MakeCalFromEeproms_Executable")
            args = self.cp.get("MakeWbCal", "MakeCalFromEeproms_LaunchArgs")
            cmd = executable.split() + args.split()
            print " ".join(cmd)
            subprocess.call(cmd)
            self.display += "WB calibration table created from EEPROMs.\n"
        except Exception, err:
            self.display += "%s\n" % err
        try:
            executable = self.cp.get("MakeWbCal", "MakeWarmBoxCalFile_Executable")
            args = self.cp.get("MakeWbCal", "MakeWarmBoxCalFile_LaunchArgs")
            cmd = executable.split() + args.split()
            print " ".join(cmd)
            subprocess.call(cmd)
            self.display += ("WB calibration plots created by MakeWarmBoxCalFile.\nCheck %s for plots.\n" % self.INTEGRATION_DIR)
        except Exception, err:
            self.display += "%s\n" % err
        # Make copy to integration directory
        try:
            shutil.copy2(self.wbCalFile + '.ini', self.wbCalDuplicate + '.ini')
            self.display += "Copying %s to %s...\n" % (self.wbCalFile, self.wbCalDuplicate)
        except Exception, err:
            self.display += "%s\n" % err
        self.textCtrlIntegration.SetValue(self.display)

    def onCalibrateFSR(self, event):
        os.chdir(self.INTEGRATION_DIR)
        iniList = [os.path.abspath(ini) for ini in os.listdir(".") if (ini.startswith("CalibrateFSR") and ini.endswith(".ini"))]
        dlg = wx.SingleChoiceDialog(self, "Select FSR calibration to perform", "Cavity FSR calibration", iniList,
                                    wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() != wx.ID_OK: return
        ini = dlg.GetStringSelection()
        dlg.Destroy()
        co = ConfigObj(os.path.join("../..", ini), raise_errors=True)
        if 'INSTRUCTIONS' in co['SETTINGS']:
            if wx.MessageBox(co['SETTINGS']['INSTRUCTIONS'], "Instructions - Cancel if not ready", wx.OK | wx.CANCEL) != wx.OK:
                return
        spectrumFile = os.path.abspath(co['SETTINGS']['SPECTRUM_FILE'])
        if os.path.exists(spectrumFile):
            os.remove(spectrumFile)
            print "Deleted old spectrum file: %s" % spectrumFile
        fitIni = os.path.abspath(co['SETTINGS']['FITTER_FILE'])
        newThread = threading.Thread(target=self._onCalibrateFSR, args=(ini, spectrumFile, fitIni))
        newThread.setDaemon(True)
        newThread.start()

    def _onCalibrateFSR(self, ini, spectrumFile, fitIni):
        os.chdir(self.INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile + ".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile + ".ini")
        newDir = time.strftime(self.INTEGRATION_DIR + "/CalibrateFSR/%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)
            os.chdir(newDir)
            executable = self.cp.get("CalibrateFSR", "CalibrateFSR_Executable")
            cmd = executable.split() + ["-c", ini]
            print " ".join(cmd)
            subprocess.call(cmd)
            time.sleep(2.0)
            src = spectrumFile
            dest = os.path.join(newDir, os.path.split(src)[1])
            nAttempts = 0
            while nAttempts < 10:
                try:
                    shutil.move(src, dest)
                    print "Moving %s to %s" % (src, dest)
                    break
                except:
                    time.sleep(2.0)
                    nAttempts += 1
            if nAttempts >= 10:
                raise RuntimeError("Cannot move file %s to result directory" % src)
            executable = self.cp.get("CalibrateFSR", "Fitter_Executable")
            cmd = executable.split() + ["-c", fitIni, "-d", dest]
            print " ".join(cmd)
            subprocess.call(cmd)
            # Read output file to find FSR and check quality
            fp = file('FSR_calibration.txt', 'r')
            for line in fp:
                if line.startswith('Fitted '): numLines = int(line[7:line.find(" ", 7)])
                if line.startswith('FSR = '): fsr = float(line[6:line.find(" ", 6)])
                if line.startswith('RMS residual = '): res = float(line[15:line.find(" ", 15)])
            if numLines < 3:
                raise ValueError("Insufficient reference lines (%d) found" % numLines)
            if res > 1.0e-3:
                raise ValueError("Residual (%f) is too large for reliable FSR" % res)
            fp.close()
            # On success modify the CalibrateSystem INI files
            print "Cavity FSR is: %.7f" % fsr
            calSysList = [i for i in os.listdir("../..") if (i.startswith("CalibrateSystem") and i.endswith(".ini"))]
            for cs in calSysList:
                print "Writing cavity FSR into %s" % cs
                co = ConfigObj(os.path.join("../..", cs), raise_errors=True)
                co["SETTINGS"]["CAVITY_FSR"] = fsr
                co.write()
            self.display += "Calibrate FSR finished.\n"
        except Exception, err:
            self.display += "Calibrate FSR failed: %s\n" % err
            self.display += traceback.format_exc()

        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(self.INTEGRATION_DIR)
        print "Task done\n" + '-' * 35

    def onCalibrateSystem(self, event):
        newThread = threading.Thread(target=self._onCalibrateSystem)
        newThread.setDaemon(True)
        newThread.start()

    def _onCalibrateSystem(self):
        os.chdir(self.INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile + ".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile + ".ini")
        iniList = [os.path.abspath(ini) for ini in os.listdir(".") if (ini.startswith("CalibrateSystem") and ini.endswith(".ini"))]
        newDir = time.strftime(self.INTEGRATION_DIR + "/CalibrateSystem/%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)
            os.chdir(newDir)
            executable = self.cp.get("CalibrateSystem", "Executable")
            for ini in iniList:
                cmd = executable.split() + ["-c", ini]
                print " ".join(cmd)
                subprocess.call(cmd)
            self.display += "Calibrate System finished.\n"
            # Move the current active files to Integration folder
            if os.path.isfile(self.wbCalActive + ".ini"):
                savedWbCalActive = os.path.join(newDir, time.strftime(os.path.split(self.wbCalActive)[1] + "_%Y%m%d_%H%M%S.ini"))
                shutil.move(self.wbCalActive + ".ini", savedWbCalActive)
            if os.path.isfile(self.hbCalActive + ".ini"):
                savedHbCalActive = os.path.join(newDir, time.strftime(os.path.split(self.hbCalActive)[1] + "_%Y%m%d_%H%M%S.ini"))
                shutil.move(self.hbCalActive + ".ini", savedHbCalActive)
            self.display += "Archived active WB file.\n"
        except Exception, err:
            self.display += "Calibrate System failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(self.INTEGRATION_DIR)
        print "Task done\n" + '-' * 35

    def onWlmOffset(self, event):
        newThread = threading.Thread(target=self._onWlmOffset)
        newThread.setDaemon(True)
        newThread.start()

    def _onWlmOffset(self):
        os.chdir(self.INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile + ".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile + ".ini")
        iniList = [os.path.abspath(ini) for ini in os.listdir(".") if (ini.startswith("FindWlmOffset") and ini.endswith(".ini"))]
        newDir = time.strftime(self.INTEGRATION_DIR + "/FindWlmOffset/%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)
            os.chdir(newDir)
            executable = self.cp.get("FindWlmOffset", "Executable")
            for ini in iniList:
                cmd = executable.split() + ["-a", "-t", "2e-4", "-c", ini]
                print " ".join(cmd)
                subprocess.call(cmd)
            # Move the current active WB file to Integration folder
            if os.path.isfile(self.wbCalActive + ".ini"):
                savedWbCalActive = os.path.join(newDir, time.strftime(os.path.split(self.wbCalActive)[1] + "_%Y%m%d_%H%M%S.ini"))
                shutil.move(self.wbCalActive + ".ini", savedWbCalActive)
            self.display += "Archived active WB file.\n"
            self.display += "WLM Offset finished.\n"
        except Exception, err:
            self.display += "WLM Offset failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(self.INTEGRATION_DIR)
        print "Task done\n" + '-' * 35

    def onThresholdStats(self, event):
        newThread = threading.Thread(target=self._onThresholdStats)
        newThread.setDaemon(True)
        newThread.start()

    def _onThresholdStats(self):
        os.chdir(self.INTEGRATION_DIR)
        FreqConverter.loadWarmBoxCal(self.wbCalFile + ".ini")
        FreqConverter.loadHotBoxCal(self.hbCalFile + ".ini")
        newDir = time.strftime(self.INTEGRATION_DIR + "/ThresholdStats/%Y%m%d_%H%M%S")
        try:
            if not os.path.isdir(newDir):
                os.makedirs(newDir)
            os.chdir(newDir)
            analyzerId = Driver.fetchObject("LOGIC_EEPROM")[0]
            instrType = analyzerId["Analyzer"]
            instrName = instrType + analyzerId["AnalyzerNum"]
            schemeDict = self.allSchemes[instrType]
            start, end, increment = [2000, 16000, 1000]
            executable = self.cp.get("ThresholdStats", "Executable")
            for schKey in schemeDict:
                schemeFileName = schemeDict[schKey]
                if not os.path.isfile(schemeFileName):
                    raise Exception, "Scheme file does not exist: %s" % schemeFileName
                print "Running scheme %s" % schemeFileName
                currTime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                cmd = executable.split() + [instrName + "_" + schKey, str(start), str(end), str(increment), schemeFileName]
                print " ".join(cmd)
                subprocess.Popen(cmd).wait()
                print "Finished scheme %s" % schemeFileName
            self.display += "Threshold Stats finished.\n"
        except Exception, err:
            self.display += "Threshold Stats failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)
        os.chdir(self.INTEGRATION_DIR)
        print "Task done\n" + '-' * 35

    def onFlowControl(self, event):
        try:
            cmd = self.cp.get("FlowControl", "Executable")
            print cmd
            try:
                info = subprocess.STARTUPINFO()
            except:
                info = None
            subprocess.Popen(cmd.split(" "), startupinfo=info)
            self.display += "Starting Flow Control ...\n"
        except Exception, err:
            self.display += "Flow Control failed: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)

    def onWriteSoftwareVer(self, event):
        try:
            softwareVer = Driver.allVersions()["host release"]
            dbAnalyzer = DB.get_container(dict(identifier=self.analyzer))["identifier"]
            reqDict = {
                "user": "xml_user",
                "passwd": "skCyrcFHVZecfD",
                "identifier": dbAnalyzer,
                "Analyzer Software Version": softwareVer
            }
            DB.set_compnent_version(reqDict)
            self.display += "Software version number %s written to database.\n" % softwareVer
        except Exception, err:
            self.display += "Software version number can't be written to database: %s\n" % err
        self.textCtrlIntegration.SetValue(self.display)


def handleCommandSwitches():
    shortOpts = "c:"
    longOpts = []
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile


if __name__ == "__main__":
    app = wx.App(False)
    configFile = handleCommandSwitches()
    frame = IntegrationTool(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
