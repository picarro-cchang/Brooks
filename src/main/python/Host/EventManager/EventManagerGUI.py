#!/usr/bin/python
#
# File Name: EventManagerGUI.py
#
# Purpose:
#
#   This is the GUI for the main EventManager application.
#
# Notes:
#
# File History:
# 06-02-18 russ  First release
# 06-05-10 russ  Switched level 1 (normal) and level 0 (debug) event icons to reduce icon clutter
# 06-06-19 russ  threading.Timer fix to prevent local time changes causing problems
# 06-10-26 russ  Support for changing the underlying data source for events
# 06-12-20 russ  Added ms reading to the event time
# 08-04-04 sze   Added Linux compatibility
# 10-01-22 sze   Changed date format display to ISO standard
import wx
import wx.lib.mixins.listctrl as listmix
import Queue
import sys
import time
if sys.platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp
import Host.EventManager.EventManager as EventManager
import threading
if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes

from os.path import dirname as os_dirname
from os.path import abspath

MIN_REFRESH_PERIOD_s = 0.2

def GetSelfPath():
    "adapted from a c.l.py thread here: http://tinyurl.com/nrg6o"
    if hasattr(sys, "frozen"): #we're running compiled with py2exe
        return sys.executable
    else:
        return abspath(sys.argv[0])

class EventViewListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """ListCtrl that auto-sizes the right-most column to fit the width.

    DataSource must be the list of Event objects that are to be displayed.
    """
    def __init__(self, parent, ID, DataSource, EventSourceList = [], pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        wx.ListCtrl.__init__(self, parent, ID, pos, size,
                             style = wx.LC_REPORT
                                   | wx.LC_VIRTUAL
                                   #| wx.BORDER_SUNKEN
                                   | wx.BORDER_NONE
                                   # wx.LC_EDIT_LABELS
                                   #| wx.LC_SORT_ASCENDING
                                   #| wx.LC_NO_HEADER
                                   #| wx.LC_VRULES
                                   | wx.LC_HRULES
                                   | wx.LC_SINGLE_SEL
                             )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self._DataSource = DataSource
        self._EventSourceList = EventSourceList
        self.EnsureLatestEventOnscreen = True
        self.ShowEventDate = False
        self.ColourCodeSources = True

        colourList = [
                        "#FFFFFF",
                        "#FFFFD4",
                        "#AAD4FF",
                        "#D4D4FF",
                        "#CCFFCC",
                        "#FFD4AA",
                        "#D2D2D2",
                        "#FFD4D4",
                        "#F77979",
                        "#F89008",
                        "#00AAFF",
                        "#FFFF55",
                        "#D4FFFF",
                        ]
        self.ColourAttr = []
        for i in range(len(colourList)):
            attr = wx.ListItemAttr()
            attr.SetBackgroundColour(colourList[i])
            self.ColourAttr.append(attr)

        self.InsertColumn(0, "Index", wx.LIST_FORMAT_RIGHT, width = 70)
        self.InsertColumn(1, "Time", width = 140)
        self.InsertColumn(2, "Source", width = 100)
        self.InsertColumn(3, "Code", width = 50)
        self.InsertColumn(4, "Desc", width = 300)

        self.ilEventIcons = wx.ImageList(16, 16)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)

        thisDir = os_dirname(GetSelfPath())
        self.IconIndex_Warning  = myIL.Add(wx.Bitmap(thisDir + '/Warning_16x16_32.ico', wx.BITMAP_TYPE_ICO))
        self.IconIndex_Info     = myIL.Add(wx.Bitmap(thisDir + '/Info_16x16_32.ico', wx.BITMAP_TYPE_ICO))
        self.IconIndex_Critical = myIL.Add(wx.Bitmap(thisDir + '/Critical_16x16_32.ico', wx.BITMAP_TYPE_ICO))

        self.EvenRowAttr = wx.ListItemAttr()
        self.EvenRowAttr.SetBackgroundColour("#FFFFF0")

    def _RefreshList(self):
        try:
            eventCount = len(self._DataSource)
            self.SetItemCount(eventCount)
            if self.EnsureLatestEventOnscreen:
                #print eventCount, "on screen!"
                self.EnsureVisible(eventCount - 1)
        except Exception, E:
            print "Exception trapped in _RefreshList: %r %s" % (E,E)
            pass

    def OnGetItemText(self, item, col):
        try:
            if col == 0: #idx
                return "%s" % (self._DataSource[item].Index,)
            elif col == 1: #time
                if self.ShowEventDate:
                    ret = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._DataSource[item].EventTime))
                else:
                    ret = time.strftime("%H:%M:%S", time.localtime(self._DataSource[item].EventTime))
                ms = int(self._DataSource[item].EventTime * 1000) % 1000
                ret += ".%03d" % ms
                return ret
            elif col == 2: #source
                return "%s" % self._DataSource[item].Source
            elif col == 3: #code
                return "%s" % self._DataSource[item].Event.Code
            elif col == 4: #desc
                msg = self._DataSource[item].Event.Description
                if self._DataSource[item].Data:
                    msg += " : %s" % (self._DataSource[item].Data,)
                return msg
        except IndexError:
            #Likely due to the EventList getting shrunk behind the scenes so our item index is now too big.
            #Ignore it for now... likely a better way to deal with this, but don't know it at the moment.
            #In any case, the viewing of the data should NEVER affect the actual logging.
            pass

    def OnGetItemImage(self, item):
        try:
            evtLevel = self._DataSource[item].Event.Level
            if evtLevel == 0: #debug
                return self.IconIndex_Info
            elif evtLevel == 1:
                return -1
            elif evtLevel == 2:
                return self.IconIndex_Warning
            elif evtLevel == 3: #Major
                return self.IconIndex_Critical
        except IndexError:
            #Likely due to the EventList getting shrunk behind the scenes so our item index is now too big.
            #Ignore it for now... likely a better way to deal with this, but don't know it at the moment.
            #In any case, the viewing of the data should NEVER affect the actual logging.
            pass

    def OnGetItemAttr(self, item):
        try:
            if self.ColourCodeSources:
                sourceName = self._DataSource[item].Source
                colourIndex = self._EventSourceList.index(sourceName)
                if (colourIndex + 1) > len(self.ColourAttr):
                    return None
                else:
                    return self.ColourAttr[colourIndex]
            else:
                if item % 2 == 0:
                    return self.EvenRowAttr
                else:
                    return None
        except IndexError:
            #Likely due to the EventList getting shrunk behind the scenes so our item index is now too big.
            #Ignore it for now... likely a better way to deal with this, but don't know it at the moment.
            #In any case, the viewing of the data should NEVER affect the actual logging.
            pass

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.debug_mode = False

    def Initialize(self, DataSource = None, SourceEventCounter = None, EventSourceList = None, CommandQueue = None):
        self._EventList = DataSource #will hold a reference to the main event list (or BE it in debug mode)
        self._SourceEventCounter = SourceEventCounter #contains a dictionary of source names and event counts
        self._EventSourceList = EventSourceList #the list of unique event sources
        self.commandQueue = CommandQueue

        self.CurrentEventListItem = None
        self.CurrentEventListEventLog = None

        self.SetTitle("Event Manager - Event Viewer")
        self.SetBackgroundColour('#191970')
        self.SetForegroundColour('#FFFFFF')
        self.MakeWidgets()
        self.PrepareMenuBar()
        self.PrepareStatusBar()
        self.DoLayout()
        self.BindEvents()
        self.PrepareTimers()

    def PrepareTimers(self):
        self.Bind(wx.EVT_TIMER, self.OnCommandTimer)
        self.commandTimer = wx.Timer(self)
        self.commandTimer.Start(500)
        if self.debug_mode:
            self.Bind(wx.EVT_TIMER, self.OnTimer_ForDEBUG)
            self.ticks = 0
            self.timer1 = wx.Timer(self)
            self.timer1.Start(10)
        pass

    def OnClose(self, Event):
        #print "Close attempted"
        sys.exit()

    def OnFinish(self, Event):
        print "ONFINISH EXECUTED"
        #Event.Skip()

    def BindEvents(self):
        #self.lstEventLog.Bind(wx.EVT_SCROLLWIN, self.On_lstEventLog_Scroll)
        self.chkTrackLatestEvent.Bind(wx.EVT_CHECKBOX, self.On_chkTrackLatestEvent_Check)
        self.chkShowEventDate.Bind(wx.EVT_CHECKBOX, self.On_chkShowEventDate_Check)
        self.chkColourCodeSources.Bind(wx.EVT_CHECKBOX, self.On_chkColourCodeSources_Check)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.On_lstEventLog_ItemSelected, self.lstEventLog)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        #self.Bind(wx.EVT_QUERY_END_SESSION, self.OnFinish)

    def On_lstEventLog_ItemSelected(self, Event):
        idx = Event.m_itemIndex
        self.CurrentEventListIndex = idx
        self.CurrentEventListEventLog = self.lstEventLog._DataSource[idx]
        evtLog = self.CurrentEventListEventLog

        if 0: assert isinstance(evtLog, EventManager.EventLogger.EventLog) #for Wing
        self.tlblEventTime.SetLabel(   time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(evtLog.EventTime)))
        self.tlblEventCode.SetLabel(   str(evtLog.Event.Code))
        self.tlblEventID.SetLabel(     str(evtLog.Index))
        #print evtLog.Index
        self.tlblEventLevel.SetLabel(  str(evtLog.Event.Level))
        self.chkEventPublic.SetValue(  evtLog.Event.Public)
        self.tlblEventSource.SetLabel( evtLog.Source)
        msg = evtLog.Event.Description
        if evtLog.Data:
            msg += " : %s" % (evtLog.Data,)
        self.tlblEventText.SetLabel(   msg)
        self.txtEventVerbose.SetValue(evtLog.Event.VerboseDescription or "<no verbose description available>")
        Event.Skip()

    def On_chkTrackLatestEvent_Check(self, event):
        cb = event.GetEventObject()
        assert isinstance(cb,wx.CheckBox)
        self.lstEventLog.EnsureLatestEventOnscreen = cb.GetValue()

    def On_chkShowEventDate_Check(self, event):
        cb = event.GetEventObject()
        assert isinstance(cb,wx.CheckBox)
        self.lstEventLog.ShowEventDate = cb.GetValue()
        self.lstEventLog.RefreshItems(1, len(self.lstEventLog._DataSource))

    def On_chkColourCodeSources_Check(self, event):
        cb = event.GetEventObject()
        assert isinstance(cb,wx.CheckBox)
        self.lstEventLog.ColourCodeSources = cb.GetValue()
        self.lstEventLog.RefreshItems(1, len(self.lstEventLog._DataSource))

    def On_lstEventLog_Scroll(self, event):
        #print "scroll event %s" % event
        self.lstEventLog.EnsureLatestEventOnscreen = False
        self.chkTrackLatestEvent.SetValue(self.lstEventLog.EnsureLatestEventOnscreen)
        event.Skip()

    def OnCommandTimer(self,event):
        """The command timer runs commands enqueued by the EventLog thread within the GUI thread and
        refreshes the event view control"""

        self.lstEventLog._RefreshList()

        if self.commandQueue != None:
            while True:
                try:
                    command = self.commandQueue.get(block = False)
                    command()
                except Queue.Empty:
                    break

    def OnTimer_ForDEBUG(self, event):
        """This is a debug timer ONLY.
        """
        import random
        itemCount = self.lstEventLog.GetItemCount()
        #idx = self.lstEventLog.InsertImageStringItem(sys.maxint, str(itemCount), random.choice([0,1,2]))
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())

