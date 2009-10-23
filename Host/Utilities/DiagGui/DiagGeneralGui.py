# File Name: DiagGeneralGui.py
# Purpose: This module handles the General page of the Diag GUI
#
# File History:
# 06-04-06 ytsai   Created file

# system imports
import sys,os
import wx
import time

# das related imports
sys.path.append("../..")
import Common.ss_autogen as Global
import Common.CmdFIFO as CmdFIFO
from   Common.SharedTypes import DriverRpcServerPort

####################################################################
#
class GeneralGui(wx.Panel):
    """ Creates General Panel Controls """
    def __init__(self,*args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        self.listControl = GeneralList(self)
        self.updateButton  = wx.Button(self,-1,"update")
        self.clearButton = wx.Button(self,-1,"clear")
        self.clearAllButton = wx.Button(self,-1,"clear all")
        self.saveButton = wx.Button(self,-1,"save")
        self.diag = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % DriverRpcServerPort, ClientName = "Diagnostics")

        self.SetupPanel()

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.onUpdateButtonClick, self.updateButton)
        self.Bind(wx.EVT_BUTTON, self.onSaveButtonClick, self.saveButton)
        self.Bind(wx.EVT_BUTTON, self.onClearButtonClick, self.clearButton)
        self.Bind(wx.EVT_BUTTON, self.onClearAllButtonClick, self.clearAllButton)

        # Do first update for screen
        self.onUpdateButtonClick(self)

    def SetupPanel(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add( self.listControl,1,wx.EXPAND,0)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.updateButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer2.Add(self.saveButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer2.Add(self.clearButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer2.Add(self.clearAllButton, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        sizer1.Add(sizer2, 0, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer1)
        sizer1.Fit(self)
        sizer1.SetSizeHints(self)

    def onUpdateButtonClick(self,parent):
        self.tablesTotalDict = self.diag.DIAG_ReadTableTotals()
        self.listControl.OnUpdateTable( self.tablesTotalDict )

    def _translateTableFamilyNumStringToTableFamilyInt( self, tableFamilyNumString ):
        for f in range(len(Global.DIAG_TableFamilyTypeDict)):
            if Global.DIAG_TableFamilyTypeDict[f] == tableFamilyNumString:
                return f

    def _translateTableNumStringToTableNumInt( self, tableNumString, tableNumDict ):
        for t in range(len(tableNumDict)):
            if tableNumDict[t] == tableNumString:
                return t

    def onClearButtonClick(self,parent):
        if len( self.tablesTotalDict ) <= 0:
            return

        item = self.listControl.currentItem
        tableFamilyName = self.listControl.GetItemText( item )
        tableName       = self.listControl.GetColumnText( item, 1 )
        tableFamilyNum  = self._translateTableFamilyNumStringToTableFamilyInt( tableFamilyName )
        tableNameDict   = _tableNameDict(tableFamilyNum)
        tableNum =  self._translateTableNumStringToTableNumInt( tableName, tableNameDict )
        promptString = 'This will clear table ' + tableFamilyName + '/' + tableName + '  Are you sure?'
        dlg = wx.SingleChoiceDialog(self, promptString ,'Warning',['Yes','No'], wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.GetStringSelection() == 'Yes':
                self.diag.DIAG_ClearTable( tableFamilyNum, tableNum )
                self.onUpdateButtonClick(self)

    def onClearAllButtonClick(self,parent):
        dlg = wx.SingleChoiceDialog(self, 'This will clear all tables. Are you sure?','Warning',['Yes','No'], wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.GetStringSelection() == 'Yes':
                self.diag.DIAG_ClearTables()
                self.onUpdateButtonClick(self)

    def onSaveButtonClick(self,parent):
        wildcard    = "*.log"
        defaultFile = time.strftime("Diag%Y%m%d_%H%M%S.log",time.localtime())
        dlg = wx.FileDialog( self, message="Save file as",
          defaultDir=os.getcwd(), defaultFile=defaultFile, wildcard=wildcard, style=wx.SAVE)
        dlg.SetFilterIndex(1)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            print "Saving to %s" % path
            print "Please wait..."
            self.diag.DIAG_SaveTables( path )
            print "Done saving file!"

    def onRefresh(self,parent):
        pass

####################################################################
#
class GeneralList( wx.ListCtrl ):
    def __init__(self, parent ):
        wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)
        self.SetupList()
        self.SetupEvents()
        self.tablesList = []

    def SetupList(self):
        self.InsertColumn(0, "Type")
        self.InsertColumn(1, "Name")
        self.InsertColumn(2, "Entries")
        self.SetColumnWidth(0, 128)
        self.SetColumnWidth(1, 180)
        self.SetColumnWidth(2, 600)

        self.attrYellow = wx.ListItemAttr()
        self.attrYellow.SetBackgroundColour("yellow")
        self.attrBlue = wx.ListItemAttr()
        self.attrBlue.SetBackgroundColour("light blue")
        self.attrRed = wx.ListItemAttr()
        self.attrRed.SetBackgroundColour("light red")

    def SetupEvents(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        #self.log.WriteText('OnItemSelected: "%s", "%s", "%s", "%s"\n' %
        #                   (self.currentItem,
        #                    self.GetItemText(self.currentItem),
        #                    self.GetColumnText(self.currentItem, 1),
        #                    self.GetColumnText(self.currentItem, 2)))

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        #self.log.WriteText("OnItemActivated: %s\nTopItem: %s\n" %
        #                     (self.GetItemText(self.currentItem), self.GetTopItem()))

    def GetColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemDeselected(self, evt):
        """ """

    def OnGetItemText(self, item, col):
        if len(self.tablesList) <= 0:
            return ""

        if item < len(self.tablesList):
            return self.tablesList[item][col]
        else:
            return ""

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        if len(self.tablesList) <= 0:
            return None
        if self.tablesList[item][0] == "DIAG_HoldTables":
            return None
        elif self.tablesList[item][0] == "DIAG_EventCountTables":
            return self.attrBlue
        elif self.tablesList[item][0] == "DIAG_EventLogTables":
            return None
        elif self.tablesList[item][0] == "DIAG_UsageLogTables":
            return self.attrBlue
        elif self.tablesList[item][0] == "DIAG_ParamLogTables":
            return None
        else:
            return None

    def OnUpdateTable(self, tablesTotalDict ):
        tablesList = []
        for tableFamilyNum in range(len(Global.DIAG_TableFamilyTypeDict)):
            tableFamilyName = Global.DIAG_TableFamilyTypeDict[tableFamilyNum]
            tableNameDict = _tableNameDict(tableFamilyNum)
            for tableNum in range(len(tableNameDict)-1):
                list = []
                tableName = tableNameDict[ tableNum ]
                list.append( tableFamilyName )
                list.append( tableName )
                numEntries = tablesTotalDict[tableFamilyName][tableName]
                list.append( numEntries )
                tablesList.append( list )
        self.tablesList = tablesList
        self.SetItemCount(len(tablesList))
        self.Refresh()

    def OnDoubleClick(self, event):
        #print "OnDoubleClick item %s/%s\n" % (self.GetItemText(self.currentItem),\
        #  self.GetColumnText(self.currentItem, 1))
        event.Skip()

def _tableNameDict( tableFamilyNum ):
    """ Returns dictionary of table in specified family """
    if   tableFamilyNum == Global.DIAG_HoldTables:
        return Global.DIAG_HoldTableTypeDict
    elif tableFamilyNum == Global.DIAG_EventCountTables:
        return Global.DIAG_EventCountTableTypeDict
    elif tableFamilyNum == Global.DIAG_EventLogTables:
        return Global.DIAG_LogTableTypeDict
    elif tableFamilyNum == Global.DIAG_UsageLogTables:
        return Global.DIAG_UsageTableTypeDict
    elif tableFamilyNum == Global.DIAG_ParamLogTables:
        return Global.DIAG_ParameterTableTypeDict
