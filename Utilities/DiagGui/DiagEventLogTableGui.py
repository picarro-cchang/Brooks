# File Name: DiagEventLogTableGui.py
# Purpose: This module handles the EventLogTable page
#
# File History:
# 06-04-06 ytsai   Created file

import sys,os
import wx
sys.path.append("../..")

import Common.CmdFIFO as CmdFIFO
import Common.ss_autogen as Global
from   Common.SharedTypes import DriverRpcServerPort

####################################################################
#
class EventLogTableGui(wx.Panel):
    """ Creates General Panel Controls """
    def __init__(self,*args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)

        # create other classes
        self.diag = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % DriverRpcServerPort, ClientName = "Diagnostics")

        #Initialize table
        self.tableNum    = Global.DIAG_ReadyMajorLogTable
        self.table=[]

        # create controls
        self.CreateControls()

        # setup panel
        self.SetupPanel()

        # Bind events
        self.BindEvents()

    def CreateControls(self):
        self.listControl = GeneralList(self)
        self.readButton  = wx.Button(self,-1,"update")
        self.numEntriesText = wx.TextCtrl(self, -1, "", size=(68, -1), style=wx.TE_READONLY)

        # create list for combobox, and attach to combobox
        list = []
        for table in range(len(Global.DIAG_LogTableTypeDict)-1):
            list.append( Global.DIAG_LogTableTypeDict[table] )
        self.tableComboBox = wx.ComboBox( self, 500, list[self.tableNum], (90, 50), (200, -1),
          list, wx.CB_DROPDOWN )

    def SetupPanel(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add( self.listControl,1,wx.EXPAND,0)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.readButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer2.Add(self.tableComboBox, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer2.Add(self.numEntriesText, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer1.Add(sizer2, 0, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer1)
        sizer1.Fit(self)
        sizer1.SetSizeHints(self)

    def BindEvents(self):
        self.Bind(wx.EVT_BUTTON, self.onUpdateButtonClick, self.readButton)
        self.Bind(wx.EVT_COMBOBOX, self.onEventComboBox, self.tableComboBox)

    def onUpdateButtonClick(self,parent):
        numEntries = self.diag.DIAG_ReadTableTotal( Global.DIAG_EventLogTables, self.tableNum )
        self.table = self.diag.DIAG_ReadEventLogTable( self.tableNum, numEntries )
        self.listControl.OnUpdateTable( self.table, numEntries )
        self.numEntriesText.Clear()
        self.numEntriesText.WriteText( "%d" % numEntries )

    def onEventComboBox(self, event):
        self.tableComboBox = event.GetEventObject()
        self.tableNum = self.tableComboBox.GetSelection()

    def onRefresh(self,parent):
        if len(self.table) <= 0:
            self.onUpdateButtonClick(parent)

####################################################################
#
class GeneralList( wx.ListCtrl ):
    def __init__(self, parent ):
        wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)
        self.SetupList()
        self.SetupEvents()
        self.table = []

    def SetupList(self):
        self.InsertColumn( 0, "" )
        col = 1
        for field in Global.DIAG_EventLogStruct._fields_[:-1]:
            self.InsertColumn( col, field[0] )
            self.SetColumnWidth(col, 100)
            col += 1

        customDataEntries = 0
        while customDataEntries < 16:
            self.InsertColumn( col,"customData%d" % customDataEntries )
            self.SetColumnWidth(col, 100)
            customDataEntries+=1
            col += 1

        self.SetColumnWidth(0, 30)
        self.SetColumnWidth(1, 110)
        self.SetColumnWidth(2, 200)

        self.attrYellow = wx.ListItemAttr()
        self.attrYellow.SetBackgroundColour("yellow")
        self.attrBlue = wx.ListItemAttr()
        self.attrBlue.SetBackgroundColour("light blue")
        self.attrRed = wx.ListItemAttr()
        self.attrRed.SetBackgroundColour("light red")

    def SetupEvents(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        if len(self.table) <= 0:
            return ""
        if col == 0:
            return "%d" % (item+1)
        else:
            key = self.table[ "_fields_" ][col-1]
            return self.table[key][item]

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 0:
            return self.attrBlue
        else:
            return None

    def OnUpdateTable(self, table, numEntries ):
        self.table = table
        self.SetItemCount( numEntries )
        self.Refresh()
