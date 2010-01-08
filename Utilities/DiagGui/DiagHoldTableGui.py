# File Name: DiagHoldTableGui.py
# Purpose: This module handles the HoldTable page
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
class HoldTableGui(wx.Panel):
    """ Creates General Panel Controls """
    def __init__(self,*args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)

        # create other classes
        self.diag = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % DriverRpcServerPort, ClientName = "Diagnostics")
        self.tableNum    = 0
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
        for table in range(len(Global.DIAG_HoldTableTypeDict)-1):
            list.append( Global.DIAG_HoldTableTypeDict[table] )
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
        numEntries = self.diag.DIAG_ReadTableTotal( Global.DIAG_HoldTables, self.tableNum )
        self.table = self.diag.DIAG_ReadHoldTable( self.tableNum, numEntries )
        self.listControl.OnUpdateTable( self.table )
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
        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "Time")
        self.InsertColumn(2, "Value(float)")
        self.InsertColumn(3, "Value(UINT32)")
        self.SetColumnWidth(0, 230)
        self.SetColumnWidth(1, 120)
        self.SetColumnWidth(2, 180)
        self.SetColumnWidth(3, 180)

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
        key = Global.DIAG_MinMaxHoldTypeDict[item]
        if col==0:
            return key
        elif item < len(self.table):
            return self.table[key][col-1]
        else:
            return ""

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 0:
            return self.attrBlue
        else:
            return None

    def OnUpdateTable(self, table):
        self.table = table
        self.SetItemCount(len(table)-1)
        self.Refresh()
