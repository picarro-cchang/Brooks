#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Sat Aug 29 16:55:29 2009

import wx

# begin wxGlade: extracode
from wx.py import crust
from ControllerPanels import StatsPanel
from ControllerPanels import RingdownPanel
from ControllerPanels import WlmPanel
from ControllerPanels import PressurePanel
from ControllerPanels import HotBoxPanel
from ControllerPanels import WarmBoxPanel
from ControllerPanels import LaserPanel

from ControllerPanels import CommandLogPanel
# end wxGlade



class ControllerFrameGui(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ControllerFrameGui.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.topNotebook = wx.Notebook(self, -1, style=0)
        self.shellPane = wx.Panel(self.topNotebook, -1)
        self.statsPane = wx.Panel(self.topNotebook, -1)
        self.ringdownPane = wx.Panel(self.topNotebook, -1)
        self.wlmPane = wx.Panel(self.topNotebook, -1)
        self.pressurePane = wx.Panel(self.topNotebook, -1)
        self.hotBoxPane = wx.Panel(self.topNotebook, -1)
        self.warmBoxPane = wx.Panel(self.topNotebook, -1)
        self.laser4Pane = wx.Panel(self.topNotebook, -1)
        self.laser3Pane = wx.Panel(self.topNotebook, -1)
        self.laser2Pane = wx.Panel(self.topNotebook, -1)
        self.laser1Pane = wx.Panel(self.topNotebook, -1)
        self.commandLogPane = wx.Panel(self.topNotebook, -1)
        
        # Menu Bar
        self.controllerFrameGui_menubar = wx.MenuBar()
        self.interface = wx.Menu()
        self.interfaceUser = wx.MenuItem(self.interface, wx.NewId(), "User", "", wx.ITEM_NORMAL)
        self.interface.AppendItem(self.interfaceUser)
        self.interfaceFull = wx.MenuItem(self.interface, wx.NewId(), "Full", "", wx.ITEM_NORMAL)
        self.interface.AppendItem(self.interfaceFull)
        self.interface.AppendSeparator()
        self.interfaceClose = wx.MenuItem(self.interface, wx.NewId(), "Close", "", wx.ITEM_NORMAL)
        self.interface.AppendItem(self.interfaceClose)
        self.controllerFrameGui_menubar.Append(self.interface, "Interface")
        self.file = wx.Menu()
        self.fileLoadConfig = wx.MenuItem(self.file, wx.NewId(), "Load config file", "", wx.ITEM_NORMAL)
        self.file.AppendItem(self.fileLoadConfig)
        self.fileWriteConfig = wx.MenuItem(self.file, wx.NewId(), "Write config file", "", wx.ITEM_NORMAL)
        self.file.AppendItem(self.fileWriteConfig)
        self.controllerFrameGui_menubar.Append(self.file, "File")
        self.parameters = wx.Menu()
        self.controllerFrameGui_menubar.Append(self.parameters, "Parameters")
        self.help = wx.Menu()
        self.helpAbout = wx.MenuItem(self.help, wx.NewId(), "About", "", wx.ITEM_NORMAL)
        self.help.AppendItem(self.helpAbout)
        self.controllerFrameGui_menubar.Append(self.help, "Help")
        self.SetMenuBar(self.controllerFrameGui_menubar)
        # Menu Bar end
        self.controllerFrameGui_statusbar = self.CreateStatusBar(1, 0)
        self.commandLogPanel = CommandLogPanel(self.commandLogPane, -1)
        self.laser1Panel = LaserPanel(self.laser1Pane, -1)
        self.laser2Panel = LaserPanel(self.laser2Pane, -1)
        self.laser3Panel = LaserPanel(self.laser3Pane, -1)
        self.laser4Panel = LaserPanel(self.laser4Pane, -1)
        self.warmBoxPanel = WarmBoxPanel(self.warmBoxPane, -1)
        self.hotBoxPanel = HotBoxPanel(self.hotBoxPane, -1)
        self.pressurePanel = PressurePanel(self.pressurePane, -1)
        self.wlmPanel = WlmPanel(self.wlmPane, -1)
        self.ringdownPanel = RingdownPanel(self.ringdownPane, -1)
        self.statsPanel = StatsPanel(self.statsPane, -1)
        self.crustPanel = crust.Crust(self.shellPane, -1)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.onUserInterface, self.interfaceUser)
        self.Bind(wx.EVT_MENU, self.onFullInterface, self.interfaceFull)
        self.Bind(wx.EVT_MENU, self.onClose, self.interfaceClose)
        self.Bind(wx.EVT_MENU, self.onLoadIni, self.fileLoadConfig)
        self.Bind(wx.EVT_MENU, self.onWriteIni, self.fileWriteConfig)
        self.Bind(wx.EVT_MENU, self.onAbout, self.helpAbout)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ControllerFrameGui.__set_properties
        self.SetTitle("Cavity Ring-Down Spectrometer Controller")
        self.SetSize((1000, 700))
        self.controllerFrameGui_statusbar.SetStatusWidths([-1])
        # statusbar fields
        controllerFrameGui_statusbar_fields = ["controllerFrameGui_statusbar"]
        for i in range(len(controllerFrameGui_statusbar_fields)):
            self.controllerFrameGui_statusbar.SetStatusText(controllerFrameGui_statusbar_fields[i], i)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ControllerFrameGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_13 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_11 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_8 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(self.commandLogPanel, 1, wx.EXPAND, 0)
        self.commandLogPane.SetSizer(sizer_2)
        sizer_3.Add(self.laser1Panel, 1, wx.EXPAND, 0)
        self.laser1Pane.SetSizer(sizer_3)
        sizer_4.Add(self.laser2Panel, 1, wx.EXPAND, 0)
        self.laser2Pane.SetSizer(sizer_4)
        sizer_5.Add(self.laser3Panel, 1, wx.EXPAND, 0)
        self.laser3Pane.SetSizer(sizer_5)
        sizer_6.Add(self.laser4Panel, 1, wx.EXPAND, 0)
        self.laser4Pane.SetSizer(sizer_6)
        sizer_7.Add(self.warmBoxPanel, 1, wx.EXPAND, 0)
        self.warmBoxPane.SetSizer(sizer_7)
        sizer_8.Add(self.hotBoxPanel, 1, wx.EXPAND, 0)
        self.hotBoxPane.SetSizer(sizer_8)
        sizer_9.Add(self.pressurePanel, 1, wx.EXPAND, 0)
        self.pressurePane.SetSizer(sizer_9)
        sizer_10.Add(self.wlmPanel, 1, wx.EXPAND, 0)
        self.wlmPane.SetSizer(sizer_10)
        sizer_11.Add(self.ringdownPanel, 1, wx.EXPAND, 0)
        self.ringdownPane.SetSizer(sizer_11)
        sizer_12.Add(self.statsPanel, 1, wx.EXPAND, 0)
        self.statsPane.SetSizer(sizer_12)
        sizer_13.Add(self.crustPanel, 1, wx.EXPAND, 0)
        self.shellPane.SetSizer(sizer_13)
        self.topNotebook.AddPage(self.commandLogPane, "Command/Log")
        self.topNotebook.AddPage(self.laser1Pane, "Laser1")
        self.topNotebook.AddPage(self.laser2Pane, "Laser2")
        self.topNotebook.AddPage(self.laser3Pane, "Laser3")
        self.topNotebook.AddPage(self.laser4Pane, "Laser4")
        self.topNotebook.AddPage(self.warmBoxPane, "WarmBox")
        self.topNotebook.AddPage(self.hotBoxPane, "HotBox")
        self.topNotebook.AddPage(self.pressurePane, "Pressure")
        self.topNotebook.AddPage(self.wlmPane, "WavelengthMonitor")
        self.topNotebook.AddPage(self.ringdownPane, "Ringdowns")
        self.topNotebook.AddPage(self.statsPane, "Statistics")
        self.topNotebook.AddPage(self.shellPane, "Shell")
        sizer_1.Add(self.topNotebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def onUserInterface(self, event): # wxGlade: ControllerFrameGui.<event_handler>
        print "Event handler `onUserInterface' not implemented!"
        event.Skip()

    def onFullInterface(self, event): # wxGlade: ControllerFrameGui.<event_handler>
        print "Event handler `onFullInterface' not implemented!"
        event.Skip()

    def onClose(self, event): # wxGlade: ControllerFrameGui.<event_handler>
        print "Event handler `onClose' not implemented!"
        event.Skip()

    def onLoadIni(self, event): # wxGlade: ControllerFrameGui.<event_handler>
        print "Event handler `onLoadIni' not implemented!"
        event.Skip()

    def onWriteIni(self, event): # wxGlade: ControllerFrameGui.<event_handler>
        print "Event handler `onWriteIni' not implemented!"
        event.Skip()

    def onAbout(self, event): # wxGlade: ControllerFrameGui.<event_handler>
        print "Event handler `onAbout' not implemented!"
        event.Skip()

# end of class ControllerFrameGui


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    controllerFrameGui = ControllerFrameGui(None, -1, "")
    app.SetTopWindow(controllerFrameGui)
    controllerFrameGui.Show()
    app.MainLoop()
