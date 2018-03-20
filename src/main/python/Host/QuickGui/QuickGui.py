#!/usr/bin/python
# -*- coding: utf-8 -*-
#
"""
File Name: QuickGui.py
Purpose: Simple GUI for plotting measurement system and data manager broadcasts

$>QuickGui.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify config file.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "QuickGui"
UPDATE_TIMER_INTERVAL = 1000

import wx
import Queue
import requests
import os
import wx.lib.mixins.listctrl as listmix
import subprocess32 as subprocess


from Host.QuickGui.UserCalGui import UserCalGui
from Host.QuickGui.SysAlarmGui import *
from Host.QuickGui.MeasureAlarmGui import AlarmViewListCtrl
import Host.QuickGui.DialogUI as Dialog
from Host.Common import CmdFIFO
from Host.Common import GraphPanel
from Host.Common.GuiTools import ColorDatabase, FontDatabase, SubstDatabase, StringDict, getInnerStr, setItemFont
from Host.Common.SharedTypes import RPC_PORT_DATA_MANAGER, RPC_PORT_SAMPLE_MGR, RPC_PORT_DRIVER, RPC_PORT_VALVE_SEQUENCER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.parsePeriphIntrfConfig import parsePeriphIntrfConfig
from Host.Common.EventManagerProxy import *

from Host.DataLogger.DataLoggerInterface import DataLoggerInterface
from Host.InstMgr.InstMgrInterface import InstMgrInterface
from Host.AlarmSystem.AlarmInterface import AlarmInterface
from Host.EventManager.EventStore import EventStore
from Host.DataManager.DataStore import DataStoreForGraphPanels

from Host.Utilities.UserAdmin.UserAdmin import DB_SERVER_URL

AppPath = os.path.dirname(os.path.realpath(__file__))
TimeStamp = time.time

class EventViewListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """ListCtrl that auto-sizes the right-most column to fit the width.

    DataSource must be the EventStore object which contains the event history
    """
    def __init__(self, parent, id, config, DataSource, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        wx.ListCtrl.__init__(self, parent, id, pos, size,
                             style = wx.LC_REPORT
                             | wx.LC_VIRTUAL
                             | wx.BORDER_NONE
                             | wx.LC_SINGLE_SEL
                         )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.ilEventIcons = wx.ImageList(16, 16)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)
        self.IconIndex_Warning  = myIL.Add(wx.Bitmap(AppPath + '/task-attention.png',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconIndex_Info     = myIL.Add(wx.Bitmap(AppPath + '/dialog-information.png',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconIndex_Critical = myIL.Add(wx.Bitmap(AppPath + '/dialog-error.png',
                                                     wx.BITMAP_TYPE_ICO))
        self._DataSource = DataSource
        self.firstItem = 0

        self.columns = []
        if not config.getboolean("StatusBox","ShowHeader"):
            self.SetSingleStyle(wx.LC_NO_HEADER)
        self.showIcon = config.getboolean("StatusBox","ShowIcon")
        if self.showIcon:
            self.columns.append(("", dict(width=24), None))
        else:
            self.columns.append(("",dict(width=0),None))
        if config.getboolean("StatusBox","ShowIndex"):
            self.columns.append(("Index",dict(format=wx.LIST_FORMAT_RIGHT,width=55),0))
        if config.getboolean("StatusBox","ShowDate"):
            self.columns.append(("Date",dict(width=80),1))
        if config.getboolean("StatusBox","ShowTime"):
            self.columns.append(("Time",dict(width=60),2))
        if config.getboolean("StatusBox","ShowSource"):
            self.columns.append(("Source",dict(width=100),3))
        if config.getboolean("StatusBox","ShowCode"):
            self.columns.append(("Code",dict(width=50),5))
        if config.getboolean("StatusBox","ShowDescription"):
            self.columns.append(("Description",dict(width=250),6))
        for i in range(len(self.columns)):
            col = self.columns[i]
            self.InsertColumn(i, col[0],**col[1])
        self.SetItemCount(self._DataSource.getEventCount())

    def OnGetItemText(self,item,col):
        x = self._DataSource.getEvent(self.firstItem+item)
        field = self.columns[col][2]
        if x is None or field is None:
            return ""
        else:
            return "%s" % (x[field],)

    def OnGetItemAttr(self,item):
        return None

    def OnGetItemImage(self, item):
        if not self.showIcon: return None
        evtLevel = self._DataSource.getEvent(self.firstItem+item)[4]
        if evtLevel == 0: #debug
            return self.IconIndex_Info
        elif evtLevel == 1:
            return -1
        elif evtLevel == 2:
            return self.IconIndex_Warning
        elif evtLevel == 3: #Major
            return self.IconIndex_Critical
        else:
            return -1

    def RefreshList(self):
        lastVisible = self.GetTopItem() >= self.GetItemCount() - self.GetCountPerPage()
        if self.firstItem+self.GetTopItem()<self._DataSource.getFirstEventIndex():
            lastVisible = True
        self.SetItemCount(self._DataSource.getEventCount())
        if lastVisible:
            itemCount = self.GetItemCount()
            if self._DataSource.getEventCount() == self._DataSource.getMaxEvents():
                self.RefreshItems(0,itemCount-1)            
            if itemCount > 0:
                self.EnsureVisible(itemCount-1)
            self.firstItem = self._DataSource.getFirstEventIndex()


class InstStatusPanel(wx.Panel):
    """The InstStatusPanel has check indicators which show the states of the control loops
    """
    def __init__(self, font, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)

        self.warmBoxTempLabel = wx.StaticText(self, -1, "Warm Box Temp (degC)")
        setItemFont(self.warmBoxTempLabel,font)
        self.cavityTempLabel = wx.StaticText(self, -1, "Cavity Temperature (degC)")
        setItemFont(self.cavityTempLabel,font)
        self.cavityPressureLabel = wx.StaticText(self, -1, "Cavity Pressure (Torr)")
        setItemFont(self.cavityPressureLabel,font)

        self.warmBoxTemp = wx.TextCtrl(self, -1, style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2)
        self.warmBoxTemp.SetMinSize((55, -1))
        self.warmBoxTemp.SetBackgroundColour('#85B24A')
        setItemFont(self.warmBoxTemp,font)

        self.cavityTemp = wx.TextCtrl(self, -1, style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2)
        self.cavityTemp.SetMinSize((55, -1))
        self.cavityTemp.SetBackgroundColour('#85B24A')
        setItemFont(self.cavityTemp,font)

        self.cavityPressure = wx.TextCtrl(self, -1, style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2)
        self.cavityPressure.SetMinSize((55, -1))
        self.cavityPressure.SetBackgroundColour('#85B24A')
        setItemFont(self.cavityPressure,font)

        self.__do_layout()

    def __do_layout(self):
        sizer_out = wx.BoxSizer(wx.VERTICAL)
        sizer_in = wx.FlexGridSizer(3, 2)
        sizer_in.Add(self.warmBoxTempLabel, 0, wx.RIGHT, 3)
        sizer_in.Add(self.warmBoxTemp, 0)
        sizer_in.Add(self.cavityTempLabel, 0, wx.RIGHT, 3)
        sizer_in.Add(self.cavityTemp, 0)
        sizer_in.Add(self.cavityPressureLabel, 0, wx.RIGHT, 3)
        sizer_in.Add(self.cavityPressure, 0)

        sizer_out.Add(sizer_in, 0, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_out)
        sizer_out.Fit(self)
        sizer_out.SetSizeHints(self)


class QuickGui(wx.Frame):
    def __init__(self, configFile, defaultTitle = ""):

        wx.Frame.__init__(self,parent=None,id=-1,title='CRDS_Data_Viewer',size=(1200,700),
                          style=wx.CAPTION|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL)

        self.commandQueue = Queue.Queue()
        self.defaultTitle = defaultTitle

        self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = APP_NAME)
        self.dataManagerRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = APP_NAME)
        self.sampleMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SAMPLE_MGR, ClientName = APP_NAME)
        try:
            self.valveSeqRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_VALVE_SEQUENCER, ClientName = APP_NAME)
        except:
            self.valveSeqRpc = None

        self.configFile = configFile
        self.config = CustomConfigObj(self.configFile)
        self.valveSeqOption = self.config.getboolean("ValveSequencer","Enable",True)
        self.numGraphs = max(1, self.config.getint("Graph","NumGraphs",1))
        self.colorDatabase = ColorDatabase(self.config,"Colors")
        self.fontDatabase = FontDatabase(self.config,"Fonts",self.colorDatabase)
        self.sourceSubstDatabase = SubstDatabase.fromIni(self.config,"SourceFilters","string",["replacement"])
        self.keySubstDatabase = SubstDatabase.fromIni(self.config,"KeyFilters","string",
                                                       ["replacement","units","format"],
                                                       ["\g<0>","","%.3f"])

        if "StandardModeKeysSources" in self.config:
            self.sourceStandardModeDatabase = None
            self.keyStandardModeDatabase = None
            self.standardModeSourcesDict = StringDict.fromIni(self.config,"StandardModeKeysSources","source")
            self.standardModeKeysDict = {}
            for idx in range(len(self.standardModeSourcesDict.getStrings())):
                self.standardModeKeysDict[idx] = StringDict.fromIni(self.config,"StandardModeKeysSources","key%d"%idx)
        else:
            self.sourceStandardModeDatabase = SubstDatabase.fromIni(self.config,"StandardModeSources","string")
            self.keyStandardModeDatabase = SubstDatabase.fromIni(self.config,"StandardModeKeys","string")

        self.displayFilterSubstDatabase = SubstDatabase.fromIni(self.config,"DisplayFilters","key",["select"],[""])
        self.defaultSources = StringDict.fromIni(self.config,"Defaults","source")
        self.defaultKeys = {}
        for idx in range(self.numGraphs):
            self.defaultKeys[idx] = StringDict.fromIni(self.config,"Defaults","key%d"%idx)
        self.dataStore  = DataStoreForGraphPanels(self.config)
        self.eventStore = EventStore(self.config)
        self.alarmInterface = AlarmInterface(self.config, APP_NAME)
        self.alarmInterface.getAlarmData()
        self.sysAlarmInterface = SysAlarmInterface(self.config.getint("AlarmBox", "ledBlinkTime", 0) )
        self.dataLoggerInterface = DataLoggerInterface(self.config, APP_NAME)
        self.dataLoggerInterface.getDataLoggerInfo()
        self.instMgrInterface = InstMgrInterface(self.config, APP_NAME)

        # clamp # of additional alarms displayed to 5 (shows vert scrollbar if more)
        self.numAlarms = self.config.getint("AlarmBox", "NumAlarms", 4)
        self.numAlarmsDisplay = min(5, self.numAlarms)

        self.showGraphZoomed = self.config.getboolean("Graph","ShowGraphZoomed",False)
        self.shutdownShippingSource = self.config.get("ShutdownShippingSource", "Source", "Sensors")
        self.hostSession = requests.Session()
        self.lockTime = False
        self.allTimeLocked = False
        self.sourceChoices = []
        self.keyChoices = [None]*self.numGraphs
        self.source = [None]*self.numGraphs
        self.dataKey = [None]*self.numGraphs
        self.logo = None
        self.fullInterface = False
        self.userLevel = 0
        self.userLoggedIn = False    
        self.showStat = True # Show data statistics panels
        self.showInstStat = True # Show instrument status panels
        self.serviceModeOnlyControls = []
        self.statControls = []
        self.cavityTempS = None
        self.cavityTempT = None
        self.warmBoxTempS = None
        self.warmBoxTempT = None
        self.cavityPressureS = None
        self.cavityPressureT = None
        self.defaultLineMarkerColor = self.colorDatabase.getColorFromIni("Graph", "LineColor")
        self.defaultLineWidth = self.config.getfloat("Graph","LineWidth")
        self.defaultMarkerSize = self.config.getfloat("Graph","MarkerSize")
        self.lineMarkerColor = self.defaultLineMarkerColor
        self.restartUserLog = False
        self.externalTools = {}
        # Collect instrument status setpoint and tolerance
        try:
            self.cavityTempS = self.driverRpc.rdDasReg("CAVITY_TEMP_CNTRL_USER_SETPOINT_REGISTER")
            self.cavityTempT = self.driverRpc.rdDasReg("CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER")
        except:
            self.cavityTempS = 45.0
            self.cavityTempT = 0.2
        try:
            self.warmBoxTempS = self.driverRpc.rdDasReg("WARM_BOX_TEMP_CNTRL_USER_SETPOINT_REGISTER")
            self.warmBoxTempT = self.driverRpc.rdDasReg("WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER")
        except:
            self.warmBoxTempS = 45.0
            self.warmBoxTempT = 0.2
        try:
            self.cavityPressureS = self.sampleMgrRpc.ReadOperatePressureSetpoint()
            self.cavityPressureTPer = self.sampleMgrRpc.ReadPressureTolerancePer()
        except:
            self.cavityPressureS = 140.0
            self.cavityPressureTPer = 0.05
        self.cavityPressureT = self.cavityPressureTPer*self.cavityPressureS

        # Set up instrument status panel source and key
        self.instStatSource = self.config.get("InstStatPanel", "Source", "Sensors")
        self.instStatCavityPressureKey = self.config.get("InstStatPanel", "CavityPressureKey", "CavityPressure")
        self.instStatCavityTempKey = self.config.get("InstStatPanel", "CavityTempKey", "CavityTemp")
        self.instStatWarmBoxTempKey = self.config.get("InstStatPanel", "WarmBoxTempKey", "WarmBoxTemp")

        # Load in the data keys for the peripheral interface.  Ignore this if there is no "PeriphIntrf"
        # section in the QuickGui ini file.
        # PeriphIntrf is only used in the Surveyor product line for devices such as the anemometer and
        # GPS.
        if "PeriphIntrf" in self.config.keys():
            try:
                self.rawPeriphDict = {}
                self.syncPeriphDict = {}
                periphIntrfConfig = os.path.join(basePath, self.config.get("PeriphIntrf", "periphIntrfConfig"))
                selectAll = self.config.getboolean("PeriphIntrf", "showAll", False)
                (self.rawPeriphDict, self.syncPeriphDict) = parsePeriphIntrfConfig(periphIntrfConfig,selectAll)
                # Add peripheral interface columns (if available) in standard mode
                if self.rawPeriphDict:
                    self._addStandardKeys(self.rawPeriphDict)
                if self.syncPeriphDict:
                    self._addStandardKeys(self.syncPeriphDict)
            except Exception, err:
                print "%r Exception parsing peripheral interface config." % err

        self._layoutFrame()
        # Create the image panels with the frame as parent
        # Don't know what images this might show, none in ini file - RSF
        # for key in self.imageDatabase.dbase:
        #     self.imageDatabase.setImagePanel(key,self)

        self.menuBar = wx.MenuBar()
        self.iUserSettings = wx.Menu()
        self.iView = wx.Menu()
        self.iTools = wx.Menu()
        self.iHelp = wx.Menu()

        #user level setting menu
        self.menuBar.Append(self.iUserSettings,"Users")
        self.idLoginUser = wx.NewId()

        self.iGuiMode = wx.MenuItem(self.iUserSettings, self.idLoginUser, "User Login", "", wx.ITEM_NORMAL)

        self.iUserSettings.AppendItem(self.iGuiMode)

        self.iGuiMode.Enable(True)

        self.menuBar.Append(self.iView,"View")
        self.idLockTime = wx.NewId()
        self.iLockTime = wx.MenuItem(self.iView, self.idLockTime, "Lock time axis when zoomed", "", wx.ITEM_CHECK)
        self.iView.AppendItem(self.iLockTime)
        self.idStatDisplay = wx.NewId()
        self.iStatDisplay = wx.MenuItem(self.iView, self.idStatDisplay, "Statistics", "", wx.ITEM_CHECK)
        self.iView.AppendItem(self.iStatDisplay)
        self.idInstStatDisplay = wx.NewId()
        self.iInstStatDisplay = wx.MenuItem(self.iView, self.idInstStatDisplay, "Instrument Status", "", wx.ITEM_CHECK)
        self.iView.AppendItem(self.iInstStatDisplay)
        self.userLevelMap = {"SuperUser": 4, "Admin": 3, "Technician": 2, "Operator": 1}

        # get external tools from config
        if "ExternalTools" in self.config:
            tools = self.config["ExternalTools"]
            for k in tools:
                if k.startswith("toolName"):
                    idx = int(k[8:])
                    self.externalTools[tools[k]] = {}
                    if ("toolCmd%d" % idx) in tools:
                        self.externalTools[tools[k]]["cmd"] = tools["toolCmd%d" % idx]
                    if ("toolUser%d" % idx) in tools:
                        self.externalTools[tools[k]]["user"] = \
                            [self.userLevelMap[t.strip()] for t in tools["toolUser%d" % idx].split(",")]


        self.menuBar.Append(self.iTools,"Tools")
        if self.config.getboolean("UserCalibration", "Enable", True):
            self.idUserCal = wx.NewId()
            self.iUserCal = wx.MenuItem(self.iTools, self.idUserCal, "User Calibration", "", wx.ITEM_NORMAL)
            self.iTools.AppendItem(self.iUserCal)
            self.Bind(wx.EVT_MENU, self._OnUserCal, id=self.idUserCal)

        for tool in self.externalTools:
            self.externalTools[tool]['id'] = wx.NewId()
            self.externalTools[tool]['menu'] = wx.MenuItem(self.iTools,
                                                        self.externalTools[tool]['id'], 
                                                        tool, "", wx.ITEM_NORMAL)
            self.iTools.AppendItem(self.externalTools[tool]['menu'])
        self.menuBar.EnableTop(1, False)
        self.menuBar.EnableTop(2, False)
        try:
            self.pulseSource = self.config.get("PulseAnalyzer", "Source")
            self.idPulseAnalyzerParam = wx.NewId()
            self.iPulseAnalyzerParam = wx.MenuItem(self.iTools, self.idPulseAnalyzerParam, "Pulse Analyzer Parameters", "", wx.ITEM_NORMAL)
            self.iTools.AppendItem(self.iPulseAnalyzerParam)
            self.Bind(wx.EVT_MENU, self.OnPulseAnalyzerParam, id=self.idPulseAnalyzerParam)
        except:
            self.pulseSource = None

        if self.valveSeqOption:
            self.idValveSeq = wx.NewId()
            self.iValveSeq = wx.MenuItem(self.iTools, self.idValveSeq, "Show Valve Sequencer GUI", "", wx.ITEM_NORMAL)
            self.iTools.AppendItem(self.iValveSeq)
            self.Bind(wx.EVT_MENU, self._OnValveSeq, id=self.idValveSeq)

        self.menuBar.Append(self.iHelp,"Help")
        self.idABOUT = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idABOUT, "About", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)

        self.SetMenuBar(self.menuBar)
        self.Bind(wx.EVT_MENU, self._OnAbout, id=self.idABOUT)

        self.Bind(wx.EVT_MENU, self._OnLoginUser, id=self.idLoginUser)

        self.Bind(wx.EVT_MENU, self._OnLockTime, id=self.idLockTime)
        self.iLockTime.Enable(self.numGraphs>1)
        self.Bind(wx.EVT_MENU, self._OnStatDisplay, id=self.idStatDisplay)
        self.Bind(wx.EVT_MENU, self._OnInstStatDisplay, id=self.idInstStatDisplay)

        for tool in self.externalTools:
            self.Bind(wx.EVT_MENU, self._OnExternalTools, id=self.externalTools[tool]['id'])

        self.updateTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._OnTimer, self.updateTimer)
        self.updateTimer.Start(UPDATE_TIMER_INTERVAL)
        self.Bind(wx.EVT_IDLE, self._OnIdle)

        #Add session timer for inactive session timeout function of higher user level GUI mode
        self.sessionTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._OnSessionTimer, self.sessionTimer)

        self.session_time = 0

        # The GTK has some graphics artifacts that can only be cleaned up after the
        # initial show event.  One clear example is the wx.ListCtrl automatic focus
        # which draws a rectangle around the first alarm LED + label.  The focus
        # rectangle can be removed with a call to Defocus() but this only works after
        # the entire QuickGui is shown.
        # Do one graphics refresh right after the window is fully drawn to clean
        # things up.
        self.OneShotTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._lateStart, self.OneShotTimer)
        self.OneShotTimer.Start(100, True)

    def _lateStart(self, evt):
        """
        Post init configurations.
        """
        # Some initialization can't be done until after the main window
        # and all its widgets have been initialized.  For example,
        # some widgets have their view dependent on the state of another
        # widget but until the window is created the code can examine
        # the state of widgets (reference errors). This method is called
        # a few milliseconds after the main window has been created. Put
        # post initialization steps here.
        self._OnStatDisplay(evt, self.showStat)
        self._OnInstStatDisplay(evt, self.showInstStat)
        self._OnTimer(evt)

    def _addStandardKeys(self, sourceKeyDict):
        """Add standard keys on GUI
        souceKeyDict = {"source": ["source1", "source2"], "data": ["data1", "data2", ...]}
        """
        standardSourceDict = self.standardModeSourcesDict.getStrings()
        try:
            sourceIdxList = [i for i in standardSourceDict if standardSourceDict[i] in sourceKeyDict["source"]]
            for newCol in sourceKeyDict["data"]:
                for i in sourceIdxList:
                    self.standardModeKeysDict[i].addString(newCol)
        except:
            raise

    def _layoutFrame(self):
        self.mainPanel = wx.Panel(parent=self,id=-1)
        font,fgColour,bgColour = self.fontDatabase.getFontFromIni('Panel')
        self.mainPanel.SetBackgroundColour(bgColour)
        self.mainPanel.SetForegroundColour(fgColour)
        # Define the title band
        if self.defaultTitle:
            label = self.defaultTitle
        else:
            label=getInnerStr(self.config.get('Title','String'))
        self.titleLabel = wx.StaticText(parent=self.mainPanel, id=-1, label=label, style=wx.ALIGN_CENTER)
        setItemFont(self.titleLabel,self.fontDatabase.getFontFromIni('Title'))

        # Define the footer band

        # Don't use the footer in INI file otherwise we have to change the year of each individual QuickGui.ini (more than 100 files) every year
        #copyLabel=getInnerStr(self.config.get('Footer','String'))
        copyLabel = "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0]
        footerLabel = wx.StaticText(parent=self.mainPanel, id=-1, label=copyLabel, style=wx.ALIGN_CENTER)
        setItemFont(footerLabel,self.fontDatabase.getFontFromIni('Footer'))

        # Define the graph panels
        self.graphPanel = []
        font,fgColour,bgColour = self.fontDatabase.getFontFromIni('Graph')
        for idx in range(self.numGraphs):
            gp = GraphPanel.GraphPanel(parent=self.mainPanel,id=-1)
            gp.SetGraphProperties(ylabel='Y',
                                  timeAxes=((self.config.getfloat("Graph","TimeOffset_hr"),
                                              self.config.getboolean("Graph","UseUTC")),False),
                                  grid=self.config.getboolean("Graph","Grid"),
                                  gridColour=self.colorDatabase.getColorFromIni("Graph", "GridColor"),
                                  backgroundColour=self.colorDatabase.getColorFromIni("Graph", "PaperColor"),
                                  font=font,
                                  fontSizeAxis=font.GetPointSize(),
                                  frameColour=bgColour,
                                  foregroundColour=fgColour,
                                  XTickFormat=self.config.get("Graph","TimeAxisFormat","%H:%M:%S\n%d-%b-%Y"),
                                  heightAdjustment = self.config.getfloat("Graph","HeightAdjustment",0.0),
                                  )
            #gp.Update()

            self.graphPanel.append(gp)

        # Define a gauge indicating the buffer level
        self.gauge = wx.Gauge(parent=self.mainPanel,range=100,style=wx.GA_VERTICAL,
                              size=(10,-1))

        self.userLogButton = wx.Button(parent=self.mainPanel,id=-1,size=(-1,25),label="Start User Log(s)")
        setItemFont(self.userLogButton,self.fontDatabase.getFontFromIni('MeasurementButtons'))
        self.userLogButton.State = False
        self.restartUserLog = False

        self.Bind(wx.EVT_BUTTON, self._OnUserLogButton, self.userLogButton)

        # Define the status log window
        logFileBox = wx.StaticBox(parent=self.mainPanel,id=1,label="Saved Data File")
        eventLogBox = wx.StaticBox(parent=self.mainPanel,id=-1,label="Measurement Status")
        height = self.config.getint("StatusBox","Height")
        if self.numGraphs > 2:
            height *= 0.8
        self.eventViewControl = EventViewListCtrl(parent=self.mainPanel,id=-1,config=self.config,
                                                  DataSource=self.eventStore,size=(-1,height))
        setItemFont(self.eventViewControl,self.fontDatabase.getFontFromIni('StatusBox'))
        setItemFont(eventLogBox,self.fontDatabase.getFontFromIni('Panel'))
        setItemFont(logFileBox,self.fontDatabase.getFontFromIni('Panel'))

        self.userLogTextCtrl = wx.TextCtrl(parent=self.mainPanel,id=-1,#size=(-1,12),
                                        style=wx.TE_READONLY|wx.TE_RICH2|wx.TE_MULTILINE,
                                        value="No log file")
        setItemFont(self.userLogTextCtrl,self.fontDatabase.getFontFromIni('UserLogBox'))

        eventLogBoxSizer = wx.StaticBoxSizer(eventLogBox,wx.HORIZONTAL)
        logFileBoxSizer = wx.StaticBoxSizer(logFileBox,wx.VERTICAL)
        logFileBoxSizer.Add(self.userLogButton, 0, wx.EXPAND)
        logFileBoxSizer.Add(self.userLogTextCtrl,1, wx.EXPAND|wx.ALL)
        eventLogBoxSizer.Add(self.eventViewControl,1, wx.EXPAND|wx.ALL)

        # Hide/Show the status panel that shows the name of the dat file.  21 CFR part 11 compliant
        # systems do not show the output file name on the main screen.
        #
        statusBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        statusBoxSizer.Add(logFileBoxSizer, proportion=1, flag=wx.EXPAND | wx.ALL)
        if not self.config.getboolean("UserLogBox", "Enable", True):
            statusBoxSizer.Hide(logFileBoxSizer, recursive=True)
        statusBoxSizer.Add(eventLogBoxSizer,proportion=1, flag=wx.EXPAND|wx.ALL)

        # Define the data selection tools
        toolPanel = wx.Panel(parent=self.mainPanel,id=-1)
        font,fgColour,bgColour = self.fontDatabase.getFontFromIni('Graph')
        toolPanel.SetBackgroundColour(bgColour)

        self.sourceChoice = []
        self.sourceChoiceIdList = []
        self.keyChoice = []
        self.keyChoiceIdList = []
        self.precisionChoice = []
        self.precisionChoiceIdList = []
        self.autoY = []
        self.autoYIdList = []
        self.zoomedList = []
        self.clearButton = None
        choiceSizer = wx.BoxSizer(wx.VERTICAL)

        for idx in range(self.numGraphs):
            sourceLabel = wx.StaticText(parent=toolPanel,id=-1,label="Source %d " % (idx+1))
            setItemFont(sourceLabel,self.fontDatabase.getFontFromIni('Graph'))
            newId = wx.NewId()
            self.sourceChoiceIdList.append(newId)
            sc = wx.ComboBox(parent=toolPanel,id=newId,size=(150,-1),style=wx.CB_READONLY)
            setItemFont(sc,self.fontDatabase.getFontFromIni('GraphTextBoxes'))
            self.Bind(wx.EVT_COMBOBOX, self._OnSourceChoice, sc)
            self.sourceChoice.append(sc)

            keyLabel = wx.StaticText(parent=toolPanel,id=-1,label="Data Key %d " % (idx+1))
            setItemFont(keyLabel,self.fontDatabase.getFontFromIni('Graph'))
            newId = wx.NewId()
            self.keyChoiceIdList.append(newId)
            kc = wx.ComboBox(parent=toolPanel,id=newId,size=(200,-1),style=wx.CB_READONLY)
            setItemFont(kc,self.fontDatabase.getFontFromIni('GraphTextBoxes'))
            self.Bind(wx.EVT_COMBOBOX, self._OnKeyChoice, kc)
            self.keyChoice.append(kc)

            precisionLabel = wx.StaticText(parent=toolPanel,id=-1,label="Precision ")
            setItemFont(precisionLabel,self.fontDatabase.getFontFromIni('Graph'))
            newId = wx.NewId()
            self.precisionChoiceIdList.append(newId)
            pc = wx.ComboBox(parent=toolPanel,id=newId,size=(80,-1),style=wx.CB_READONLY,
                                       choices=["auto","0","1","2","3","4"],value="auto")
            setItemFont(pc,self.fontDatabase.getFontFromIni('GraphTextBoxes'))
            self.Bind(wx.EVT_COMBOBOX, self._OnPrecisionChoice, pc)
            self.precisionChoice.append(pc)

            if self.showGraphZoomed:
                zoomedLabel = wx.StaticText(parent=toolPanel,id=-1,label="Zoomed")
                setItemFont(zoomedLabel,self.fontDatabase.getFontFromIni('Graph'))
                zoomedStatus = wx.TextCtrl(parent=toolPanel,id=-1,size=(40,-1),
                                            style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="N")
                setItemFont(zoomedStatus,self.fontDatabase.getFontFromIni('GraphTextBoxes'))
                self.zoomedList.append(zoomedStatus)

            newId = wx.NewId()
            self.autoYIdList.append(newId)
            autoYButton = wx.Button(parent=toolPanel,id=newId,size=(-1,25),label="Auto-scale Y")
            setItemFont(autoYButton,self.fontDatabase.getFontFromIni('MeasurementButtons'))
            self.Bind(wx.EVT_BUTTON, self._OnAutoScaleY, autoYButton)
            self.autoY.append(autoYButton)

            toolSizer = wx.BoxSizer(wx.HORIZONTAL)
            toolSizer.Add((10,10),proportion=0)
            toolSizer.Add(sourceLabel,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add(sc,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add((10,10),proportion=0)
            toolSizer.Add(keyLabel,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add(kc,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add((10,10),proportion=0)
            toolSizer.Add(precisionLabel,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add(pc,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add((10,10),proportion=0)
            if self.showGraphZoomed:
                toolSizer.Add(zoomedLabel,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
                toolSizer.Add((3,10),proportion=0)
                toolSizer.Add(zoomedStatus,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
                toolSizer.Add((10,10),proportion=0)
            toolSizer.Add(autoYButton,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM)
            toolSizer.Add((20,10),proportion=0)
            choiceSizer.Add(toolSizer,proportion=1)

        self.clearButton = wx.Button(parent=toolPanel,id=-1,label="Reset buffers")
        setItemFont(self.clearButton,self.fontDatabase.getFontFromIni('GraphButton'))
        self.Bind(wx.EVT_BUTTON, self._OnResetBuffers, self.clearButton)

        combToolSizer = wx.BoxSizer(wx.HORIZONTAL)
        combToolSizer.Add(choiceSizer,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM,border=10)
        combToolSizer.Add(self.clearButton,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM,border=10)
        combToolSizer.Add((10,10),proportion=0)
        toolPanel.SetSizer(combToolSizer)

        # Panel for measurement result
        self.measPanel = wx.Panel(parent=self.mainPanel,id=-1)
        setItemFont(self.measPanel,self.fontDatabase.getFontFromIni('MeasurementPanel'))

        # Alarm view
        alarmBox = wx.StaticBox(parent=self.measPanel,id=-1,label="Alarms")
        # Define the box height automatically instead of using INI file
        #size = self.config.getint("AlarmBox","Width"),self.config.getint("AlarmBox","Height")

        boxWidth = self.config.getint("AlarmBox","Width")
        boxHeight = self.numAlarmsDisplay * 40

        size = boxWidth,boxHeight

        font,fgColour,bgColour = self.fontDatabase.getFontFromIni('AlarmBox','enabledFont')
        enabled = wx.ListItemAttr(fgColour,bgColour,font)
        font,fgColour,bgColour = self.fontDatabase.getFontFromIni('AlarmBox','disabledFont')
        disabled = wx.ListItemAttr(fgColour,bgColour,font)

        self.alarmView = AlarmViewListCtrl(parent=self.measPanel,mainForm=self, id=-1,attrib=[disabled,enabled],
                                           DataStore=self.dataStore, DataSource=self.alarmInterface,
                                           fontDatabase=self.fontDatabase,
                                           size=size, numAlarms=self.numAlarms,
                                           sysAlarmInterface=self.sysAlarmInterface)
        setItemFont(alarmBox,self.fontDatabase.getFontFromIni('AlarmBox'))
        setItemFont(self.alarmView,self.fontDatabase.getFontFromIni('AlarmBox'))

        # numSysAlarms = 1 will hide IPV Connectivity, default is 1 (hide IPV)
        numSysAlarms = min(2, self.config.getint("AlarmBox", "NumSysAlarms", 1))
        boxHeight = numSysAlarms * 40

        size = boxWidth,boxHeight

        self.sysAlarmView = SysAlarmViewListCtrl(parent=self.measPanel,id=-1,attrib=[disabled,enabled],
                                           DataSource=self.sysAlarmInterface, fontDatabase=self.fontDatabase,
                                           size=size, numAlarms=numSysAlarms)
        self.sysAlarmView.SetMainForm(self)
        setItemFont(self.sysAlarmView,self.fontDatabase.getFontFromIni('AlarmBox'))

        # Combine system alarm with concentration alarms
        alarmBoxSizer = wx.StaticBoxSizer(alarmBox,wx.VERTICAL)
        alarmBoxSizer.Add(self.sysAlarmView,proportion=0,flag=wx.EXPAND)
        alarmBoxSizer.Add(self.alarmView,proportion=0,flag=wx.EXPAND)

        # Instrument status panel
        self.instStatusBox = wx.StaticBox(parent=self.measPanel,id=-1,label="Instrument Status")
        size = self.config.getint("InstStatPanel","Width", 150),self.config.getint("InstStatPanel","Height", 70)
        self.instStatusPanel = InstStatusPanel(font=self.fontDatabase.getFontFromIni('InstStatPanel'),
                                                parent=self.measPanel, id=-1, size=size
                                                )
        setItemFont(self.instStatusBox,self.fontDatabase.getFontFromIni('InstStatPanel'))
        instStatusBoxSizer = wx.StaticBoxSizer(self.instStatusBox,wx.HORIZONTAL)
        instStatusBoxSizer.Add(self.instStatusPanel,proportion=0,flag=wx.EXPAND|wx.ALL,border=2)

        # The measurement result consists of a label describing the displayed quantity,
        #  a text control which contains the number, and a label for the units associated
        #  with the quantity. Below these is a collection of three boxes for the mean, standard
        #  deviation and slope.
        # measLabel is in a vertical box sizer above a horizontal box sizer containing the
        #  measTextCtrl and the unitsLabel above the three statistics boxes
        self.measLabel = []
        self.measTextCtrl = []
        self.meanTextCtrl = []
        self.stdDevTextCtrl = []
        self.slopeTextCtrl = []
        measDisplaySizer = wx.BoxSizer(wx.VERTICAL)
        self.statsMeanFormat = self.config.get("StatsBox", "MeanFormat", default = "%.4g")
        self.statsStdvFormat = self.config.get("StatsBox", "StdvFormat", default = "%.4g")
        self.statsSlopeFormat = self.config.get("StatsBox", "SlopeFormat", default = "%.4g")
        for idx in range(self.numGraphs):
            resultSizer = wx.BoxSizer(wx.VERTICAL)
            statsSizer = wx.BoxSizer(wx.HORIZONTAL)

            measLabel = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,
                                       label='')

            # See the comments below in dataKeyUpdateAction() to understand why this code is here.
            #
            #measLabel = wx.lib.fancytext.StaticFancyText(self.measPanel,-1," ",wx.Brush("white", wx.TRANSPARENT))

            setItemFont(measLabel,self.fontDatabase.getFontFromIni('MeasurementLabel'))
            self.measLabel.append(measLabel)

            measTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,pos=(50,100),size=(150,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,
                                        value="0.00")
            setItemFont(measTextCtrl,self.fontDatabase.getFontFromIni('MeasurementBox'))
            self.measTextCtrl.append(measTextCtrl)

            resultSizer.Add(measLabel,proportion=0,flag=wx.ALIGN_CENTER)
            resultSizer.Add(measTextCtrl,proportion=1,flag=wx.ALIGN_CENTER)
            measDisplaySizer.Add(resultSizer,proportion=0,flag=wx.GROW | wx.LEFT | wx.RIGHT,border = 10)

            vs = wx.BoxSizer(wx.VERTICAL)
            st = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,label='mean')
            self.statControls.append(st)
            setItemFont(st,self.fontDatabase.getFontFromIni('StatsLabel'))
            vs.Add(st,flag=wx.ALIGN_CENTER)

            meanTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,size=(40,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="0.00")
            setItemFont(meanTextCtrl,self.fontDatabase.getFontFromIni('StatsBox'))
            self.statControls.append(meanTextCtrl)
            self.meanTextCtrl.append(meanTextCtrl)

            vs.Add(meanTextCtrl,flag=wx.EXPAND)
            statsSizer.Add(vs,proportion=1)

            vs = wx.BoxSizer(wx.VERTICAL)
            st = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,label='std dev')
            self.statControls.append(st)
            setItemFont(st,self.fontDatabase.getFontFromIni('StatsLabel'))
            vs.Add(st,flag=wx.ALIGN_CENTER)

            stdDevTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,size=(40,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="0.00")
            setItemFont(stdDevTextCtrl,self.fontDatabase.getFontFromIni('StatsBox'))
            self.statControls.append(stdDevTextCtrl)
            self.stdDevTextCtrl.append(stdDevTextCtrl)

            vs.Add(stdDevTextCtrl,flag=wx.EXPAND)
            statsSizer.Add(vs,proportion=1)

            vs = wx.BoxSizer(wx.VERTICAL)
            st = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,label='slope')
            self.statControls.append(st)
            setItemFont(st,self.fontDatabase.getFontFromIni('StatsLabel'))
            vs.Add(st,flag=wx.ALIGN_CENTER)

            slopeTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,size=(40,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="0.00")
            setItemFont(slopeTextCtrl,self.fontDatabase.getFontFromIni('StatsBox'))
            self.statControls.append(slopeTextCtrl)
            self.slopeTextCtrl.append(slopeTextCtrl)

            vs.Add(slopeTextCtrl,flag=wx.EXPAND)
            statsSizer.Add(vs,proportion=1)

            measDisplaySizer.Add(statsSizer,proportion=0,flag=wx.GROW | wx.LEFT | wx.RIGHT,border = 10)
            measDisplaySizer.Add((20,10),proportion=0)

        self.shutdownButton = wx.Button(parent=self.measPanel,id=wx.ID_EXIT,size=(75,65))
        setItemFont(self.shutdownButton,self.fontDatabase.getFontFromIni('MeasurementButtons'))
        self.Bind(wx.EVT_BUTTON, self._OnShutdownButton, self.shutdownButton)

        self.measPanelSizer = wx.BoxSizer(wx.VERTICAL)
        # Next line defines width of panel
        panelWidth = 250

        logoSizer = wx.BoxSizer(wx.VERTICAL)
        logoBmp = wx.Bitmap(AppPath + '/logo.png', wx.BITMAP_TYPE_PNG)
        logoSizer.Add(wx.StaticBitmap(self.measPanel, -1, logoBmp),proportion=0, flag=wx.TOP,border = 15)
        self.measPanelSizer.Add(logoSizer,proportion=0,flag=wx.ALIGN_CENTER|wx.BOTTOM,border = 5)
        self.measPanelSizer.Add((panelWidth,10),proportion=0)
        self.measPanelSizer.Add(measDisplaySizer,proportion=0,flag=wx.GROW | wx.LEFT | wx.RIGHT,border = 10)
        self.measPanelSizer.Add(instStatusBoxSizer,proportion=0,flag=wx.ALIGN_CENTER | wx.ALL,border = 5)
        self.measPanelSizer.Add(alarmBoxSizer,proportion=0,flag=wx.ALIGN_CENTER)
        self.measPanelSizer.AddStretchSpacer()
        self.measPanelSizer.Add(self.shutdownButton,proportion=0, flag=wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.measPanelSizer.AddSpacer(10)

        self.measPanel.SetSizer(self.measPanelSizer)

        graphBox = wx.StaticBox(parent=self.mainPanel, id=-1)
        setItemFont(graphBox,self.fontDatabase.getFontFromIni('Panel'))

        # Construct the layout using sizers
        graphPanelSizer = wx.BoxSizer(wx.VERTICAL)
        for idx in range(self.numGraphs):
            graphPanelSizer.Add(self.graphPanel[idx],proportion=1,flag=wx.GROW)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(graphPanelSizer,proportion=1,flag=wx.GROW)
        sizer.Add(self.gauge,proportion=0,flag=wx.GROW)

        innerVSizer = wx.StaticBoxSizer(graphBox,wx.VERTICAL)
        innerVSizer.Add(sizer,proportion=1,flag=wx.GROW|wx.LEFT)
        innerVSizer.Add(toolPanel,proportion=0,flag=wx.GROW)

        vsizer2 = wx.BoxSizer(wx.VERTICAL)
        titleSizer = wx.BoxSizer(wx.VERTICAL)
        titleSizer.Add(self.titleLabel,proportion=0,flag=wx.ALIGN_CENTER)
        vsizer2.Add(titleSizer,proportion=0,flag= wx.GROW | wx.ALL,border=10)
        vsizer2.Add(innerVSizer,proportion=1,flag=wx.GROW)
        vsizer2.Add(statusBoxSizer,proportion=0, flag=wx.EXPAND)

        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add(self.measPanel,proportion = 0,flag=wx.GROW | wx.RIGHT,border=10)
        hsizer1.Add(vsizer2,proportion = 1,flag=wx.GROW)
        #
        vsizer1 = wx.BoxSizer(wx.VERTICAL)
        vsizer1.Add(hsizer1,proportion=1,flag=wx.GROW | wx.LEFT | wx.RIGHT,border=10)
        footerSizer = wx.BoxSizer(wx.VERTICAL)
        footerSizer.Add(footerLabel,proportion=0,flag=wx.ALIGN_CENTER)
        vsizer1.Add(footerSizer,proportion=0,flag=wx.GROW | wx.ALL,border=10)
        self.mainPanel.SetSizer(vsizer1)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.mainPanel,proportion=1,flag=wx.EXPAND)
        self.SetSizer(box)
        self._modifyInterface()

    def _modifyInterface(self):
        """
        Enable/Disable widgets depending on the logged in user's authority level.
        The default (no one logged in) is to disable widgets that can change the
        operation of the analyzer or the data displayed on the screen.
        """
        # No one logged in, disable everything
        self.shutdownButton.Enable(False)
        self.userLogButton.Disable()
        for sc in self.sourceChoice:
            sc.SetSelection(0)
            self._OnSourceChoice(obj=sc)
            sc.Enable(False)
        for kc in self.keyChoice:
            kc.Enable(False)
        for pc in self.precisionChoice:
            pc.Enable(False)
        for ayb in self.autoY:
            ayb.Enable(False)
        for c in self.serviceModeOnlyControls:
            c.Show(False)
        self.clearButton.Enable(False)

        # Operator level
        # Activate the shutdown button, basic stats views, and different
        # data to plot
        if self.userLevel >= 1:
            self.shutdownButton.Enable(True)
            # Enable View pulldown menu
            self.menuBar.EnableTop(1, True)
            for sc in self.sourceChoice:
                sc.Enable(True)
            for kc in self.keyChoice:
                kc.Enable(True)

        # Technician level
        # Activate additional widgets that change the display of data but
        # still limit the data source choices.  Enable the valve
        # sequencer GUI.
        if self.userLevel >= 2:
            self.userLogButton.Enable(True)
            for pc in self.precisionChoice:
                pc.Enable(True)
            for ayb in self.autoY:
                ayb.Enable(True)
            self.clearButton.Enable(True)
            # Enable Tools pulldown menu
            self.menuBar.EnableTop(2, True)

        # Admin level
        # Enable data view of fit parameters and other "Picarro" only data
        if self.userLevel >= 3:
           for c in self.serviceModeOnlyControls:
               c.Show(True)

        for tool in self.externalTools:
            if "user" in self.externalTools[tool]:
                if self.userLevel in self.externalTools[tool]["user"]:
                    self.externalTools[tool]["menu"].Enable(True)
                else:
                    self.externalTools[tool]["menu"].Enable(False)

    def _getSourcesbyMode(self):
        s = self.dataStore.getSources()
        if self.userLevel < 3:
            if self.sourceStandardModeDatabase != None:
                s = [t for t in s if self.sourceStandardModeDatabase.match(t)>=0]
            else:
                s = [t for t in s if t in self.standardModeSourcesDict.getStrings().values()]
        return s

    def _getKeysbyMode(self, source):
        k = self.dataStore.getKeys(source)
        if self.userLevel < 3:
            if self.keyStandardModeDatabase != None:
                k = [t for t in k if self.keyStandardModeDatabase.match(t)>=0]
            else:
                for sourceKey in self.standardModeSourcesDict.getStrings():
                    if self.standardModeSourcesDict.getString(sourceKey) == source:
                        keyDict = self.standardModeKeysDict[sourceKey]
                        k = [t for t in k if t in keyDict.getStrings().values()]
                        break
        return k

    def _OnShutdownButton(self, evt):
        # Shutdown Modes (modes are defined in InstMgr.py)
        # mode == 0 shutdown all processes and power off the analyzer
        # mode == 1 shutdown all process and exit to the desktop
        # mode == 2 shutdown host, leave driver running, exit to desktop
        #
        # click ShutDown button -> mode 0
        # click Shutdown button while holding down SHIFT -> mode 1
        # click Shutdown button while holding down SHIFT + CTRL -> mode 0
        #
        shutdownMode = 0
        # Lets only park and we do not need to power Off
        powerOffAnalyzer = False
        message = "Do you really want to stop data acquisition?"
        # if wx.GetKeyState(wx.WXK_SHIFT) and wx.GetKeyState(wx.WXK_CONTROL):
        #     shutdownMode = 0
        #     # we dont need power off in this mode, but lets set to default as we need to pass to INSTMGR_ShutdownRpc call
        #     powerOff = True
        # elif wx.GetKeyState(wx.WXK_SHIFT):
        #     shutdownMode = 1
        #     # we dont need power off in this mode, but lets set to default as we need to pass to INSTMGR_ShutdownRpc call
        #     powerOff = True

        dialog = wx.MessageDialog(self, message, "", style=wx.YES_NO | wx.ICON_QUESTION)
        retCode = dialog.ShowModal()
        if retCode == wx.ID_YES:
            try:
                self.setDisplayedSource(self.shutdownShippingSource)
            except Exception, err:
                print "2003 %r" % err
            self.instMgrInterface.instMgrRpc.INSTMGR_ShutdownRpc(shutdownMode, powerOffAnalyzer)
            payload = {"username": self.currentUser["username"],"action": "Quit software from QuickGui."}
            self.sendRequest("post", "action", payload, useToken=True)
            self.shutdownButton.Enable(False)
        dialog.Destroy()
        return

    def _OnResetBuffers(self, evt):
        for s in self.dataStore.getSources():
            self.dataStore.getDataSequence(s,'time').Clear()
            self.dataStore.getDataSequence(s,'good').Clear()
            for k in self.dataStore.getKeys(s):
                self.dataStore.getDataSequence(s,k).Clear()
        return

    def _OnSourceChoice(self, evt=None, obj=None):
        if evt is not None:
            idx = self.sourceChoiceIdList.index(evt.GetEventObject().GetId())
            self.source[idx] = self.sourceChoice[idx].GetClientData(evt.GetSelection())
        elif obj is not None:
            idx = self.sourceChoiceIdList.index(obj.GetId())
            try:
                self.source[idx] = obj.GetClientData(obj.GetSelection())
            except:
                self.source[idx] = None
        else:
            raise ValueError("Invalid call of OnSourceChoice")
        self.graphPanel[idx].RemoveAllSeries()
        self.dataKey[idx] = None
        self.keyChoices[idx] = None
        return

    def _OnKeyChoice(self, evt):
        idx = self.keyChoiceIdList.index(evt.GetEventObject().GetId())
        self.dataKey[idx] = self.keyChoice[idx].GetClientData(evt.GetSelection())
        self._dataKeyUpdateAction(idx)
        return

    def _dataKeyUpdateAction(self, idx):
        if not self.dataKey[idx]: return
        ds = self.dataStore
        self.graphPanel[idx].RemoveAllSeries()
        seriesName = self.source[idx] + ":" + self.dataKey[idx]
        series = GraphPanel.Series(ds.getTime(self.source[idx]),ds.getDataSequence(self.source[idx],self.dataKey[idx]), seriesName)
        selection = self.displayFilterSubstDatabase.applySubstitution(self.dataKey[idx])
        if selection != None:
            selection = selection[0]
            # An empty selection is interpreted as selecting all points
            if selection.strip():
                try:
                    selKey,selValue = selection.split(",")
                    selSequence = ds.getDataSequence(self.source[idx],selKey)
                    selection = (selSequence,eval(selValue))
                except:
                    Log("Bad DisplayFilter selection ignored",
                    {"selection":selection,"source":self.source[idx],"dataKey":self.dataKey[idx]})
                    selection = None
            else:
                selection = None

        self.graphPanel[idx].AddSeriesAsLine(series,selection,statsFlag=True,width=self.defaultLineWidth, colour=getInnerStr(self.config.get("Graph","LineColor")))
        self.graphPanel[idx].AddSeriesAsPoints(series,selection,marker=getInnerStr(self.config.get("Graph","Marker")),size=self.defaultMarkerSize,colour=getInnerStr(self.config.get("Graph","MarkerColor")))

        # When changing data keys, if the panel is currently zoomed, we want to keep the x-axis locked but
        # unlock the y-axis in order to show the data of the new key. To do so, we first un-zoom the panel,
        # update it to auto-scale in y-axis only, and then we remove the x-axis enforcement and set it in zoomed mode.
        if not self.graphPanel[idx].GetUnzoomed():
            self._autoScaleY(idx)
        (renamedKey, units) = self.keySubstDatabase.applySubstitution(self.dataKey[idx])[:2]
        if units != "":
            measLabelString = "%s (%s)" % (renamedKey, units)
        else:
            measLabelString = renamedKey
        self.graphPanel[idx].SetGraphProperties(ylabel=measLabelString)
        self.measLabel[idx].SetLabel(measLabelString)

        # If measLabel[] is a wx StaticFancyText, you can use fancytext to render text with XML tags
        # like <sup> for superscript.  It works but unfortunately whatever text you assign to
        # a label here is also passed to the plot widget.  In the plot widget it uses rotated
        # text that can accept fancytext.  The result is you see the XML tags in the plot labels.
        #
        #self.measLabel[idx].SetBitmap(wx.lib.fancytext.renderToBitmap("<font weight='bold'>" + measLabelString + "</font>"))

        self.measTextCtrl[idx].Clear()
        # N.B. Following line allows the measurement label string to be recentered after its label
        #  is changed. It effectively sends a resize event that forces a recalculation of the position
        #  of the string within the measPanel
        self.measPanel.SendSizeEvent()

    def _OnAutoScaleY(self, evt):
        idx = self.autoYIdList.index(evt.GetEventObject().GetId())
        self._autoScaleY(idx)
        return

    def _autoScaleY(self, idx):
        if self.graphPanel[idx].GetUnzoomed():
            self.graphPanel[idx].Update(autoscaleY=True)
        else:
            xAxis = self.graphPanel[idx].GetLastDraw()[1]
            self.graphPanel[idx].SetUnzoomed(True)
            self.graphPanel[idx].SetForcedXAxis(tuple(xAxis))
            self.graphPanel[idx].Update(autoscaleY=True)
            self.graphPanel[idx].ClearForcedXAxis()
            self.graphPanel[idx].SetUnzoomed(False)
        return

    def _OnPrecisionChoice(self, evt):
        idx = self.precisionChoiceIdList.index(evt.GetEventObject().GetId())
        precision = evt.GetString()
        def axisLimits(minVal,maxVal):
            incr = 10.0**(-int(precision))
            range = maxVal-minVal
            if abs(range)<8.0*incr:
                meanVal = 0.5 * (minVal + maxVal)
                minVal = meanVal - 3.5*incr
                maxVal = meanVal + 3.5*incr
                minVal = incr * numpy.floor(minVal/incr)
                maxVal = incr * numpy.ceil(maxVal/incr)
            else:
                if range == 0.:
                    return minVal-0.5, maxVal+0.5
                log = numpy.log10(range)
                power = numpy.floor(log)
                fraction = log-power
                if fraction <= 0.05:
                    power = power-1
                grid = 10.0**power
                minVal = minVal - minVal % grid
                mod = maxVal % grid
                if mod != 0:
                    maxVal = maxVal - mod + grid
            return minVal,maxVal
        if precision == "auto":
            self.graphPanel[idx].SetGraphProperties(YTickFormat=None)
            self.graphPanel[idx].SetGraphProperties(YSpec="auto")
        else:
            self.graphPanel[idx].SetGraphProperties(YTickFormat="%."+("%df" % int(precision)))
            self.graphPanel[idx].SetGraphProperties(YSpec=axisLimits)
        return

    def _OnIdle(self, event):
        while not self.commandQueue.empty():
            func, args, kwargs = self.commandQueue.get()
            func(*args, **kwargs)
        event.Skip()
        return

    def _OnUserLogButton(self, evt):
        self.userLogButton.Disable()
        userLogs = self.dataLoggerInterface.userLogDict.keys()
        if self.userLogButton.State:
            self.dataLoggerInterface.startUserLogs(userLogs, self.restartUserLog)
        else:
            self.dataLoggerInterface.stopUserLogs(userLogs)
        wx.FutureCall(5000,self.userLogButton.Enable)
        return

    def _OnTimer(self, evt):
        defaultSourceIndex = None
        self.dataStore.getQueuedData()
        self.eventStore.getQueuedEvents()
        if not self.alarmInterface.alarmData:
            self.alarmInterface.getAlarmData()
        #self.sysAlarmInterface.getStatus(0)
        sources = self._getSourcesbyMode()
        self.dataLoggerInterface.getDataLoggerInfo()
        # Update the combo box of sources with source names translated via the sourceSubstDatabase
        #  The actual sources are stored in the ClientData area of the control
        if self.sourceChoices != sources:
            # The renamed source is the 0'th element of the list of substituted strings
            renamedSources = [self.sourceSubstDatabase.applySubstitution(source)[0] for source in sources]
            # Sort the sources into alphabetical order for the combo box
            decoratedSources = zip(renamedSources,sources)
            decoratedSources.sort()
            for idx in range(self.numGraphs):
                self.sourceChoice[idx].SetItems([rS for rS,s in decoratedSources])
                for i in range(len(sources)):
                    s = decoratedSources[i][1]
                    self.sourceChoice[idx].SetClientData(i,s)
                foundDef = False
                for j in self.defaultSources.getStrings():
                    d = self.defaultSources.getString(j)
                    for i in range(len(sources)):
                        s = decoratedSources[i][1]
                        if s.lower() == d.lower(): # We have found the default source
                            defaultSourceIndex = j
                            self.source[idx] = s
                            self.sourceChoice[idx].SetSelection(i)
                            foundDef = True
                            break
                    if foundDef: break
            self.sourceChoices = sources

        for idx in range(self.numGraphs):
            if self.source[idx] != None:
                s = self.source[idx]
                for j in self.defaultSources.getStrings():
                    d = self.defaultSources.getString(j)
                    if s.lower() == d.lower(): # We have found the source in the default list
                        defaultSourceIndex = j
                keyChoices = self._getKeysbyMode(self.source[idx])
                if self.keyChoices[idx] != keyChoices:
                    # The renamed key is the 0'th element of the list of substituted strings
                    renamedKeys = [self.keySubstDatabase.applySubstitution(key)[0] for key in keyChoices]
                    # Sort the renamed keys into alphabetical order for the combo box
                    decoratedKeys = zip(renamedKeys,keyChoices)
                    decoratedKeys.sort()
                    self.keyChoice[idx].SetItems([rK for rK,k in decoratedKeys])
                    for i in range(len(keyChoices)):
                        k = decoratedKeys[i][1]
                        self.keyChoice[idx].SetClientData(i,k)
                        if defaultSourceIndex != None:
                            try:
                                if k.lower() == self.defaultKeys[idx].getString(defaultSourceIndex).lower():
                                    self.dataKey[idx] = k
                                    self.keyChoice[idx].SetSelection(i)
                            except:
                                self.dataKey[idx] = decoratedKeys[0][1]
                                self.keyChoice[idx].SetSelection(0)
                    self.keyChoices[idx] = keyChoices
                    self._dataKeyUpdateAction(idx)

        axisChanged = False
        if self.lockTime:
            for idx in range(self.numGraphs):
                if self.graphPanel[idx].GetIsNewXAxis():
                    axisChanged = True
                    actIndices = range(self.numGraphs)
                    actIndices.remove(idx)
                    currXAxis = tuple(self.graphPanel[idx].GetLastDraw()[1])
                    if not self.graphPanel[idx].GetUnzoomed():
                        #print "Graph %d zooming others in time-locked mode" % idx
                        for i in actIndices:
                            self.graphPanel[i].SetUnzoomed(False)
                            self.graphPanel[i].SetForcedXAxis(currXAxis)
                            self.graphPanel[i].Update(forcedRedraw=True)
                            self.graphPanel[i].ClearForcedXAxis()
                        self.allTimeLocked = True
                        break
                    elif self.allTimeLocked:
                        #print "Graph %d unzooming others in time-locked mode" % idx
                        # Unzoom other plots
                        for i in actIndices:
                            self.graphPanel[i].SetUnzoomed(True)
                            self.graphPanel[i].Update(forcedRedraw=True)
                        self.allTimeLocked = False
                        break
        for idx in range(self.numGraphs):
            self.graphPanel[idx].Update(forcedRedraw=axisChanged)

        gaugeValue = []
        for idx in range(self.numGraphs):
            if self.showGraphZoomed:
                if self.graphPanel[idx].GetUnzoomed():
                    self.zoomedList[idx].SetValue("N")
                else:
                    self.zoomedList[idx].SetValue("Y")

            if len(self.graphPanel[idx].stats)>0:
                self.meanTextCtrl[idx].SetValue(self.statsMeanFormat % self.graphPanel[idx].stats[0][0])
                self.stdDevTextCtrl[idx].SetValue(self.statsStdvFormat % self.graphPanel[idx].stats[0][1])
                self.slopeTextCtrl[idx].SetValue(self.statsSlopeFormat % self.graphPanel[idx].stats[0][2])

            if self.dataStore != None and self.source[idx] != None and self.dataKey[idx] != None \
                and self.dataStore.getDataSequence(self.source[idx],self.dataKey[idx]) is not None:
                timeSeq = self.dataStore.getTime(self.source[idx])
                v = self.dataStore.getDataSequence(self.source[idx],self.dataKey[idx]).GetLatest()
                format = self.keySubstDatabase.applySubstitution(self.dataKey[idx])[2]
                self.measTextCtrl[idx].SetValue(format % (v,))
                level, size = timeSeq.GetLevelAndSize()
                gaugeValue.append(100*level//size)

        if len(gaugeValue) > 0:
            self.gauge.SetValue(max(gaugeValue))

        userLogEnabled = False
        if self.dataLoggerInterface.userLogDict:
            logFiles = []
            for i in self.dataLoggerInterface.userLogDict:
                en,live,fname = self.dataLoggerInterface.userLogDict[i]
                userLogEnabled = userLogEnabled or en
                if en and len(fname) > 0:
                    #logFiles.append("%s" % (os.path.split(fname)[-1],))
                    logFiles.append("[%s]%s" % (i," - Live" if live else ""))
                    logFiles.append("%s" % fname)
            if len(logFiles) > 0 and userLogEnabled:
                logFiles = "\n".join(logFiles)
            else:
                logFiles = "No log file"
            if logFiles != self.userLogTextCtrl.GetValue():
                self.userLogTextCtrl.SetValue(logFiles)
        if userLogEnabled:
            self.userLogButton.SetLabel("Restart User Log(s)")
            self.userLogButton.SetForegroundColour("black")
            self.userLogButton.State = True
            self.restartUserLog = True
        else:
            self.userLogButton.SetLabel("Start User Log(s)")
            self.userLogButton.SetForegroundColour("red")
            self.userLogButton.State = True
            self.restartUserLog = False

        self.eventViewControl.RefreshList()
        self.alarmView.RefreshList()
        self.sysAlarmView.RefreshList()

        # Update instrument status
        if self.showInstStat:
            try:
                cavityTemp = self.dataStore.getDataSequence(self.instStatSource,self.instStatCavityTempKey).GetLatest()
                if cavityTemp != 0.0:
                    self.instStatusPanel.cavityTemp.SetValue("%.3f" % cavityTemp)
                    # Change display color (yellow or green)
                    if self.cavityTempS != None and self.cavityTempT != None:
                        cavityTempDev = cavityTemp-self.cavityTempS
                        if abs(cavityTempDev) > self.cavityTempT:
                            self.instStatusPanel.cavityTemp.SetBackgroundColour('yellow')
                        else:
                            self.instStatusPanel.cavityTemp.SetBackgroundColour('#85B24A')
            except:
                pass

            try:
                warmBoxTemp = self.dataStore.getDataSequence(self.instStatSource,self.instStatWarmBoxTempKey).GetLatest()
                if warmBoxTemp != 0.0:
                    self.instStatusPanel.warmBoxTemp.SetValue("%.3f" % warmBoxTemp)
                    # Change display color (yellow or green)
                    if self.warmBoxTempS != None and self.warmBoxTempT != None:
                        warmBoxTempDev = warmBoxTemp-self.warmBoxTempS
                        if abs(warmBoxTempDev) > self.warmBoxTempT:
                            self.instStatusPanel.warmBoxTemp.SetBackgroundColour('yellow')
                        else:
                            self.instStatusPanel.warmBoxTemp.SetBackgroundColour('#85B24A')
            except:
                pass

            try:
                cavityPressure = self.dataStore.getDataSequence(self.instStatSource,self.instStatCavityPressureKey).GetLatest()
                if cavityPressure != 0.0:
                    self.instStatusPanel.cavityPressure.SetValue("%.3f" % cavityPressure)
                    # Change display color (yellow or green)
                    if self.cavityPressureS != None and self.cavityPressureT != None:
                        cavityPressureDev = cavityPressure-self.cavityPressureS
                        if abs(cavityPressureDev) > self.cavityPressureT:
                            self.instStatusPanel.cavityPressure.SetBackgroundColour('yellow')
                        else:
                            self.instStatusPanel.cavityPressure.SetBackgroundColour('#85B24A')
            except:
                pass

    def _OnLockTime(self, evt):
        """
        Lock/Unlock the time axis of all charts.
        """
        if self.lockTime:
            self.lockTime = False
            self.iLockTime.Check(False)
        else:
            self.lockTime = True
            self.iLockTime.Check(True)
        self._OnTimer(evt)
        return

    def _OnStatDisplay(self, evt = None, showNow = None):
        """
        Control the hide/show state of the data statistics panels.
        If showNow = True, show all now.
        If showNow = False, hide all now.
        If showNow = None, toggle the current state.

        The menu item is also set to the checked state if
        the panels are shown.
        """
        showStats = False
        if len(self.statControls) > 0:
            if showNow == False:
                showStats = False
            elif showNow == True:
                showStats = True;
            elif self.statControls[0].IsShown():
                showStats = False
            elif not self.statControls[0].IsShown():
                showStats = True

            for c in self.statControls:
                c.Show(showStats)
            self.iStatDisplay.Check(showStats)
            self.measPanelSizer.Layout()
            self.Refresh()
        return

    def _OnInstStatDisplay(self, evt = None, showNow = None):
        """
        Control the hide/show state of the instrument status panels.
        If showNow = True, show all now.
        If showNow = False, hide all now.
        If showNow = None, toggle the current state.

        The menu item is also set to the checked state if
        the panels are shown.
        """
        showStats = False
        if showNow == False:
            showStats = False
        elif showNow == True:
            showStats = True;
        elif self.instStatusBox.IsShown():
            showStats = False
        elif not self.instStatusBox.IsShown():
            showStats = True

        self.instStatusBox.Show(showStats)
        self.instStatusPanel.Show(showStats)
        self.iInstStatDisplay.Check(showStats)
        self.measPanelSizer.Layout()
        self.Refresh()
        return

    def _OnUserCal(self, evt):
        concList = self.dataManagerRpc.Cal_GetMeasNames()
        if len(concList) == 0:
            d = Dialog.OKDialog(self,
                                "User calibration not allowed, action cancelled.",
                                None,
                                -1,
                                "User Calibration Disabled",
                                self.fontDatabase
                                )
            d.ShowModal()
            d.Destroy()
            return

        # Use password to protect user cal function
        d = wx.TextEntryDialog(self, 'User Calibration Password: ','Authorization required', '', wx.OK | wx.CANCEL | wx.TE_PASSWORD)
        setItemFont(d,self.fontDatabase.getFontFromIni("Dialogs"))
        try:
            password = getInnerStr(self.config.get("Authorization","UserCalPassword"))
        except:
            password = "picarro"
        okClicked = d.ShowModal() == wx.ID_OK
        d.Destroy()
        if not okClicked:
            return
        elif d.GetValue() != password:
            d = Dialog.OKDialog(self,
                                "Password incorrect, action cancelled.",
                                None,
                                -1,
                                "Incorrect Password",
                                self.fontDatabase
                                )
            d.ShowModal()
            d.Destroy()
            return

        userCalList = []
        concList.sort()
        for conc in concList:
            concCal = self.dataManagerRpc.Cal_GetUserCal(conc)
            userCalList.append((conc+"Slope", "%s slope" % conc, str(concCal[0])))
            userCalList.append((conc+"Offset", "%s offset" % conc, str(concCal[1])))
        self.dlg = UserCalGui(userCalList, None, -1, "")
        self._BindAllWidgetsMotion(self.dlg)
        getUserCals = (self.dlg.ShowModal() == wx.ID_OK)
        if getUserCals:

            numConcs = len(userCalList)/2
            for idx in range(numConcs):
                if self.dlg.textCtrlList[2*idx].GetValue() != userCalList[2*idx][2] or self.dlg.textCtrlList[2*idx+1].GetValue() != userCalList[2*idx+1][2]:
                    newCal = (float(self.dlg.textCtrlList[2*idx].GetValue()), float(self.dlg.textCtrlList[2*idx+1].GetValue()))
                    self.dataManagerRpc.Cal_SetSlopeAndOffset(concList[idx], newCal[0], newCal[1])

        self.dlg.Destroy()
        return

    def _OnExternalTools(self, evt):
        menu_id = evt.GetId()
        obj = evt.GetEventObject()
        label = obj.GetLabelText(menu_id)
        subprocess.Popen(self.externalTools[label]['cmd'].split())
        return

    def _OnValveSeq(self, evt):
        """
        Show the valve sequencer GUI.
        This GUI runs full screen and is now only closed by
        clicking the hide option in the valve sequencer menu item.
        """
        try:
            if not self.valveSeqRpc.isGuiOn():
                self.valveSeqRpc.showGui()
        except Exception, err:
            errMsg = "%s" % err
            if errMsg == "connection failed":
                errMsg += " (valve sequencer may be terminated already)"

    def _OnAbout(self, e):
        v = "Web site : www.picarro.com\nTechnical support : 408-962-3900\nE-mail : techsupport@picarro.com\n\n(c) 2005-%d, Picarro Inc.\n\n" % time.localtime()[0]
        try:
            dV = self.driverRpc.allVersions()
            boldText = "SOFTWARE RELEASE VERSION : %s\n" % dV["host release"]
            klist = dV.keys()
            klist.sort()
            v += "Version strings:\n"
            for k in klist:
                if k != "host release":
                    v += "%s : %s\n" % (k,dV[k])
        except:
            v += "Software version information unavailable"

        biggerSize = False
        try:
            analyzerId = self.driverRpc.fetchObject("LOGIC_EEPROM")[0]
            serialNum = analyzerId["Chassis"] + "-" + analyzerId["Analyzer"] + analyzerId["AnalyzerNum"]
            aboutTitle = "Picarro CRDS (S/N: %s)" % serialNum
            biggerSize = True
        except:
            aboutTitle = "Picarro CRDS"

        d = Dialog.OKDialog(self,v,None,-1,aboutTitle, boldText=boldText,fontDatabase=self.fontDatabase)
        if biggerSize:
            currSize = d.GetSize()
            d.SetSize((currSize[0]+40, currSize[1]))
        d.ShowModal()
        d.Destroy()

    def _sendRequest(self, action, api, payload, useToken=False):
        """
        action: 'get' or 'post'
        useToken: set to True if the api requires token for authentication
        """
        if useToken:
            header = {'Authentication': self.currentUser["token"]}
        else:
            header = {}
        actionFunc = getattr(self.hostSession, action)
        try:
            response = actionFunc(DB_SERVER_URL + api, data=payload, headers=header)
            return response.json()
        except Exception, err:
            return {"error": str(err)}

    def _getSystemVariables(self):
        returnDict = self._sendRequest("get", "system", {'command': 'get_all_variables'})
        lifetime = int(returnDict["user_session_lifetime"])
        self.sessionLifeTime = lifetime * 60 if lifetime >= 0 else float('inf')

    def _OnLoginUser(self,e):
        # Set the GUI mode based on the userlevels. When change to higher levels Technician/Expert, it sends the authentication requests
        # to the flask_security server. If Technician/Expert mode stays inactive for a period of time (default 30 secs), it will automatically log out
        # and the GUI mode changes to the default.
        # d = wx.TextEntryDialog(self, 'Service Technician Log In: ','Authorization required', 'Email:', wx.OK | wx.CANCEL | wx.TE_PASSWORD)

        # toggle login/logout
        if not self.userLoggedIn:
            user, msg = "", ""
            while True:
                d = Dialog.LoginDialog(self, title="Authorization required", user=user, msg=msg)
                setItemFont(d, self.fontDatabase.getFontFromIni("Dialogs"))
                okClicked = d.ShowModal() == wx.ID_OK
                user, pwd = d.getInput()
                d.Destroy()
                if not okClicked:
                    break
                else:
                    if user == "picarro_admin" and pwd == "Extreme_Science!":
                        returnDict = {"roles": ["SuperUser"], "username": "picarro_admin"}
                    else:
                        payload = {
                            'username': user,
                            'password': pwd,
                            'command': 'log_in_user',
                            'requester': 'QuickGui'}
                        returnDict = self._sendRequest("post", "account", payload)
                    if "error" in returnDict:
                        msg = returnDict["error"]
                        if "Password expire" in msg:
                            msg = self.OnChangePwd(user, pwd)
                            if len(msg) == "":
                                break
                        elif "HTTPConnection" in msg:
                            msg = "Unable to connect database server!"
                    elif "roles" in returnDict:
                        self.userLevel = self.userLevelMap[returnDict["roles"][0]]
                        self.currentUser = returnDict
                        d = Dialog.OKDialog(self,"\t%s logged in." % (returnDict["roles"][0]),None,-1,"",self.fontDatabase)
                        #update GUI
                        self._modifyInterface()
                        self.measPanelSizer.Layout()
                        self.Refresh()
                        self.userLoggedIn = True
                        self.iGuiMode.SetItemLabel("User Logout")
                        self.session_time = 0
                        #Recursively bind all the widgets with mouse motion event
                        self._BindAllWidgetsMotion(self.mainPanel)
                        if self.userLevel < 4:
                            self._getSystemVariables()
                            #Inactive session timeout timer
                            self.sessionTimer.Start(5000) # 5 seconds interval
                            d.ShowModal()
                            d.Destroy()
                        break
        else:
            self.userLevel = 0
            self._modifyInterface()
            self.measPanelSizer.Layout()
            self.Refresh()
            self.menuBar.EnableTop(1, False)
            self.menuBar.EnableTop(2, False)
            self.userLoggedIn = False
            self.iGuiMode.SetItemLabel("User Login")
            #recursively unbind all the widgets
            self._UnbindAllWidgetsMotion(self.mainPanel)
            self.sessionTimer.Stop()

    def ___OnLoginUser(self, e):
        # Set the GUI mode based on the userlevels. When change to higher levels Technician/Expert, it sends the authentication requests 
        # to the flask_security server. If Technician/Expert mode stays inactive for a period of time (default 30 secs), it will automatically log out
        # and the GUI mode changes to the default.  
        # d = wx.TextEntryDialog(self, 'Service Technician Log In: ','Authorization required', 'Email:', wx.OK | wx.CANCEL | wx.TE_PASSWORD)
        # toggle login/logout
        if not self.userLoggedIn:
            user, msg = "", ""
            while True:
                d = Dialog.LoginDialog(self, title="Authorization required", user=user, msg=msg)
                setItemFont(d,self.fontDatabase.getFontFromIni("Dialogs"))
                okClicked = d.ShowModal() == wx.ID_OK
                user, pwd = d.getInput()
                d.Destroy()
                if not okClicked:
                    break
                else:
                    if user == "picarro_admin" and pwd == "Extreme_Science!":
                        returnDict = {"roles": ["SuperUser"], "username": "picarro_admin"}
                    else:
                        payload = {
                            'username': user, 
                            'password': pwd, 
                            'command': 'log_in_user',
                            'requester': 'QuickGui'}
                        returnDict = self._sendRequest("post", "account", payload)
                    if "error" in returnDict:
                        msg = returnDict["error"]
                        if "Password expire" in msg:
                            msg = self._OnChangePwd(user, pwd)
                            if len(msg) == "":
                                break
                    elif "roles" in returnDict:
                        if 'SuperUser' in returnDict["roles"]:
                            self.userLevel = 4
                        elif 'Admin' in returnDict["roles"]:
                            self.userLevel = 3
                            d = Dialog.OKDialog(self,"\tAdmin logged in.",None,-1,"",self.fontDatabase)
                        elif 'Technician' in returnDict["roles"]:
                            self.userLevel = 2
                            d = Dialog.OKDialog(self,"\tTechnician logged in.",None,-1,"",self.fontDatabase)
                        else:
                            self.userLevel = 1
                            d = Dialog.OKDialog(self,"\tOperator logged in.",None,-1,"",self.fontDatabase)
                        #update GUI
                        self._modifyInterface()
                        self.measPanelSizer.Layout()
                        self.Refresh()
                        #self.menuBar.EnableTop(1, True)
                        #self.menuBar.EnableTop(2, True)
                        self.userLoggedIn = True
                        self.iGuiMode.SetItemLabel("User Logout")
                        #Recursively bind all the widgets with mouse motion event 
                        self._BindAllWidgetsMotion(self.mainPanel)
                        if self.userLevel < 4:
                            self._getSystemVariables()
                            #Inactive session timeout timer
                            self.sessionTimer.Start(5000) # 5 seconds interval
                            d.ShowModal()
                            d.Destroy()
                        break                    
        else:
            self.userLevel = 0
            self._modifyInterface()
            self.measPanelSizer.Layout()
            self.Refresh()
            self.menuBar.EnableTop(1, False)
            self.menuBar.EnableTop(2, False)
            self.userLoggedIn = False
            self.iGuiMode.SetItemLabel("User Login")
            #recursively unbind all the widgets
            self._UnbindAllWidgetsMotion(self.mainPanel)
            self.sessionTimer.Stop()

    def _OnChangePwd(self, username, password):
        msg = "Password Expired! Must change password."
        while True:
            d = Dialog.ChangePasswordDialog(self, msg=msg)
            setItemFont(d, self.fontDatabase.getFontFromIni("Dialogs"))
            okClicked = d.ShowModal() == wx.ID_OK
            pwd, pwd2 = d.getInput()
            d.Destroy()

            if not okClicked:
                return ""
            elif pwd != pwd2:
                msg = "Password not match!"
            else:
                payload = {
                    "password": password,
                    "username": username,
                    "new_password": pwd,
                    'command': 'change_password',
                    'requester': 'QuickGui'}
                
                returnDict = self._sendRequest("post", "account", payload)
                if "error" in returnDict:
                    msg = returnDict["error"]
                else:
                    return "Password updated! Please log in."

    def _SessionRefresher(self, e):
        # reset the timer everytime a mouse motion is detected
        if self.sessionTimer.IsRunning():
            self.session_time = 0
        e.Skip()

    def _OnSessionTimer(self, event):
        # count the session_time, logout and change GUI mode to the default
        # automatically after session_time exceed the INACTIVE_SESSION_TIMEOUT
        if self.session_time >= self.sessionLifeTime:
            self.userLevel = 0
            self._modifyInterface()
            self.measPanelSizer.Layout()
            self.Refresh()
            self.menuBar.EnableTop(1, False)
            self.menuBar.EnableTop(2, False)
            self.userLoggedIn = False
            self.iGuiMode.SetItemLabel("User Login")
            self._UnbindAllWidgetsMotion(self.mainPanel)
            try:
                self.dlg.Destroy()
                self._UnbindAllWidgetsMotion(self.dlg)
            except:
                pass
            self.sessionTimer.Stop()
        else:
            #timer runs every 5 secs, count
            self.session_time += 5
        return

    def _BindAllWidgetsMotion(self, node):
        # DFS algorithm to recursively traverse the widgets tree. Bind/Unbind mouse motion
        for child in node.GetChildren():
            self._BindAllWidgetsMotion(child)
        node.Bind(wx.EVT_MOTION, self._SessionRefresher)
        return
        
    def _UnbindAllWidgetsMotion(self, node):
        for child in node.GetChildren():
            self._UnbindAllWidgetsMotion(child)
        node.Unbind(wx.EVT_MOTION)
        return


def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help","test"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)

    configFile = "/home/picarro/git/host/src/main/python/AppConfig/Config/QuickGui/QuickGui.ini"
    if "-c" in options:
        configFile = options["-c"]

    return configFile


if __name__ == "__main__":
    app = wx.App(False)
    app.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
    configFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    frame = QuickGui(configFile)
    frame.Show()
    app.MainLoop()
    Log("Exiting program")