#    thisEvent = self._CreateEventLog("Log %s of %s generated with Debug_LogMany." % (i+1, Count))
#    self._AddEventLog(thisEvent)
#    time.sleep(Delay_s)

        eventSource = random.choice(['Test_1','Test_2','Test_3'])
        eventCode = str(random.choice([0,100, 200]))
        eventDesc = random.choice(["This is a test!", "Unga bunga!", "I hope this worked!"])
        eventLevel = random.choice([0,1,2,3])

        thisEvent = EventManager.EventLogger.EventLog(eventSource, eventDesc, Data = "this is instance data", Level = eventLevel, Code = eventCode, Public = random.choice([True, False]), VerboseDescription = "this is for the verbose text")
        for i in range(100):
            self._EventList.append(thisEvent)
        #print "Count = ", len(self._EventList)
        #self.lstEventLog.UpdateEvents()

        #self.lstEventLog.SetStringItem(idx, 1, timeStr)
        #self.lstEventLog.SetStringItem(idx, 2, random.choice(['Test_1','Test_2','Test_3']))
        #self.lstEventLog.SetStringItem(idx, 3, str(random.choice([0,100, 200])))
        #self.lstEventLog.SetStringItem(idx, 4, random.choice(["This is a test!", "Unga bunga!", "I hope this worked!"]))
        #self.lstEventLog.ClearAll()

    def PrepareMenuBar(self):
        self.frame_1_menubar = wx.MenuBar()
        self.SetMenuBar(self.frame_1_menubar)

        self.mnuFile = wx.Menu()
        self.mnuFile_Exit = wx.MenuItem(self.mnuFile, wx.NewId(), "Exit", "", wx.ITEM_NORMAL)
        self.mnuFile.AppendItem(self.mnuFile_Exit)

        self.mnuHelp = wx.Menu()
        self.mnuHelp_About = wx.MenuItem(self.mnuHelp, wx.NewId(), "About", "", wx.ITEM_NORMAL)
        self.mnuHelp.AppendItem(self.mnuHelp_About)

        self.frame_1_menubar.Append(self.mnuFile, "File")
        self.frame_1_menubar.Append(self.mnuHelp, "Help")

    def PrepareStatusBar(self):
        self.StatusBar = self.CreateStatusBar(2, 0) #field count, style(?)
        self.StatusBar.SetStatusWidths([-1, -2])
        self.StatusBar.SetStatusText("This is field 0",0)
        self.StatusBar.SetStatusText("This is field 1 (twice as big as field 0)",1)

    def MakeWidgets(self):
        "Make all the widgets in the frame (but don't position them)."
        #Buttons...
        btnHeight = 30
        self.btnPFiltSelectAll     = wx.Button(self, -1, "All",  size = [-1, btnHeight])
        self.btnPFiltSelectNone    = wx.Button(self, -1, "None", size = [-1, btnHeight])
        self.btnSFiltSelectAll     = wx.Button(self, -1, "All",  size = [-1, btnHeight])
        self.btnSFiltSelectNone    = wx.Button(self, -1, "None", size = [-1, btnHeight])

        #Image lists
        #self.ilEventIcons = wx.ImageList(16, 16)

        #List Controls...
        self.lstEventLog  = EventViewListCtrl(self, -1,
                              DataSource = self._EventList,
                              EventSourceList = self._EventSourceList,
                              size = [800,400]
                              )

        ##Event Info...
        #Fixed Labels (StaticText)
        self.lblEventID            = wx.StaticText(self, -1, "ID:")
        self.lblEventTime          = wx.StaticText(self, -1, "Time:")
        self.lblEventLevel         = wx.StaticText(self, -1, "Level:")
        self.lblEventCode          = wx.StaticText(self, -1, "Code:")
        self.lblEventSource        = wx.StaticText(self, -1, "Source:")
        #self.lblEventText          = wx.StaticText(self, -1, "Event:")
        self.lblEventPublic        = wx.StaticText(self, -1, "Public:")
        #Changing text labels
        self.tlblEventID           = wx.StaticText(self, -1, "---")
        self.tlblEventTime         = wx.StaticText(self, -1, "---")
        self.tlblEventLevel        = wx.StaticText(self, -1, "---")
        self.tlblEventCode         = wx.StaticText(self, -1, "---")
        self.tlblEventSource       = wx.StaticText(self, -1, "---")
        self.tlblEventText         = wx.StaticText(self, -1, "<no item selected>", size = [-1, -1])
        self.tlblEventText.SetForegroundColour('YELLOW')
        self.tlblEventText.SetHelpText("This is a combination of the event description and the event data")
        #Checkboxes...
        self.chkEventPublic = wx.CheckBox(self, -1, "")
        self.chkTrackLatestEvent = wx.CheckBox(self, -1, "Always show latest event")
        self.chkTrackLatestEvent.SetValue(self.lstEventLog.EnsureLatestEventOnscreen)
        self.chkShowEventDate = wx.CheckBox(self, -1, "Show Event Date")
        self.chkShowEventDate.SetValue(self.lstEventLog.ShowEventDate)
        self.chkColourCodeSources = wx.CheckBox(self, -1, "Colour code sources")
        self.chkColourCodeSources.SetValue(self.lstEventLog.ColourCodeSources)

        #Text box...
        self.txtEventVerbose = wx.TextCtrl(self, -1, "<no item selected>",
                                          pos = wx.DefaultPosition,
                                          size = [80,40],
                                          style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP  )
        #self.txtEventVerbose.SetBackgroundColour('#191970')
        #self.txtEventVerbose.SetForegroundColour('WHITE')

        #CheckListBoxes...
        self.chlstPFilt = wx.CheckListBox(self, -1, (0, 0), wx.DefaultSize, ['P1','P2'])
        self.chlstSFilt = wx.CheckListBox(self, -1, (0, 0), wx.DefaultSize, ['S1','S2'])

        #idx = 0
        #for i in xrange(1000):
            #idx =frame_1.lstEventLog.InsertImageStringItem(sys.maxint, str(i+1), random.choice([0,1,2]))
            #timeStr = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            #frame_1.lstEventLog.SetStringItem(idx, 1, timeStr)
            #frame_1.lstEventLog.SetStringItem(idx, 3, str(random.choice([0,100, 200])))
            #frame_1.lstEventLog.SetStringItem(idx, 2, random.choice(['Test_1','Test_2','Test_3']))
            #frame_1.lstEventLog.SetStringItem(idx, 4, random.choice(["This is a test!", "Unga bunga!", "I hope this worked!"]))
            #time.sleep(0.5)
            ##self.lstEventLog.ClearAll()

    def DoLayout(self):
        """Creates all sizers, adds to them, and lays them out.

        In general it builds frm the inside out.
        """

        ##Priority filter frame
        #button sizer
        bsPFBut = wx.BoxSizer(wx.HORIZONTAL)
        bsPFBut.Add(self.btnPFiltSelectAll , 1, wx.GROW, 0)
        bsPFBut.Add(self.btnPFiltSelectNone, 1, wx.GROW, 0)
        #staticbox sizer with list combo and buttons
        sbPF  = wx.StaticBox(self, -1, "Priority Filter:" )
        bsPF = wx.StaticBoxSizer(sbPF, wx.VERTICAL)
        bsPF.Add(self.chlstPFilt, 1, wx.GROW, 0)
        bsPF.Add(bsPFBut, 0, wx.GROW, 0)

        ##Source filter frame
        #button sizer
        bsSFBut = wx.BoxSizer(wx.HORIZONTAL)
        bsSFBut.Add(self.btnSFiltSelectAll , 1, wx.GROW, 0)
        bsSFBut.Add(self.btnSFiltSelectNone, 1, wx.GROW, 0)
        #staticbox sizer with list combo and buttons
        sbSF  = wx.StaticBox(self, -1, "Source Filter:" )
        bsSF = wx.StaticBoxSizer(sbSF, wx.VERTICAL)
        bsSF.Add(self.chlstSFilt, 1, wx.GROW, 0)
        bsSF.Add(bsSFBut, 0, wx.GROW, 0)

        ##Options frame
        #staticbox sizer with list combo and buttons
        sbOptions  = wx.StaticBox(self, -1, "Options:" )
        bsOptions = wx.StaticBoxSizer(sbOptions, wx.VERTICAL)
        bsOptions.Add(self.chkTrackLatestEvent, 0, wx.GROW, 0)
        bsOptions.Add(self.chkShowEventDate, 0, wx.GROW, 0)
        bsOptions.Add(self.chkColourCodeSources, 0, wx.GROW, 0)

        ##Container for both filters and options
        bsFilters = wx.BoxSizer(wx.HORIZONTAL)
        bsFilters.Add(bsPF, 1, wx.GROW, 0)
        bsFilters.Add(bsSF, 1, wx.GROW, 0)
        bsFilters.Add(bsOptions, 1, wx.GROW, 0)

        ##Event log area
        sbEventLog = wx.StaticBox(self, -1, "Event Log:")
        bsEventLog = wx.StaticBoxSizer(sbEventLog, wx.VERTICAL)
        bsEventLog.Add(self.lstEventLog, 1, wx.GROW | wx.ALL, 2)

        ##Event detail area
        #static labels...
        bsEDLabels = wx.BoxSizer(wx.VERTICAL)
        labelBorder = 1
        bsEDLabels.Add(self.lblEventID    , 0, wx.ALIGN_LEFT, labelBorder)
        bsEDLabels.Add(self.lblEventTime  , 0, wx.ALIGN_LEFT, labelBorder)
        bsEDLabels.Add(self.lblEventLevel , 0, wx.ALIGN_LEFT, labelBorder)
        bsEDLabels.Add(self.lblEventCode  , 0, wx.ALIGN_LEFT, labelBorder)
        bsEDLabels.Add(self.lblEventSource, 0, wx.ALIGN_LEFT, labelBorder)
        bsEDLabels.Add(self.lblEventPublic, 0, wx.ALIGN_LEFT, labelBorder)
        #short information text...
        bsEDInfo = wx.BoxSizer(wx.VERTICAL)
        bsEDInfo.Add(self.tlblEventID    , 0, wx.ALIGN_LEFT | wx.GROW, labelBorder)
        bsEDInfo.Add(self.tlblEventTime  , 0, wx.ALIGN_LEFT | wx.GROW, labelBorder)
        bsEDInfo.Add(self.tlblEventLevel , 0, wx.ALIGN_LEFT | wx.GROW, labelBorder)
        bsEDInfo.Add(self.tlblEventCode  , 0, wx.ALIGN_LEFT | wx.GROW, labelBorder)
        bsEDInfo.Add(self.tlblEventSource, 0, wx.ALIGN_LEFT | wx.GROW, labelBorder)
        bsEDInfo.Add(self.chkEventPublic , 0, wx.ALIGN_LEFT | wx.GROW, labelBorder)
        #Long (and longer!) information text...
        bsEDInfoLong = wx.BoxSizer(wx.VERTICAL)
        bsEDInfoLong.Add(self.tlblEventText  , 0, wx.ALIGN_LEFT, labelBorder)
        bsEDInfoLong.Add(self.txtEventVerbose, 1, wx.GROW, 0)

        #All the info together...
        sbEventDetails = wx.StaticBox(self, -1, "Event details")
        bsEventDetails = wx.StaticBoxSizer(sbEventDetails, wx.HORIZONTAL)
        bsEventDetails.Add(bsEDLabels  , 0, wx.ALIGN_LEFT | wx.RIGHT, 5)
        bsEventDetails.Add(bsEDInfo    , 1, wx.ALIGN_LEFT, 0)
        bsEventDetails.Add(bsEDInfoLong, 4, wx.ALIGN_LEFT | wx.GROW, 0)

        ##The master sizer
        RootSizer = wx.BoxSizer(wx.VERTICAL)
        RootSizer.Add(bsFilters, 0, wx.GROW, 0)
        RootSizer.Add(bsEventLog, 1, wx.GROW, 0)
        RootSizer.Add(bsEventDetails, 0, wx.GROW, 0)

        ##set it all up
        self.SetAutoLayout(True)
        self.SetSizer(RootSizer)
        RootSizer.Fit(self)
        RootSizer.SetSizeHints(self)
        self.Layout()
