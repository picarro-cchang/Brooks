#!/usr/bin/python
# -*- coding: utf-8 -*-
#
"""
File Name: QuickGui.py
Purpose: Simple GUI for plotting measurement system and data manager broadcasts

File History:
    07-02-01 sze   Created first release
    07-05-22 sze   Improved handling of ini file
    08-01-07 sze   DisplayFilters which have blank select fields will select all
                   points. Invalid selections are logged, but will again select
                   all points
    08-03-01 sze   Add matching to substitution database handler to allow sources
                   and keys to be matched for StandardModeSources and StandardModeKeys
                   in the INI file
    08-03-07 sze   Corrected bad first point when a new data key is added to a pre-existing source
    08-03-07 sze   Change handling of [Default] section in INI file to allow multiple default
                   source-key pairs.
    08-09-18  alex Replaced ConfigParser with CustomConfigObj
    09-07-10  alex Support multiple panels to display user-selectable measurements. Also support time-axis locking function.
    09-07-28  alex Add pulse analyzer GUI
    09-07-29  alex Create default view (auto-scaled in y-axis) in zoomed mode whenever data keys are switched while keeping x-axis unchanged.
    09-08-05  alex Improve time-locking without a master plot
    10-01-22  sze  Changed date format display to ISO standard
    10-07-05  alex Add the function to change line/marker color at a specified time
    14-05-20  tw   Fixed bug in Win7 alarm box height calc, bumped max alarms in box to 5 before shows scrollbars.
    16-11-09  wenting Implemented three user levels on GUI mode: Operator mode, Service Technician mode and Expert mode.
    17-04-21  wenting Implemented users inactive session timeout function.
Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "QuickGui"
APP_DESCRIPTION = "CRDS GUI"
__version__ = 1.0
_DEFAULT_CONFIG_NAME = "QuickGui.ini"
_MAIN_CONFIG_SECTION = "Setup"
UPDATE_TIMER_INTERVAL = 1000
FLASK_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"
import pdb
import sys
import wx
from wx.lib import sized_controls
import wx.lib.fancytext
import Queue
import numpy
import requests
import os
from os.path import dirname as os_dirname
import re
import collections
import string
import time
import threading
from threading import Thread
import pprint
import traceback
from platform import platform
import wx.lib.mixins.listctrl as listmix
from wx.lib.wordwrap import wordwrap
import subprocess32 as subprocess

from Host.QuickGui.PulseAnalyzerGui import PulseAnalyzerGui
from Host.QuickGui.UserCalGui import UserCalGui
from Host.QuickGui.SysAlarmGui import *
import Host.QuickGui.DialogUI as Dialog
from Host.Common import CmdFIFO, StringPickler, Listener, TextListener
#from Host.Common import plot
from Host.Common import GraphPanel
from Host.Common import AppStatus
from Host.Common import SharedTypes
from Host.Common.GuiTools import *
from Host.Common.SharedTypes import RPC_PORT_ALARM_SYSTEM, RPC_PORT_DATALOGGER, RPC_PORT_INSTR_MANAGER, RPC_PORT_DRIVER, \
                                    RPC_PORT_SAMPLE_MGR, RPC_PORT_DATA_MANAGER, RPC_PORT_VALVE_SEQUENCER, RPC_PORT_QUICK_GUI, \
                                    RPC_PORT_SUPERVISOR, RPC_PORT_ARCHIVER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.parsePeriphIntrfConfig import parsePeriphIntrfConfig
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

class ImageDatabase(object):
    def __init__(self):
        self.dbase = {}
    def setImagePanel(self,key,parent,*args,**kwargs):
        if key not in self.dbase:
            raise KeyError("Cannot setImagePanel in database until key %s has been registered" % (key,))
        else:
            kwargs.update(dict(size=self.dbase[key][5]))
            self.dbase[key][0] = ImagePanel(self.dbase[key][1],parent,*args,**kwargs)
    def processConfigSection(self,config,sectionName,key):
        fileName = config.get(sectionName,"File")
        AppDir = os.path.split(AppPath)[0]
        fileName = os.path.join(AppDir,fileName)
        try:
            temp = config.get(sectionName,"ImageReference")
            imageRef = [float(t) for t in temp.split(",")]
        except KeyError:
            imageRef = [0.5,0.5]
        try:
            temp = config.get(sectionName,"FrameReference")
            frameRef = [float(t) for t in temp.split(",")]
        except KeyError:
            frameRef = [0.5,0.5]
        try:
            temp = config.get(sectionName,"Offset")
            offset = [float(t) for t in temp.split(",")]
        except KeyError:
            offset = [0.0,0.0]
        try:
            temp = config.get(sectionName,"Scale")
            scale = [float(t) for t in temp.split(",")]
        except KeyError:
            scale = [-1,-1]
        self.dbase[key] = [None,fileName,imageRef,frameRef,offset,scale]
    def placeImage(self,key,frameSize):
        fw, fh = frameSize
        imagePanel,fileName,imageRef,frameRef,offset,scale = self.dbase[key]
        iw, ih = imagePanel.Size
        x = fw*frameRef[0]-iw*imageRef[0]+offset[0]
        y = fh*frameRef[1]-ih*imageRef[1]+offset[1]
        # Change to screen coordinates
        y = fh - ih - y
        imagePanel.SetPosition((int(x),int(y)))
        wx.FutureCall(5,imagePanel.Refresh)

class ImagePanel(wx.Panel):
    def __init__(self,imgFile,parent,id=-1,size=(-1,-1),**kwargs):
        wx.Panel.__init__(self,parent,id,**kwargs)
        img = wx.Image(imgFile,wx.BITMAP_TYPE_ANY)
        if size[0]<0: w = abs(size[0])*img.GetWidth()
        else: w = size[0]
        if size[1]<0: h = abs(size[1])*img.GetHeight()
        else: h = size[1]
        img = img.Scale(w,h)
        self.SetSize((w,h))
        self.bmp = img.ConvertToBitmap()
        self.Size = (w,h)
        self.Bind(wx.EVT_PAINT,self.OnPaint)

    def OnPaint(self,evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp,0,0,True)

class InstMgrInterface(object):
    """Interface to the instrument manager RPC"""
    def __init__(self,config):
        self.config = config
        self.loadConfig()
        self.instMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, ClientName = "QuickGui")
        self.result = None
        self.exception = None
        self.rpcInProgress = False

    def loadConfig(self):
        pass


class AlarmViewListCtrl(wx.ListCtrl):
    """ListCtrl to display alarm status
    attrib is a list of wx.ListItemAttr objects for the disabled and enabled alarm text
    DataSource must be the AlarmInterface object which reads the alarm status
    """
    def __init__(self, parent, id, attrib, DataStore=None, DataSource=None, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, numAlarms=4):
        wx.ListCtrl.__init__(self, parent, id, pos, size,
                             style = wx.LC_REPORT
                             | wx.LC_VIRTUAL
                             | wx.LC_NO_HEADER
                             | wx.NO_BORDER
                         )
        self.parent = parent
        self.ilEventIcons = wx.ImageList(32, 32)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)
        thisDir = os_dirname(AppPath)
        self.IconAlarmOff  = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidOff_32x32.png',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconAlarmGreen  = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidGreen_32x32.png',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconAlarmYellow  = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidYellow_32x32.png',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconAlarmRed    = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidRed_32x32.png',
                                                     wx.BITMAP_TYPE_ICO))

        self.dataStore = DataStore
        self._DataSource = DataSource
        self.InsertColumn(0,"Icon",width=40)
        sx,sy = self.GetSize()

        # must subtract off width needed for scrollbars (17)
        self.InsertColumn(1, "Name", width=sx-40-17)

        self.alarmNames = []
        for i in range(numAlarms):
            self.alarmNames.append("Alarm %d" % (i+1))
        self.attrib = attrib
        self.SetItemCount(numAlarms)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseDown)
        self.Bind(wx.EVT_MOTION,self.OnMouseMotion)
        self.tipWindow = None
        self.tipItem = None

    def SetMainForm(self,mainForm):
        self.mainForm = mainForm

    def OnMouseDown(self,evt):
        pass

    def OnLeftDown(self,evt):
        pos = evt.GetPositionTuple()
        item,flags = self.HitTest(pos)
        if self.tipWindow and self.tipWindow.IsShown():
            self.tipWindow.Close()
        if self._DataSource.alarmData:
            name,mode,enabled,alarm1,clear1,alarm2,clear2 = self._DataSource.alarmData[item]
            alarm1 = "%.2f" % alarm1
            alarm2 = "%.2f" % alarm2
            clear1 = "%.2f" % clear1
            clear2 = "%.2f" % clear2
            d = dict(name=name,mode=mode,enabled=enabled,alarm1=alarm1,clear1=clear1,
                        alarm2=alarm2,clear2=clear2)
            dialog = Dialog.AlarmDialog(self.mainForm,d,None,-1,"Setting alarm %d" % (item+1,))
            retCode = dialog.ShowModal()
            dialog.Destroy()
            if retCode == wx.ID_OK:
                self._DataSource.setAlarm(item+1,d["enabled"],d["mode"],
                                          float(d["alarm1"]),float(d["clear1"]),
                                          float(d["alarm2"]),float(d["clear2"]))

    def OnMouseMotion(self,evt):
        pos = evt.GetPositionTuple()
        item,flags = self.HitTest(pos)
        if item>=0:
            if self.tipWindow and self.tipWindow.IsShown():
                self.tipWindow.Close()
            rect = self.GetItemRect(item)
            left, top = self.ClientToScreenXY(rect.x, rect.y)
            right, bottom = self.ClientToScreenXY(rect.GetRight(), rect.GetBottom())
            rect = wx.Rect(left, top, right - left + 1, bottom - top + 1)
            if self._DataSource.alarmData:
                name,mode,enabled,alarm1,clear1,alarm2,clear2 = self._DataSource.alarmData[item]
                if mode == "Higher":
                    desc = "Alarm if > %.2f, Cleared when < %.2f" % (alarm1, clear1)
                elif mode == "Lower":
                    desc = "Alarm if < %.2f, Cleared when > %.2f" % (alarm1, clear1)
                elif mode == "Outside":
                    desc = "Alarm if < %.2f or > %.2f, Cleared when > %.2f and < %.2f" % \
                         (alarm2, alarm1, clear2, clear1)
                elif mode == "Inside":
                    desc = "Alarm if > %.2f and < %.2f, Cleared when < %.2f or > %.2f" % \
                         (alarm2, alarm1, clear2, clear1)
                self.tipWindow = wx.TipWindow(self,"%s" % (desc,),maxLength=1000,rectBound=rect)
        evt.Skip()

    def OnGetItemText(self,item,col):
        if col==1 and self._DataSource.alarmData:
            return self._DataSource.alarmData[item][0]
        else:
            return ""

    def OnGetItemAttr(self,item):
        # Use appropriate attributes for enabled and disabled items
        if self._DataSource.alarmData and self._DataSource.alarmData[item][2]:
            return self.attrib[1]
        else:
            return self.attrib[0]

    def OnGetItemImage(self, item):
        """
        When the list is refreshed with RefreshList() (are we sure?) it comes here
        to figure out what LED light to display.
        """
        alarmColor = self.IconAlarmRed
        status = int(self.dataStore.alarmStatus) & (1 << item)
        enabled = (self._DataSource.alarmData and self._DataSource.alarmData[item][2])
        itemText = self.OnGetItemText(item,1)

        if not enabled:
            alarmColor = self.IconAlarmOff
        elif len(self.dataStore.mode) == 0 or "warming_mode" in self.dataStore.mode:
            alarmColor = self.IconAlarmOff
        elif status == 0:
            alarmColor = self.IconAlarmGreen
        else:
            alarmColor = self.IconAlarmRed

        return alarmColor

    def Defocus(self):
        """
        GTK version of ListCtrl automatically sets the focus rectangle on
        a list item even if the focus is on an entirely different widget.
        This will remove the focus state.
        Note that this needs to be called after every screen redraw.
        """
        self.SetItemState(self.GetFocusedItem(), 0, wx.LIST_STATE_FOCUSED)

    def RefreshList(self):
        self.RefreshItems(0,self.GetItemCount()-1)
        self.Defocus()

class AlarmInterface(object):
    """Interface to the alarm system RPC and status ports"""
    def __init__(self,config):
        self.config = config
        self.loadConfig()
        self.alarmRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ALARM_SYSTEM, ClientName = "QuickGui")

        self.statusWord = 0x0
        self.result = None
        self.exception = None
        self.rpcInProgress = False
        self.alarmData = []

    def getAlarmData(self):
        """Get alarm data by making a non-blocking RPC call to the alarm system"""
        if self.rpcInProgress: return False
        self.result = None
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._getAlarmData)
        th.setDaemon(True)
        th.start()
        return True

    def _getAlarmData(self):
        alarmData = []
        index = 1
        try:
            while True:
                status,name = self.alarmRpc.ALARMSYSTEM_getNameRpc(index)
                if status<0: break
                status,mode = self.alarmRpc.ALARMSYSTEM_getModeRpc(index)
                status,enabled = self.alarmRpc.ALARMSYSTEM_isEnabledRpc(index)
                status,alarm1 = self.alarmRpc.ALARMSYSTEM_getAlarmThresholdRpc(index,1)
                status,alarm2 = self.alarmRpc.ALARMSYSTEM_getAlarmThresholdRpc(index,2)
                status,clear1 = self.alarmRpc.ALARMSYSTEM_getClearThresholdRpc(index,1)
                status,clear2 = self.alarmRpc.ALARMSYSTEM_getClearThresholdRpc(index,2)
                alarmData.append((name,mode,enabled,alarm1,clear1,alarm2,clear2))
                index += 1
            self.result = self.alarmData = alarmData
        except Exception,e:
            self.exception = e
        self.rpcInProgress = False

    def setAlarm(self,index,enable,mode,alarm1,clear1,alarm2=0,clear2=0):
        """Set alarm enable and threshold by making a non-blocking RPC call to the alarm system"""
        if self.rpcInProgress: return False
        self.result = None
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._setAlarm,args=(index,enable,mode,alarm1,clear1,alarm2,clear2))
        th.setDaemon(True)
        th.start()
        return True

    def _setAlarm(self,index,enable,mode,alarm1,clear1,alarm2,clear2):
        try:
            self.alarmRpc.ALARMSYSTEM_setModeRpc(index,mode)
            self.alarmRpc.ALARMSYSTEM_setAlarmThresholdRpc(index,1,alarm1)
            self.alarmRpc.ALARMSYSTEM_setClearThresholdRpc(index,1,clear1)
            self.alarmRpc.ALARMSYSTEM_setAlarmThresholdRpc(index,2,alarm2)
            self.alarmRpc.ALARMSYSTEM_setClearThresholdRpc(index,2,clear2)
            if enable:
                self.alarmRpc.ALARMSYSTEM_enableRpc(index)
            else:
                self.alarmRpc.ALARMSYSTEM_disableRpc(index)
        except Exception,e:
            self.exception = e
        # Refresh alarm data with changes made
        self._getAlarmData()
        self.rpcInProgress = False

    def loadConfig(self):
        pass

class DataLoggerInterface(object):
    """Interface to the data logger and archiver RPC"""
    def __init__(self,config):
        self.config = config
        self.loadConfig()
        self.archiverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER, ClientName = "QuickGui")
        self.dataLoggerRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER, ClientName = "QuickGui")
        self.exception = None
        self.rpcInProgress = False
        self.userLogDict = {}
        self.privateLogDict = {}

    def getDataLoggerInfo(self):
        """Get data logger info by making a non-blocking RPC call to the data logger"""
        if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._getDataLoggerInfo)
        th.setDaemon(True)
        th.start()
        return True

    def _getDataLoggerInfo(self):
        userLogDict = {}
        privateLogDict = {}
        try:
            stat,userLogs = self.dataLoggerRpc.DATALOGGER_getUserLogsRpc()
            stat,privateLogs = self.dataLoggerRpc.DATALOGGER_getPrivateLogsRpc()
            for i in userLogs:
                en = self.dataLoggerRpc.DATALOGGER_logEnabledRpc(i)
                if en:
                    fname = self.dataLoggerRpc.DATALOGGER_getFilenameRpc(i)
                    live, fname = self.archiverRpc.GetLiveArchiveFileName(i,fname)
                    userLogDict[i] = (True,live,fname)
                else:
                    userLogDict[i] = (False,False,'')
            for i in privateLogs:
                en = self.dataLoggerRpc.DATALOGGER_logEnabledRpc(i)
                if en:
                    fname = self.dataLoggerRpc.DATALOGGER_getFilenameRpc(i)
                    live, fname = self.archiverRpc.GetLiveArchiveFileName(i,fname)
                    privateLogDict[i] = (True,live,fname)
                else:
                    privateLogDict[i] = (False,False,'')
        except Exception,e:
            self.exception = e
        self.rpcInProgress = False
        self.userLogDict = userLogDict
        self.privateLogDict = privateLogDict

    def startUserLogs(self,userLogList,restart=False):
        """Start a list of user logs by making a non-blocking RPC call to the alarm system"""
        while self.rpcInProgress: time.sleep(0.5)
        # if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._startUserLogs,args=(userLogList,restart))
        th.setDaemon(True)
        th.start()
        return True

    def _startUserLogs(self,userLogList,restart):
        try:
            for i in userLogList:
                self.dataLoggerRpc.DATALOGGER_startLogRpc(i,restart)
        except Exception,e:
            self.exception = e
        # Refresh info with changes made
        self._getDataLoggerInfo()
        self.rpcInProgress = False

    def stopUserLogs(self,userLogList):
        """Stop a list of user logs by making a non-blocking RPC call to the alarm system"""
        while self.rpcInProgress: time.sleep(0.5)
        # if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._stopUserLogs,args=(userLogList,))
        th.setDaemon(True)
        th.start()
        return True

    def _stopUserLogs(self,userLogList):
        try:
            for i in userLogList:
                self.dataLoggerRpc.DATALOGGER_stopLogRpc(i)
        except Exception,e:
            self.exception = e
        # Refresh info with changes made
        self._getDataLoggerInfo()
        self.rpcInProgress = False

    def loadConfig(self):
        pass
class EventViewListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """ListCtrl that auto-sizes the right-most column to fit the width.

    DataSource must be the EventStore object which contains the event history
    """
    def __init__(self, parent, id, config, DataSource, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        wx.ListCtrl.__init__(self, parent, id, pos, size,
                             style = wx.LC_REPORT
                             | wx.LC_VIRTUAL
                             #| wx.BORDER_SUNKEN
                             | wx.BORDER_NONE
                             # wx.LC_EDIT_LABELS
                             #| wx.LC_SORT_ASCENDING
                             #| wx.LC_NO_HEADER
                             #| wx.LC_VRULES
                             #| wx.LC_HRULES
                             | wx.LC_SINGLE_SEL
                         )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.ilEventIcons = wx.ImageList(16, 16)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)
        thisDir = os_dirname(AppPath)
        self.IconIndex_Warning  = myIL.Add(wx.Bitmap(thisDir + '/Warning_16x16_32.ico',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconIndex_Info     = myIL.Add(wx.Bitmap(thisDir + '/Info_16x16_32.ico',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconIndex_Critical = myIL.Add(wx.Bitmap(thisDir + '/Critical_16x16_32.ico',
                                                     wx.BITMAP_TYPE_ICO))
        self._DataSource = DataSource
        self.firstItem = 0

        self.columns = []
        if not config.getboolean("StatusBox","ShowHeader"):
            self.SetSingleStyle(wx.LC_NO_HEADER)
        self.showIcon = config.getboolean("StatusBox","ShowIcon")
        if self.showIcon:
            self.columns.append(("",dict(width=20),None))
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

class EventStore(object):
    def __init__(self,config):
        self.config = config
        self.loadConfig()
        self.queue = Queue.Queue()
        self.listener = TextListener.TextListener(self.queue,
                                                  SharedTypes.BROADCAST_PORT_EVENTLOG,
                                                  retry = True,
                                                  name = "QuickGUI event log listener", logFunc = Log)
        self.eventDeque = collections.deque()
        self.firstEvent = 0

    def loadConfig(self):
        self.maxEvents = self.config.getint('EventManagerStream','Lines')

    def getQueuedEvents(self):
        n = self.maxEvents
        while True:
            try:
                line = self.queue.get_nowait()
                index,time,source,level,code,desc = [s.strip() for s in line.split("|",6)]
                date,time = [s.strip() for s in time.split()]
                eventTuple = (int(index),date,time,source,float(level[1:]),int(code[1:]),desc)
                # Level 1.5 = info only; message shows on both GUI and EventLog
                if eventTuple[4] >= 1.5:
                    self.eventDeque.append(eventTuple)
                while len(self.eventDeque) > n:
                    self.eventDeque.popleft()
                    self.firstEvent += 1
            except Queue.Empty:
                return

    def getFirstEventIndex(self):
        return self.firstEvent

    def getMaxEvents(self):
        return self.maxEvents

    def getEventCount(self):
        return len(self.eventDeque)

    def getEvent(self,item):
        if item<self.firstEvent:
            return None
        else:
            return self.eventDeque[item-self.firstEvent]
class StringDict(object):
    # Class which manages a dictionary of strings specified within a section of an INI file using keys with the same
    #  prefix
    @staticmethod
    def fromIni(config,secname,keyPrefix="string"):
        sl = StringDict()
        for opt in config.list_options(secname):
            if opt.startswith(keyPrefix.lower()):
                index = int(opt[len(keyPrefix):])
                sl.strings[index] = getInnerStr(config.get(secname,opt).strip())
        return sl
    def __init__(self):
        self.strings = {}
    def getString(self,index):
        return self.strings[index]
    def getStrings(self):
        return self.strings
    def addString(self, newStr):
        if newStr not in self.strings.values():
            newIdx = max(self.strings.keys())+1
            self.strings[newIdx] = newStr

class SubstDatabase(object):
    # The substitution database is used to store collections of compiled regular expressions for matching
    #  against an input string together with substitutions that may be applied to the input string
    #  to transform it for various purposes. The substitution may be a string, a list of strings or a
    #  dictionary of strings. The function applySubstitution returns a string, a list of strings or a
    #  dictionary of strings resulting from applying the most recent matching substitution to the input
    #  string.
    # If there is no matching entry in the substitution database, the returned value is None

    @staticmethod
    def fromIni(config,secname,keyPrefix="string",substPrefixList=[],defaultSubst=None):
        """Creates and returns a substitution database from a ConfigParser object."""
        db = SubstDatabase()
        if defaultSubst is None: defaultSubst = len(substPrefixList)*[r"\g<0>"]
        if not config.has_section(secname): return
        else:
            for opt in config.list_options(secname):
                if opt.startswith(keyPrefix.lower()):
                    index = int(opt[len(keyPrefix):])
                    str  = getInnerStr(config.get(secname,opt).strip())
                    # If the regular expression does not start with ^ or end with a $, append these
                    if not str.startswith("^"): str = "^" + str
                    if not str.endswith("$"): str = str + "$"
                    repl = []
                    for sp,default in zip(substPrefixList,defaultSubst):
                        try:
                            repl.append(getInnerStr(config.get(secname,"%s%d" % (sp.lower(),index,))))
                        except KeyError:
                            repl.append(default)
                    db.setSubstitution(index,str,repl)
        return db
    def __init__(self):
        self.dbase = {}
        self.sortedIndices = None
    def setSubstitution(self,index,regExp,subst,flags=re.IGNORECASE):
        self.dbase[index] = ((re.compile(regExp,flags),subst))
        self.sortedIndices = None
    def applySubstitution(self,input):
        # Finds the substitution with the largest index whose regex matches the input string
        if self.sortedIndices is None:
            self.sortedIndices = sorted(self.dbase.keys())
        for index in reversed(self.sortedIndices):
            regEx,subst = self.dbase[index]
            if re.match(regEx,input) is not None:
                if isinstance(subst,list):
                    return [re.sub(regEx,s,input) for s in subst]
                elif isinstance(subst,dict):
                    result = {}
                    for k in subst:
                        result[k] = re.sub(regEx,subst[k],input)
                    return result
                else:
                    return re.sub(regEx,subst,input)
        else:
            return None
    def match(self,input):
        # Returns match index if some regExp matches the input, -1 if no match
        if self.sortedIndices is None:
            self.sortedIndices = sorted(self.dbase.keys())
        for index in reversed(self.sortedIndices):
            regEx,subst = self.dbase[index]
            if re.match(regEx,input) is not None:
                return index
        else:
            return -1
#end of class SubstDatabase
class ColorDatabase(object):
    # The color database allows the user to give names to colors. A named color may be use to define
    #  another color, up to the maximum depth specified by maxIter. It is implemented by looking up color
    #  names is a dictionary (self.dbase) and recursively looking up the result until it is not found.
    #  The unknown key is assumed to be a hexadecimal color specification (as a string of the
    #  form "#RRGGBB") or a string describing one of the standard wxPython colors.
    maxIter = 10
    def __init__(self,config,secname):
        self.dbase = {}
        self.config = config
        self.secname = secname
    # We get the color from the config file on an "as-needed" basis, resolving any back references which may
    #  be present. This is necessary because the order of the keys in an INI file is required to be undefined,
    #  and we cannot assume that dependencies occur before usage.
    def getColor(self,name):
        name = name.lower()
        if name not in self.dbase:
            if self.config.has_option(self.secname,name):
                self.dbase[name] = self.getColor(getInnerStr(self.config.get(self.secname,name)).lower())
            else:
                return name
        return self.dbase[name]
    def removeColor(self,name):
        del self.dbase[name]
    def clear(self):
        self.dbase.clear()
#end of class ColorDatabase
class FontDatabase(object):
    default = {'font':'arial','pointsize':10,
               'italic':False,'bold':False,
               'foregroundcolor':'black','backgroundcolor':'white'}
    def __init__(self,config,secname):
        self.dbase = {}
        self.config = config
        self.secname = secname

    def parseDescr(self,descr):
        """Parse a font description in the INI file, returning a dictionary of the parameters"""
        try:
            d = dict([map(string.strip,map(string.lower,item.split(":"))) for item in descr.split(",")])
        except ValueError:
            raise ValueError,"Invalid font parameters (check punctuation):\n%s" % (descr,)

        # Check keynames and handle Booleans
        for k in d:
            if k not in self.default:
                raise KeyError("Unknown font description key: %s",k)
            # Booleans are special, "1","yes","true" and "on" are True
            #                       "0","no","false" and "off" are False
            if isinstance(self.default[k],bool):
                d[k] = normalizeBoolean(d[k])
            else:
                d[k] = type(self.default[k])(d[k])
        return d

    def getFont(self,name):
        """Returns a dictionary containing the parameters of the named font"""
        name = name.lower()
        if name not in self.dbase:
            if self.config.has_option(self.secname,name):
                descr = getInnerStr(self.config.get(self.secname,name)).lower()
                d = self.parseDescr(descr)
                self.dbase[name] = self.getFont(d["font"]).copy()
                del d["font"]
                self.dbase[name].update(d)
            else:
                self.dbase[name] = self.default.copy()
                self.dbase[name]["font"] = name
        return self.dbase[name]

    def getDefault(self):
        return self.default.copy()
#end of class FontDatabase


class DataStore(object):
    """
    Holds the data queried by AlarmViewListCtrl to update the alarm LEDs and names.
    """
    def __init__(self,config):
        self.config = config
        self.loadConfig()
        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject, retry = True)
        self.sourceDict = {}
        self.oldData = {}
        self.alarmStatus = 0
        self.mode = ""

    def loadConfig(self):
        self.seqPoints = self.config.getint('DataManagerStream','Points')

    def getQueuedData(self):
        """
        Get data from a queue.  The queue'd data is captured from the DataManager broadcast.
        The format is a dict of dicts.
        The top level dict keys are "data", "good", "mode", "source", "time", and "ver". See
        the MeasData.py wrapper class.

        good - True or 0.  Does this flag "measurement mode"?
        mode - warming_mode, CFADS_mode, etc. (Don't know where the definitions are nor how the
                value is set.
        source - sensors, analyze_CFADS.  Appears to contain a DataManager script name when there
                is a valid measurement.
        time - Unix timestamp. Source of timestamp...???
        ver - ???

        The value associated with the "data" key is a dict of hardware readings, fit parameters,
        and gas concentrations from DataManager.  For example. obj["data"]["CO2"] contains
        the CO2 gas concentration.

        What is happening below is not obvious.  To plot the data in a time series, we need several
        hundreds of points per data stream.  As there are at least several 10's of steams that can be
        selected for plotting we would have to push a lot of data through the RPC pipe if the QuickGui
        had to get all that data for each plot update.

        The data is collected in self.sourceDict and self.oldData.  When working with self.sourceDict
        it is bound to 'd'.

            d = self.sourceDict[source]

        When starting out self.sourceDict is empty so we initialize it with ring buffers n elements long.

            d[k] = GraphPanel.Sequence(n)

        Yes, Sequence is a ring buffer, not a Python sequence.
        As new data comes in, it is pushed, or added, to the ring buffer if it's not full, or overwrites
        an old value if we have reached capacity.

            d[k].Add(obj['data'][k])

        GetPointers() return the indicies of where the next data is added.  We track the pointers outside
        of the Sequence class so that we can advance the indices of ring buffers that don't receive new
        data in the current update event.  This is necessary keep all data on the same time axis range
        in the plots.
        """
        n = self.seqPoints
        while True:
            try:
                obj = self.queue.get_nowait()
                if "mode" in obj:
                    self.mode = obj["mode"]
                    #print("mode", self.mode)
                if "data" in obj and "ALARM_STATUS" in obj["data"]:
                    # diagnostics
                    #pprint.pprint(obj)
                    #time.sleep(1000)
                    self.alarmStatus = obj["data"]["ALARM_STATUS"]
                source = obj['source']
                if source not in self.oldData:
                    self.oldData[source] = {}

                if source not in self.sourceDict:
                    self.sourceDict[source] = {}
                    d = self.sourceDict[source]
                    d['good'] = GraphPanel.Sequence(n)
                    d['time'] = GraphPanel.Sequence(n)
                    for k in obj['data']:
                        d[k] = GraphPanel.Sequence(n)
                else:
                    d = self.sourceDict[source]
                # Find where new data have to be placed in the sequence
                cptrs = d['time'].GetPointers()
                for k in d:
                    try:
                        if k in ('time','good'):
                            d[k].Add(obj[k])
                        else:
                            d[k].Add(obj['data'][k])
                    except KeyError:
                        if k in self.oldData[source]:
                            d[k].Add(self.oldData[source][k].GetLatest())
                        else:
                            d[k].Add(0)
                for k in obj['data']:
                    if k not in d:
                        d[k] = GraphPanel.Sequence(n)
                        d[k].SetPointers(cptrs)
                        d[k].Add(obj['data'][k])
                self.oldData[source].update(d)
                time.sleep(0)
            except Queue.Empty:
                return

    def getSources(self):
        return sorted(self.sourceDict.keys())

    def getTime(self,source):
        return self.sourceDict[source]['time']

    def getKeys(self,source):
        return self.sourceDict[source].keys()

    def getDataSequence(self,source,key):
        return self.sourceDict[source][key]

#end of class DataStore
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

class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")


class QuickGui(wx.Frame):
    def __init__(self, configFile, defaultTitle = ""):

        # fullScreen sets the main view with no border and full screen.
        fullScreen = False

        if(fullScreen):
            styleSettings = (wx.CAPTION|wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL)
            wx.Frame.__init__(self,parent=None,id=-1,title='CRDS Data Viewer', style = styleSettings)
        else:
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
        self.SupervisorRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                                        APP_NAME,
                                                        IsDontCareConnection = False)
        self.configFile = configFile
        self.config = self.loadConfig(self.configFile)
        self.valveSeqOption = self.config.getboolean("ValveSequencer","Enable",True)
        self.numGraphs = max(1, self.config.getint("Graph","NumGraphs",1))
        self.colorDatabase = ColorDatabase(self.config,"Colors")
        self.fontDatabase = FontDatabase(self.config,"Fonts")
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
        self.dataStore  = DataStore(self.config)
        self.eventStore = EventStore(self.config)
        self.alarmInterface = AlarmInterface(self.config)
        self.alarmInterface.getAlarmData()
        self.sysAlarmInterface = SysAlarmInterface(self.config.getint("AlarmBox", "ledBlinkTime", 0) )
        self.dataLoggerInterface = DataLoggerInterface(self.config)
        self.dataLoggerInterface.getDataLoggerInfo()
        self.instMgrInterface = InstMgrInterface(self.config)
        
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
        self.imageDatabase = ImageDatabase()
        self.loadImageDatabase() # from ini file
        self.cavityTempS = None
        self.cavityTempT = None
        self.warmBoxTempS = None
        self.warmBoxTempT = None
        self.cavityPressureS = None
        self.cavityPressureT = None
        self.defaultLineMarkerColor = self.getColorFromIni("Graph","LineColor")
        self.defaultLineWidth = self.config.getfloat("Graph","LineWidth")
        self.defaultMarkerSize = self.config.getfloat("Graph","MarkerSize")
        self.lineMarkerColor = self.defaultLineMarkerColor
        self.restartUserLog = False
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

        # Get INI for peripheral interface and create an internal dictionary for later use
        self.periphStandardSourceKey = {}
        basePath = os.path.split(configFile)[0]
        self.rawPeriphDict = {}
        self.syncPeriphDict = {}
        try:
            periphIntrfConfig = os.path.join(basePath, self.config.get("PeriphIntrf", "periphIntrfConfig"))
            selectAll = self.config.getboolean("PeriphIntrf", "showAll", False)
            (self.rawPeriphDict, self.syncPeriphDict) = parsePeriphIntrfConfig(periphIntrfConfig,selectAll)
        except Exception, err:
            print "1280 %r Exception parsing peripheral interface config." % err

        # Add peripheral interface columns (if available) in standard mode
        if self.rawPeriphDict:
            self._addStandardKeys(self.rawPeriphDict)
        if self.syncPeriphDict:
            self._addStandardKeys(self.syncPeriphDict)

        # Set Windows platform type
        self.platform = platform()[:10]

        # Create the image panels with the frame as parent
        for key in self.imageDatabase.dbase:
            self.imageDatabase.setImagePanel(key,self)

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
        self.externalTools = {}
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
            self.Bind(wx.EVT_MENU, self.OnUserCal, id=self.idUserCal)

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
            self.Bind(wx.EVT_MENU, self.OnValveSeq, id=self.idValveSeq)

        self.menuBar.Append(self.iHelp,"Help")
        self.idABOUT = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idABOUT, "About", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)

        self.SetMenuBar(self.menuBar)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=self.idABOUT)

        self.Bind(wx.EVT_MENU, self.OnLoginUser, id=self.idLoginUser)

        self.Bind(wx.EVT_MENU, self.OnLockTime, id=self.idLockTime)
        self.iLockTime.Enable(self.numGraphs>1)
        self.Bind(wx.EVT_MENU, self.OnStatDisplay, id=self.idStatDisplay)
        self.Bind(wx.EVT_MENU, self.OnInstStatDisplay, id=self.idInstStatDisplay)        
        for tool in self.externalTools:
            self.Bind(wx.EVT_MENU, self.OnExternalTools, id=self.externalTools[tool]['id'])

        self.updateTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.OnTimer,self.updateTimer)
        self.updateTimer.Start(UPDATE_TIMER_INTERVAL)
        self.Bind(wx.EVT_IDLE,self.OnIdle)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        self.Bind(wx.EVT_PAINT,self.OnPaint)

        #Add session timer for inactive session timeout function of higher user level GUI mode
        self.sessionTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.OnSessionTimer,self.sessionTimer)

        self.session_time = 0

        self.layoutFrame()
        self.startServer()

        # The GTK has some graphics artifacts that can only be cleaned up after the
        # initial show event.  One clear example is the wx.ListCtrl automatic focus
        # which draws a rectangle around the first alarm LED + label.  The focus
        # rectangle can be removed with a call to Defocus() but this only works after
        # the entire QuickGui is shown.
        # Do one graphics refresh right after the window is fully drawn to clean
        # things up.
        self.OneShotTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.lateStart, self.OneShotTimer)
        self.OneShotTimer.Start(100, True)
        # Full screen for the Linux industrial platform.
        if(fullScreen):
            self.Maximize(True)
            self.ShowFullScreen(True, style = wx.FULLSCREEN_NOBORDER)

    def lateStart(self, evt):
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
        self.OnStatDisplay(evt, self.showStat)
        self.OnInstStatDisplay(evt, self.showInstStat)
        self.OnTimer(evt)

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
        except Exception, err:
            print "1403 %r" % err

    def enqueueViewerCommand(self, command, *args, **kwargs):
        self.commandQueue.put((command, args, kwargs))

    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_QUICK_GUI),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)
        self.rpcServer.register_function(self.setTitle)
        self.rpcServer.register_function(self.setLineMarkerColor)
        self.rpcServer.register_function(self.getLineMarkerColor)
        self.rpcServer.register_function(self.getDataKeys)
        self.rpcServer.register_function(self.setSysAlarmEnable)
        self.rpcServer.register_function(self.setDisplayedSource)
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.Destroy)
        self.rpcThread.start()

    #
    # RPC functions
    #
    def setTitle(self, newTitle):
        self.enqueueViewerCommand(self._setTitle,newTitle)
        return "OK"

    def setLineMarkerColor(self, lineMarkerColor=None, colorTime=None):
        """Set the graph line and marker color. The default value is defined in INI file"""
        if lineMarkerColor != None:
            self.lineMarkerColor = lineMarkerColor
        else:
            self.lineMarkerColor = self.defaultLineMarkerColor

        ds = self.dataStore
        for idx in range(self.numGraphs):
            if colorTime == None:
                cTime = ds.getTime(self.source[idx]).GetLatest()
            else:
                cTime = colorTime
            self.graphPanel[idx].AddColorTime(cTime)
            self.graphPanel[idx].AddColor(self.lineMarkerColor)
        return "New line color is %s" % self.lineMarkerColor

    def getLineMarkerColor(self):
        """Get the graph line and marker color."""
        return self.lineMarkerColor

    def getDataKeys(self, source=None):
        """Get all the data keys (column titles) for a given source or all the sources"""
        if source != None:
            return self.dataStore.getKeys(source)
        else:
            sources = self.getSourcesbyMode()
            retDict = {}
            for source in sources:
                retDict[source] = self.dataStore.getKeys(source)
            return retDict

    def setSysAlarmEnable(self, index, enable):
        """Enable/disable one of the system alarms"""
        self.sysAlarmInterface.setAlarm(index, enable)

    def setDisplayedSource(self, source):
        try:
            srcSel = self.sourceChoice[0].GetItems().index(source)
            for idx in range(len(self.sourceChoice)):
                self.sourceChoice[idx].SetSelection(srcSel)
                self.source[idx] = self.sourceChoice[idx].GetClientData(srcSel)
                self.graphPanel[idx].RemoveAllSeries()
                self.dataKey[idx] = None
                self.keyChoices[idx] = None
            return "OK"
        except Exception, err:
            return "%r" % err
    #
    # End of RPC functions
    #

    def loadConfig(self,configFile):
        config = CustomConfigObj(configFile)
        return config

    def loadImageDatabase(self):
        for secname in self.config.list_sections():
            if secname[:5].lower()=="image":
                self.imageDatabase.processConfigSection(self.config,secname,secname[5:].strip().lower())

    def getColorFromIni(self,section,name):
        return self.colorDatabase.getColor(getInnerStr(self.config.get(section,name)))

    def getFontFromIni(self,section,optionName="font"):
        """Reads font and color information from the requested section in a configuration file"""
        fontNames={'times':wx.ROMAN,'arial':wx.SWISS,'script':wx.SCRIPT,'courier':wx.TELETYPE,'fixed':wx.MODERN}
        def getValue(key,getter):
            if self.config.has_option(section,key): return getter(section,key)
            else: return fontDict[key]
        if self.config.has_option(section,optionName):
            fontDict = self.fontDatabase.getFont(getInnerStr(self.config.get(section,optionName)))
        else:
            fontDict = self.fontDatabase.getDefault()
        # Allow font parameters to be overridden within the section, if desired
        size = getValue("pointsize",self.config.getint)
        italicFlag = getValue("italic",self.config.getboolean)
        boldFlag = getValue("bold",self.config.getboolean)
        foregroundColour = self.colorDatabase.getColor(getValue("foregroundcolor",self.getColorFromIni))
        backgroundColour = self.colorDatabase.getColor(getValue("backgroundcolor",self.getColorFromIni))
        if italicFlag: style = wx.ITALIC
        else: style = wx.NORMAL
        if boldFlag: weight = wx.BOLD
        else: weight = wx.NORMAL
        faceName=fontDict["font"]
        if faceName in fontNames:
            font = wx.Font(size,fontNames[faceName],style,weight)
        else:
            font = wx.Font(size,wx.DEFAULT,style,weight,faceName=faceName)
        return font, foregroundColour, backgroundColour

    def layoutFrame(self):
        self.mainPanel = wx.Panel(parent=self,id=-1)
        font,fgColour,bgColour = self.getFontFromIni('Panel')
        self.mainPanel.SetBackgroundColour(bgColour)
        self.mainPanel.SetForegroundColour(fgColour)
        # Define the title band
        if self.defaultTitle:
            label = self.defaultTitle
        else:
            label=getInnerStr(self.config.get('Title','String'))
        self.titleLabel = wx.StaticText(parent=self.mainPanel, id=-1, label=label, style=wx.ALIGN_CENTER)
        setItemFont(self.titleLabel,self.getFontFromIni('Title'))

        # Define the footer band

        # Don't use the footer in INI file otherwise we have to change the year of each individual QuickGui.ini (more than 100 files) every year
        #copyLabel=getInnerStr(self.config.get('Footer','String'))
        copyLabel = "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0]
        footerLabel = wx.StaticText(parent=self.mainPanel, id=-1, label=copyLabel, style=wx.ALIGN_CENTER)
        setItemFont(footerLabel,self.getFontFromIni('Footer'))

        # Define the graph panels
        self.graphPanel = []
        font,fgColour,bgColour = self.getFontFromIni('Graph')
        for idx in range(self.numGraphs):
            gp = GraphPanel.GraphPanel(parent=self.mainPanel,id=-1)
            gp.SetGraphProperties(ylabel='Y',
                                   timeAxes=((self.config.getfloat("Graph","TimeOffset_hr"),
                                              self.config.getboolean("Graph","UseUTC")),False),
                                   grid=self.config.getboolean("Graph","Grid"),
                                   gridColour=self.getColorFromIni("Graph","GridColor"),
                                   backgroundColour=self.getColorFromIni("Graph","PaperColor"),
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
        setItemFont(self.userLogButton,self.getFontFromIni('MeasurementButtons'))
        self.userLogButton.State = False
        self.restartUserLog = False

        self.Bind(wx.EVT_BUTTON,self.OnUserLogButton,self.userLogButton)

        # Define the status log window
        logFileBox = wx.StaticBox(parent=self.mainPanel,id=1,label="Saved Data File")
        eventLogBox = wx.StaticBox(parent=self.mainPanel,id=-1,label="Measurement Status")
        height = self.config.getint("StatusBox","Height")
        if self.numGraphs > 2:
            height *= 0.8
        self.eventViewControl = EventViewListCtrl(parent=self.mainPanel,id=-1,config=self.config,
                                                  DataSource=self.eventStore,size=(-1,height))
        setItemFont(self.eventViewControl,self.getFontFromIni('StatusBox'))
        setItemFont(eventLogBox,self.getFontFromIni('Panel'))
        setItemFont(logFileBox,self.getFontFromIni('Panel'))

        self.userLogTextCtrl = wx.TextCtrl(parent=self.mainPanel,id=-1,#size=(-1,12),
                                        style=wx.TE_READONLY|wx.TE_RICH2|wx.TE_MULTILINE,
                                        value="No log file")
        setItemFont(self.userLogTextCtrl,self.getFontFromIni('UserLogBox'))

        eventLogBoxSizer = wx.StaticBoxSizer(eventLogBox,wx.HORIZONTAL)
        logFileBoxSizer = wx.StaticBoxSizer(logFileBox,wx.VERTICAL)
        logFileBoxSizer.Add(self.userLogButton, 0, wx.EXPAND)
        logFileBoxSizer.Add(self.userLogTextCtrl,1, wx.EXPAND|wx.ALL)
        eventLogBoxSizer.Add(self.eventViewControl,1, wx.EXPAND|wx.ALL)

        statusBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        statusBoxSizer.Add(logFileBoxSizer, proportion=1, flag=wx.EXPAND|wx.ALL)
        statusBoxSizer.Add(eventLogBoxSizer,proportion=1, flag=wx.EXPAND|wx.ALL)

        # Define the data selection tools
        toolPanel = wx.Panel(parent=self.mainPanel,id=-1)
        font,fgColour,bgColour = self.getFontFromIni('Graph')
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
            setItemFont(sourceLabel,self.getFontFromIni('Graph'))
            newId = wx.NewId()
            self.sourceChoiceIdList.append(newId)
            sc = wx.ComboBox(parent=toolPanel,id=newId,size=(150,-1),style=wx.CB_READONLY)
            setItemFont(sc,self.getFontFromIni('GraphTextBoxes'))
            self.Bind(wx.EVT_COMBOBOX,self.OnSourceChoice,sc)
            self.sourceChoice.append(sc)

            keyLabel = wx.StaticText(parent=toolPanel,id=-1,label="Data Key %d " % (idx+1))
            setItemFont(keyLabel,self.getFontFromIni('Graph'))
            newId = wx.NewId()
            self.keyChoiceIdList.append(newId)
            kc = wx.ComboBox(parent=toolPanel,id=newId,size=(200,-1),style=wx.CB_READONLY)
            setItemFont(kc,self.getFontFromIni('GraphTextBoxes'))
            self.Bind(wx.EVT_COMBOBOX,self.OnKeyChoice,kc)
            self.keyChoice.append(kc)

            precisionLabel = wx.StaticText(parent=toolPanel,id=-1,label="Precision ")
            setItemFont(precisionLabel,self.getFontFromIni('Graph'))
            newId = wx.NewId()
            self.precisionChoiceIdList.append(newId)
            pc = wx.ComboBox(parent=toolPanel,id=newId,size=(80,-1),style=wx.CB_READONLY,
                                       choices=["auto","0","1","2","3","4"],value="auto")
            setItemFont(pc,self.getFontFromIni('GraphTextBoxes'))
            self.Bind(wx.EVT_COMBOBOX,self.OnPrecisionChoice,pc)
            self.precisionChoice.append(pc)

            if self.showGraphZoomed:
                zoomedLabel = wx.StaticText(parent=toolPanel,id=-1,label="Zoomed")
                setItemFont(zoomedLabel,self.getFontFromIni('Graph'))
                zoomedStatus = wx.TextCtrl(parent=toolPanel,id=-1,size=(40,-1),
                                            style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="N")
                setItemFont(zoomedStatus,self.getFontFromIni('GraphTextBoxes'))
                self.zoomedList.append(zoomedStatus)

            newId = wx.NewId()
            self.autoYIdList.append(newId)
            autoYButton = wx.Button(parent=toolPanel,id=newId,size=(-1,25),label="Auto-scale Y")
            setItemFont(autoYButton,self.getFontFromIni('MeasurementButtons'))
            self.Bind(wx.EVT_BUTTON,self.OnAutoScaleY,autoYButton)
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
        setItemFont(self.clearButton,self.getFontFromIni('GraphButton'))
        self.Bind(wx.EVT_BUTTON,self.OnResetBuffers,self.clearButton)

        combToolSizer = wx.BoxSizer(wx.HORIZONTAL)
        combToolSizer.Add(choiceSizer,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM,border=10)
        combToolSizer.Add(self.clearButton,proportion=0,flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM,border=10)
        combToolSizer.Add((10,10),proportion=0)
        toolPanel.SetSizer(combToolSizer)

        # Panel for measurement result
        self.measPanel = wx.Panel(parent=self.mainPanel,id=-1)
        setItemFont(self.measPanel,self.getFontFromIni('MeasurementPanel'))

        # Alarm view
        alarmBox = wx.StaticBox(parent=self.measPanel,id=-1,label="Alarms")
        # Define the box height automatically instead of using INI file
        #size = self.config.getint("AlarmBox","Width"),self.config.getint("AlarmBox","Height")

        boxWidth = self.config.getint("AlarmBox","Width")
        if self.platform == "Windows-XP":
            boxHeight = 10 + self.numAlarmsDisplay * 15
        elif self.platform == "win32":
            # Win7
            boxHeight = self.numAlarmsDisplay * 20
        else:
            # Xubuntu
            boxHeight = self.numAlarmsDisplay * 40

        size = boxWidth,boxHeight

        font,fgColour,bgColour = self.getFontFromIni('AlarmBox','enabledFont')
        enabled = wx.ListItemAttr(fgColour,bgColour,font)
        font,fgColour,bgColour = self.getFontFromIni('AlarmBox','disabledFont')
        disabled = wx.ListItemAttr(fgColour,bgColour,font)

        self.alarmView = AlarmViewListCtrl(parent=self.measPanel,id=-1,attrib=[disabled,enabled],
                                           DataStore=self.dataStore, DataSource=self.alarmInterface,
                                           size=size, numAlarms=self.numAlarms)
        self.alarmView.SetMainForm(self)
        setItemFont(alarmBox,self.getFontFromIni('AlarmBox'))
        setItemFont(self.alarmView,self.getFontFromIni('AlarmBox'))

        # numSysAlarms = 1 will hide IPV Connectivity, default is 1 (hide IPV)
        numSysAlarms = min(2, self.config.getint("AlarmBox", "NumSysAlarms", 1))

        # System Alarm view
        # Define box height automatically
        #boxWidth = self.config.getint("AlarmBox","Width")

        if self.platform == "Windows-XP":
            boxHeight = numSysAlarms * 17
        elif self.platform == "win32":
            # Windows 7
            boxHeight = numSysAlarms * 20
        else:
            # Xubuntu
            boxHeight = numSysAlarms * 40

        size = boxWidth,boxHeight

        self.sysAlarmView = SysAlarmViewListCtrl(parent=self.measPanel,id=-1,attrib=[disabled,enabled],
                                           DataSource=self.sysAlarmInterface,
                                           size=size, numAlarms=numSysAlarms)
        self.sysAlarmView.SetMainForm(self)
        setItemFont(self.sysAlarmView,self.getFontFromIni('AlarmBox'))

        # Combine system alarm with concentration alarms
        alarmBoxSizer = wx.StaticBoxSizer(alarmBox,wx.VERTICAL)
        alarmBoxSizer.Add(self.sysAlarmView,proportion=0,flag=wx.EXPAND)
        alarmBoxSizer.Add(self.alarmView,proportion=0,flag=wx.EXPAND)

        # Instrument status panel
        self.instStatusBox = wx.StaticBox(parent=self.measPanel,id=-1,label="Instrument Status")
        size = self.config.getint("InstStatPanel","Width", 150),self.config.getint("InstStatPanel","Height", 70)
        self.instStatusPanel = InstStatusPanel(font=self.getFontFromIni('InstStatPanel'),
                                                parent=self.measPanel, id=-1, size=size
                                                )
        setItemFont(self.instStatusBox,self.getFontFromIni('InstStatPanel'))
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

            setItemFont(measLabel,self.getFontFromIni('MeasurementLabel'))
            self.measLabel.append(measLabel)

            measTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,pos=(50,100),size=(150,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,
                                        value="0.00")
            setItemFont(measTextCtrl,self.getFontFromIni('MeasurementBox'))
            self.measTextCtrl.append(measTextCtrl)

            resultSizer.Add(measLabel,proportion=0,flag=wx.ALIGN_CENTER)
            resultSizer.Add(measTextCtrl,proportion=1,flag=wx.ALIGN_CENTER)
            measDisplaySizer.Add(resultSizer,proportion=0,flag=wx.GROW | wx.LEFT | wx.RIGHT,border = 10)

            vs = wx.BoxSizer(wx.VERTICAL)
            st = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,label='mean')
            self.statControls.append(st)
            setItemFont(st,self.getFontFromIni('StatsLabel'))
            vs.Add(st,flag=wx.ALIGN_CENTER)

            meanTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,size=(40,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="0.00")
            setItemFont(meanTextCtrl,self.getFontFromIni('StatsBox'))
            self.statControls.append(meanTextCtrl)
            self.meanTextCtrl.append(meanTextCtrl)

            vs.Add(meanTextCtrl,flag=wx.EXPAND)
            statsSizer.Add(vs,proportion=1)

            vs = wx.BoxSizer(wx.VERTICAL)
            st = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,label='std dev')
            self.statControls.append(st)
            setItemFont(st,self.getFontFromIni('StatsLabel'))
            vs.Add(st,flag=wx.ALIGN_CENTER)

            stdDevTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,size=(40,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="0.00")
            setItemFont(stdDevTextCtrl,self.getFontFromIni('StatsBox'))
            self.statControls.append(stdDevTextCtrl)
            self.stdDevTextCtrl.append(stdDevTextCtrl)

            vs.Add(stdDevTextCtrl,flag=wx.EXPAND)
            statsSizer.Add(vs,proportion=1)

            vs = wx.BoxSizer(wx.VERTICAL)
            st = wx.StaticText(parent=self.measPanel,id=-1,style=wx.ALIGN_CENTER,label='slope')
            self.statControls.append(st)
            setItemFont(st,self.getFontFromIni('StatsLabel'))
            vs.Add(st,flag=wx.ALIGN_CENTER)

            slopeTextCtrl = wx.TextCtrl(parent=self.measPanel,id=-1,size=(40,-1),
                                        style=wx.TE_READONLY|wx.TE_CENTER|wx.TE_RICH2,value="0.00")
            setItemFont(slopeTextCtrl,self.getFontFromIni('StatsBox'))
            self.statControls.append(slopeTextCtrl)
            self.slopeTextCtrl.append(slopeTextCtrl)

            vs.Add(slopeTextCtrl,flag=wx.EXPAND)
            statsSizer.Add(vs,proportion=1)

            measDisplaySizer.Add(statsSizer,proportion=0,flag=wx.GROW | wx.LEFT | wx.RIGHT,border = 10)
            measDisplaySizer.Add((20,10),proportion=0)

        self.shutdownButton = wx.Button(parent=self.measPanel,id=wx.ID_EXIT,size=(75,65))
        setItemFont(self.shutdownButton,self.getFontFromIni('MeasurementButtons'))
        self.Bind(wx.EVT_BUTTON,self.OnShutdownButton,self.shutdownButton)

        self.measPanelSizer = wx.BoxSizer(wx.VERTICAL)
        # Next line defines width of panel
        panelWidth = 250

        logoSizer = wx.BoxSizer(wx.VERTICAL)
        logoBmp = wx.Bitmap(os_dirname(AppPath)+'/logo.png',wx.BITMAP_TYPE_PNG)
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
        setItemFont(graphBox,self.getFontFromIni('Panel'))

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
        self.modifyInterface()

    def modifyInterface(self):
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
            self.OnSourceChoice(obj=sc)
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

    def getSourcesbyMode(self):
        s = self.dataStore.getSources()
        if self.userLevel < 3:
            if self.sourceStandardModeDatabase != None:
                s = [t for t in s if self.sourceStandardModeDatabase.match(t)>=0]
            else:
                s = [t for t in s if t in self.standardModeSourcesDict.getStrings().values()]
        return s

    def getKeysbyMode(self,source):
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

    def OnShutdownButton(self,evt):
        # Shutdown Modes (modes are defined in InstMgr.py)
        # mode == 0 shutdown all processes and power off the analyzer
        # mode == 1 shutdown all process and exit to the desktop
        # mode == 2 shutdown host, leave driver running, exit to desktop
        #
        # click ShutDown button -> mode 0
        # click Shutdown button while holding down SHIFT -> mode 1
        # click Shutdown button while holding down SHIFT + CTRL -> mode 2
        #
        shutdownMode = 0
        message = "Do you really want to shutdown the analyzer?"
        if wx.GetKeyState(wx.WXK_SHIFT) and wx.GetKeyState(wx.WXK_CONTROL):
            shutdownMode = 2
        elif wx.GetKeyState(wx.WXK_SHIFT):
            shutdownMode = 1

        dialog = wx.MessageDialog(self, message, "Analyzer Shut Down", style=wx.YES_NO | wx.ICON_QUESTION)
        retCode = dialog.ShowModal()
        if retCode == wx.ID_YES:
            try:
                self.setDisplayedSource(self.shutdownShippingSource)
            except Exception, err:
                print "2003 %r" % err

            self.instMgrInterface.instMgrRpc.INSTMGR_ShutdownRpc(shutdownMode)
        dialog.Destroy()
        self.shutdownButton.Enable(False)

    def OnResetBuffers(self,evt):
        for s in self.dataStore.getSources():
            self.dataStore.getDataSequence(s,'time').Clear()
            self.dataStore.getDataSequence(s,'good').Clear()
            for k in self.dataStore.getKeys(s):
                self.dataStore.getDataSequence(s,k).Clear()
    def OnSourceChoice(self, evt=None, obj=None):
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
    def OnKeyChoice(self,evt):
        idx = self.keyChoiceIdList.index(evt.GetEventObject().GetId())
        self.dataKey[idx] = self.keyChoice[idx].GetClientData(evt.GetSelection())
        self.dataKeyUpdateAction(idx)
    def dataKeyUpdateAction(self, idx):
        if not self.dataKey[idx]: return
        ds = self.dataStore
        self.graphPanel[idx].RemoveAllSeries()
        series = GraphPanel.Series(ds.getTime(self.source[idx]),ds.getDataSequence(self.source[idx],self.dataKey[idx]))
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

        #self.graphPanel[idx].AddSeriesAsLine(series,selection,statsFlag=True,width=self.defaultLineWidth)
        #self.graphPanel[idx].AddSeriesAsPoints(series,selection,marker=getInnerStr(self.config.get("Graph","Marker")),size=self.defaultMarkerSize)
        #if self.graphPanel[idx].getNumColors() == 0:
        #    self.graphPanel[idx].AddColor(self.lineMarkerColor)
        #
        # The above code block forces the line and points to be the same color.
        # Below we set line and marker color based upon the QuickGui ini file.
        # RSF
        #
        self.graphPanel[idx].AddSeriesAsLine(series,selection,statsFlag=True,width=self.defaultLineWidth, colour=getInnerStr(self.config.get("Graph","LineColor")))
        self.graphPanel[idx].AddSeriesAsPoints(series,selection,marker=getInnerStr(self.config.get("Graph","Marker")),size=self.defaultMarkerSize,colour=getInnerStr(self.config.get("Graph","MarkerColor")))

        # When changing data keys, if the panel is currently zoomed, we want to keep the x-axis locked but
        # unlock the y-axis in order to show the data of the new key. To do so, we first un-zoom the panel,
        # update it to auto-scale in y-axis only, and then we remove the x-axis enforcement and set it in zoomed mode.
        if not self.graphPanel[idx].GetUnzoomed():
            self.autoScaleY(idx)
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

    def OnAutoScaleY(self, evt):
        idx = self.autoYIdList.index(evt.GetEventObject().GetId())
        self.autoScaleY(idx)

    def autoScaleY(self, idx):
        if self.graphPanel[idx].GetUnzoomed():
            self.graphPanel[idx].Update(autoscaleY=True)
        else:
            xAxis = self.graphPanel[idx].GetLastDraw()[1]
            self.graphPanel[idx].SetUnzoomed(True)
            self.graphPanel[idx].SetForcedXAxis(tuple(xAxis))
            self.graphPanel[idx].Update(autoscaleY=True)
            self.graphPanel[idx].ClearForcedXAxis()
            self.graphPanel[idx].SetUnzoomed(False)

    def OnPrecisionChoice(self,evt):
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

    def OnIdle(self,event):
        while not self.commandQueue.empty():
            func, args, kwargs = self.commandQueue.get()
            func(*args, **kwargs)
        event.Skip()

    def _setTitle(self,title):
        """Sets the title and refreshes main panel so that title is recentered"""
        self.titleLabel.SetLabel(title)
        self.mainPanel.SendSizeEvent()

    def OnUserLogButton(self,evt):
        self.userLogButton.Disable()
        userLogs = self.dataLoggerInterface.userLogDict.keys()
        if self.userLogButton.State:
            self.dataLoggerInterface.startUserLogs(userLogs, self.restartUserLog)
        else:
            self.dataLoggerInterface.stopUserLogs(userLogs)
        wx.FutureCall(5000,self.userLogButton.Enable)

    def OnTimer(self,evt):
        defaultSourceIndex = None
        self.dataStore.getQueuedData()
        self.eventStore.getQueuedEvents()
        if not self.alarmInterface.alarmData:
            self.alarmInterface.getAlarmData()
        #self.sysAlarmInterface.getStatus(0)
        sources = self.getSourcesbyMode()
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
                keyChoices = self.getKeysbyMode(self.source[idx])
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
                    self.dataKeyUpdateAction(idx)

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

            if self.dataStore != None and self.source[idx] != None and self.dataKey[idx] != None:
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

    def OnLockTime(self, evt):
        """
        Lock/Unlock the time axis of all charts.
        """
        if self.lockTime:
            self.lockTime = False
            self.iLockTime.Check(False)
        else:
            self.lockTime = True
            self.iLockTime.Check(True)
        self.OnTimer(evt)
        return

    def OnStatDisplay(self, evt = None, showNow = None):
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

    def OnInstStatDisplay(self, evt = None, showNow = None):
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

        if showStats:
            try:
                self.cavityTempS = self.driverRpc.rdDasReg("CAVITY_TEMP_CNTRL_SETPOINT_REGISTER")
                self.cavityTempT = self.driverRpc.rdDasReg("CAVITY_TEMP_CNTRL_TOLERANCE_REGISTER")
                self.warmBoxTempS = self.driverRpc.rdDasReg("WARM_BOX_TEMP_CNTRL_SETPOINT_REGISTER")
                self.warmBoxTempT = self.driverRpc.rdDasReg("WARM_BOX_TEMP_CNTRL_TOLERANCE_REGISTER")
            except:
                pass
            try:
                self.cavityPressureS = self.sampleMgrRpc.ReadOperatePressureSetpoint()
                cavityPressureTPer = self.sampleMgrRpc.ReadPressureTolerancePer()
                self.cavityPressureT = cavityPressureTPer*self.cavityPressureS
            except:
                self.cavityPressureS = 140.0
                self.cavityPressureT = 5.0

        self.instStatusBox.Show(showStats)
        self.instStatusPanel.Show(showStats)
        self.iInstStatDisplay.Check(showStats)
        self.measPanelSizer.Layout()
        self.Refresh()

    def OnUserCal(self, evt):
        concList = self.dataManagerRpc.Cal_GetMeasNames()
        if len(concList) == 0:
            d = Dialog.OKDialog(self,"User calibration not allowed, action cancelled.",None,-1,"User Calibration Disabled")
            d.ShowModal()
            d.Destroy()
            return

        # Use password to protect user cal function
        d = wx.TextEntryDialog(self, 'User Calibration Password: ','Authorization required', '', wx.OK | wx.CANCEL | wx.TE_PASSWORD)
        setItemFont(d,self.getFontFromIni("Dialogs"))
        try:
            password = getInnerStr(self.config.get("Authorization","UserCalPassword"))
        except:
            password = "picarro"
        okClicked = d.ShowModal() == wx.ID_OK
        d.Destroy()
        if not okClicked:
            return
        elif d.GetValue() != password:
            d = Dialog.OKDialog(self,"Password incorrect, action cancelled.",None,-1,"Incorrect Password")
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
        self.BindAllWidgetsMotion(self.dlg)
        getUserCals = (self.dlg.ShowModal() == wx.ID_OK)
        if getUserCals:

            numConcs = len(userCalList)/2
            for idx in range(numConcs):
                if self.dlg.textCtrlList[2*idx].GetValue() != userCalList[2*idx][2] or self.dlg.textCtrlList[2*idx+1].GetValue() != userCalList[2*idx+1][2]:
                    newCal = (float(self.dlg.textCtrlList[2*idx].GetValue()), float(self.dlg.textCtrlList[2*idx+1].GetValue()))
                    self.dataManagerRpc.Cal_SetSlopeAndOffset(concList[idx], newCal[0], newCal[1])

        self.dlg.Destroy()

    def OnExternalTools(self, evt):
        menu_id = evt.GetId()
        obj = evt.GetEventObject()
        label = obj.GetLabelText(menu_id)
        subprocess.Popen(self.externalTools[label]['cmd'].split()) 

    def OnValveSeq(self, evt):
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

    def OnPulseAnalyzerParam(self, evt):
        errorMsg = ""
        if not self.pulseSource:
            errorMsg = "Pulse Analyzer source not specified"
        else:
            try:
                concList = self.dataManagerRpc.PulseAnalyzer_GetParam(self.pulseSource,"allConcList")
                if concList == "Failed":
                    errorMsg = "Unable to modify Pulse Analyzer"
                elif len(concList) == 0:
                    errorMsg = "Pulse Analyzer not defined"
                else:
                    pass
            except:
                errorMsg = "Connection to Pulse Analyzer failed"
        if errorMsg:
            d = Dialog.OKDialog(self,errorMsg,None,-1,"Error")
            d.ShowModal()
            d.Destroy()
            return

        concThresList = []
        pulseConfigList = []
        for conc in concList:
            concThresList.append((conc, "%s threshold" % conc, str(self.dataManagerRpc.PulseAnalyzer_GetParam(self.pulseSource,"threshold",conc))))
        concThresList.sort()
        pulseConfigList.append(("waitTime", "Wait Time (seconds)", str(self.dataManagerRpc.PulseAnalyzer_GetParam(self.pulseSource,"waitTime"))))
        pulseConfigList.append(("triggerTime", "Trigger Time (seconds)", str(self.dataManagerRpc.PulseAnalyzer_GetParam(self.pulseSource,"triggerTime"))))
        pulseConfigList.append(("bufSize", "Buffer Size", str(self.dataManagerRpc.PulseAnalyzer_GetParam(self.pulseSource,"bufSize"))))
        dlg = PulseAnalyzerGui((concThresList+pulseConfigList), None, -1, "")
        getParamVals = (dlg.ShowModal() == wx.ID_OK)
        if getParamVals:
            numThres = len(concThresList)
            numConfigParam = len(pulseConfigList)
            for idx in range(numThres):
                if dlg.textCtrlList[idx].GetValue() != concThresList[idx][2]:
                    self.dataManagerRpc.PulseAnalyzer_SetParam(self.pulseSource,"threshold",float(dlg.textCtrlList[idx].GetValue()),concThresList[idx][0])
            for idx in range(numConfigParam):
                if dlg.textCtrlList[idx+numThres].GetValue() != pulseConfigList[idx][2]:
                    pulseConfigName = pulseConfigList[idx][0]
                    if pulseConfigName in ["bufSize"]:
                        self.dataManagerRpc.PulseAnalyzer_SetParam(self.pulseSource,pulseConfigName,int(dlg.textCtrlList[idx+numThres].GetValue()))
                    else:
                        self.dataManagerRpc.PulseAnalyzer_SetParam(self.pulseSource,pulseConfigName,float(dlg.textCtrlList[idx+numThres].GetValue()))
        dlg.Destroy()

    def OnSize(self,evt):
        w, h = self.GetClientSizeTuple()
        for key in self.imageDatabase.dbase:
            self.imageDatabase.placeImage(key,(w,h))
        evt.Skip()

    def OnPaint(self,evt):
        w, h = self.GetClientSizeTuple()
        for key in self.imageDatabase.dbase:
            self.imageDatabase.placeImage(key,(w,h))
        evt.Skip()

    def OnAbout(self,e):
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

        d = Dialog.OKDialog(self,v,None,-1,aboutTitle, boldText=boldText)
        if biggerSize:
            currSize = d.GetSize()
            d.SetSize((currSize[0]+40, currSize[1]))
        d.ShowModal()
        d.Destroy()

    def sendRequest(self, action, api, payload, useToken=False):
        """
        action: 'get' or 'post'
        useToken: set to True if the api requires token for authentication
        """
        if useToken:
            header = {'Authentication': self.current_user["token"]}
        else:
            header = {}
        actionFunc = getattr(self.hostSession, action)
        try:
            response = actionFunc(FLASK_SERVER_URL + api, data=payload, headers=header)
            return response.json()
        except Exception, err:
            return {"error": str(err)}

    def getSystemVariables(self):
        returnDict = self.sendRequest("get", "system", {'command':'get_all_variables'})
        self.sessionLifeTime = int(returnDict["user_session_lifetime"]) * 60

    def OnLoginUser(self,e):
        # Set the GUI mode based on the userlevels. When change to higher levels Technician/Expert, it sends the authentication requests 
        # to the flask_security server. If Technician/Expert mode stays inactive for a period of time (default 30 secs), it will automatically log out
        # and the GUI mode changes to the default.  
        # d = wx.TextEntryDialog(self, 'Service Technician Log In: ','Authorization required', 'Email:', wx.OK | wx.CANCEL | wx.TE_PASSWORD)

        # toggle login/logout
        if not self.userLoggedIn:
            user, msg = "", ""
            while True:
                d = Dialog.LoginDialog(self, title="Authorization required", user=user, msg=msg)
                setItemFont(d,self.getFontFromIni("Dialogs"))
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
                        returnDict = self.sendRequest("post", "account", payload)       
                    if "error" in returnDict:
                        msg = returnDict["error"]
                        if "Password expire" in msg:
                            msg = self.OnChangePwd(user, pwd)
                            if len(msg) == "":
                                break
                    elif "roles" in returnDict:
                        self.userLevel = self.userLevelMap[returnDict["roles"][0]]
                        d = Dialog.OKDialog(self,"\t%s logged in." % (returnDict["roles"][0]),None,-1,"") 
                        #update GUI
                        self.modifyInterface()
                        self.measPanelSizer.Layout()
                        self.Refresh()
                        self.userLoggedIn = True
                        self.iGuiMode.SetItemLabel("User Logout")
                        #Recursively bind all the widgets with mouse motion event 
                        self.BindAllWidgetsMotion(self.mainPanel)
                        if self.userLevel < 4:
                            self.getSystemVariables()
                            #Inactive session timeout timer
                            self.sessionTimer.Start(5000) # 5 seconds interval
                            d.ShowModal()
                            d.Destroy()
                        break                    
        else:
            self.userLevel = 0
            self.modifyInterface()
            self.measPanelSizer.Layout()
            self.Refresh()
            self.menuBar.EnableTop(1, False)
            self.menuBar.EnableTop(2, False)
            self.userLoggedIn = False
            self.iGuiMode.SetItemLabel("User Login")
            #recursively unbind all the widgets
            self.UnbindAllWidgetsMotion(self.mainPanel)
            self.sessionTimer.Stop()

    def OnChangePwd(self, username, password):
        msg = "Password Expired! Must change password."
        while True:
            d = Dialog.ChangePasswordDialog(self, msg=msg)
            setItemFont(d, self.getFontFromIni("Dialogs"))
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
                
                returnDict = self.sendRequest("post", "account", payload)                
                if "error" in returnDict:
                    msg = returnDict["error"]
                else:
                    return "Password updated! Please log in."

    # reset the timer everytime a mouse motion is detected        
    def SessionRefresher(self, e):
        if self.sessionTimer.IsRunning():
            self.session_time = 0
        e.Skip()

    # count the session_time, logout and change GUI mode to the default
    # automatically after session_time exceed the INACTIVE_SESSION_TIMEOUT
    def OnSessionTimer(self, event):
        if self.session_time >= self.sessionLifeTime:
            self.userLevel = 0
            self.modifyInterface()
            self.measPanelSizer.Layout()
            self.Refresh()
            self.menuBar.EnableTop(1, False)
            self.menuBar.EnableTop(2, False)
            self.userLoggedIn = False
            self.iGuiMode.SetItemLabel("User Login")
            self.UnbindAllWidgetsMotion(self.mainPanel)
            try:
                self.dlg.Destroy()
                self.UnbindAllWidgetsMotion(self.dlg)
            except:
                pass
            self.sessionTimer.Stop()
        else:
            #timer runs every 5 secs, count
            self.session_time += 5

    #DFS algorithm to recursively traverse the widgets tree. Bind/Unbind mouse motion             
    def BindAllWidgetsMotion(self, node):
        for child in node.GetChildren():
            self.BindAllWidgetsMotion(child)
        node.Bind(wx.EVT_MOTION,self.SessionRefresher)
        return
        
    def UnbindAllWidgetsMotion(self, node):
        for child in node.GetChildren():
            self.UnbindAllWidgetsMotion(child)
        node.Unbind(wx.EVT_MOTION)
        return
    
#end of class QuickGui
HELP_STRING = \
"""\
QuickGui.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "./QuickGui.ini"
-t  Specify the GUI title

"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:t:'
    longOpts = ["help","test"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "2628 %s %r" % (data, data)
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

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    if "-t" in options:
        defaultTitle = options["-t"]
    else:
        defaultTitle = ""

    return (configFile, defaultTitle)

if __name__ == "__main__":
    app = wx.PySimpleApp(False)
    app.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
    configFile, defaultTitle = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    frame = QuickGui(configFile, defaultTitle)
    frame.Show()
    app.MainLoop()
    Log("Exiting program")