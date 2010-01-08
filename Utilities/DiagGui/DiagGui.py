# File Name: DiagGui.py
# Purpose: This module handles the main frame/app for the DiagGui
#
# File History:
# 06-04-06 ytsai   Created file

import sys,os
import wx

from DiagGeneralGui import GeneralGui
from DiagHoldTableGui import HoldTableGui
from DiagEventCountTableGui import EventCountTableGui
from DiagEventLogTableGui import EventLogTableGui
from DiagUsageLogTableGui import UsageLogTableGui
from DiagParameterLogTableGui import ParameterLogTableGui

class MainFrame(wx.Frame):
    def __init__(self, parent, ID, title, pos=wx.DefaultPosition,
            size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):

        # create window frame
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)

        # create notebook
        self.notebook = wx.Notebook(self, -1, style=0)

        # create panels for notebook
        self.createPanels()

        # add pages
        self.createPages()

        # bind to events
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def __do_layout(self):
        notebookSizer = wx.BoxSizer(wx.VERTICAL)
        self.createPages
        notebookSizer.Add(self.notebook, 1, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_1)
        self.Layout()

    def createPanels(self):
        self.panelAttributeList =[ \
          (GeneralGui, "General"), \
          (HoldTableGui, "HoldPanel"), \
          (EventCountTableGui, "EventCountPanel"), \
          (EventLogTableGui, "EventLogPanel"), \
          (UsageLogTableGui, "UsageLogPanel"), \
          (ParameterLogTableGui, "ParameterLogPanel"), \
          ]
        self.panelList= []
        for panelIndex in range(len(self.panelAttributeList)):
            (Gui,Name) = self.panelAttributeList[panelIndex]
            self.panelList.append( Gui(id=-1, name=Name, parent=self.notebook, pos=wx.Point(0, 0),\
              size=wx.Size(646, 309), style=wx.TAB_TRAVERSAL) )

    def createPages(self):
        for panelIndex in range(len(self.panelAttributeList)):
            (Gui,Name) = self.panelAttributeList[panelIndex]
            self.notebook.AddPage( page=self.panelList[panelIndex], select=False, text=Name )

    def OnCloseWindow(self, event):
        self.Destroy()

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        self.panelList[new].onRefresh(self.panelList[new])

class MainApp(wx.PySimpleApp):
    def Main(self):
        frame = MainFrame(None, -1, "CRDS Diagnostics", size=(860, 608), style = wx.DEFAULT_FRAME_STYLE)
        frame.Show(True)
        self.SetTopWindow(frame)
        self.MainLoop()

if __name__ == '__main__':
    App = MainApp()
    App.Main()