class EventViewerApp(wx.PySimpleApp):
    def OnExit(self):
        print "App exited!"
class LogViewer(object):
    def __init__(self, EventDataSource, EventSourceCounter, EventSourceList, debug = False):
        self._EventDataSource = EventDataSource
        self._EventSourceCounter = EventSourceCounter
        self._EventSourceList = EventSourceList
        self.commandQueue = Queue.Queue(0)
        self.app = EventViewerApp(0)
        wx.InitAllImageHandlers()
        self.frame_1 = MyFrame(None, -1, "", size=(900,700))
        self.frame_1.debug_mode = debug
        self.frame_1.Initialize(DataSource = EventDataSource, \
            SourceEventCounter = EventSourceCounter, EventSourceList = EventSourceList, \
            CommandQueue = self.commandQueue)
        self.app.SetTopWindow(self.frame_1)
        self.ViewerNotRunning = threading.Event()
        self.ViewerNotRunning.set()

    def Launch(self):
        """Launches the Event viewer GUI.

        When the GUI finishes running the ViewerNotRunning event is set.
        """
        self.frame_1.Show()
        self.ViewerNotRunning.clear()
        self.app.MainLoop()
        #print "MainLoop completed"
        self.ViewerNotRunning.set()
        #print "ViewerNotRunning set"
    # Functions are curried and enqueued for execution within GUI thread

    def ShutDown(self):
        def _ShutDown():
            self.frame_1.Close()
        self.commandQueue.put(_ShutDown)


    def UpdateEventData(self):
        def _UpdateEventData():
            # Events will appear on screen when CommandTimer fires next
            #update the event count in the status bar...
            self.frame_1.StatusBar.SetStatusText("%6s events" % len(self._EventDataSource), 0)
        self.commandQueue.put(_UpdateEventData)


    def ChangeDataSource(self, EventDataSource):
        def _ChangeDataSource():
            self._EventDataSource = EventDataSource
            self.frame_1.lstEventLog._DataSource = EventDataSource
        self.commandQueue.put(_ChangeDataSource)


if __name__ == "__main__":
    eventList =[]
    va = LogViewer(eventList, debug = True)
    va.Launch()