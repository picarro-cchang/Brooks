#!/usr/bin/env python

import wx
import time
from wx.lib.masked import TimeCtrl
from datetime import datetime

class SupervisorLauncherFrame(wx.Frame):
    def __init__(self, typeChoices, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Picarro Mode Switcher")
        self.SetBackgroundColour("#E0FFFF")

        # labels
        self.labelTitle = wx.StaticText(self, -1, "Picarro Mode Switcher", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        copyrightText = "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0]
        self.labelFooter = wx.StaticText(self, -1, copyrightText, style=wx.ALIGN_CENTER)
        self.labelSelect = wx.StaticText(self, -1, "Select Measurement Mode", style=wx.ALIGN_CENTER)

        # Divider line
        self.staticLine = wx.StaticLine(self, -1)

        # controls
        self.comboBoxSelect = wx.ComboBox(self, -1, value = typeChoices[0], choices = typeChoices, style = wx.CB_READONLY|wx.CB_DROPDOWN)

        # button
        self.buttonLaunch = wx.Button(self, -1, "Launch", size=(110, 20))
        self.buttonLaunch.SetBackgroundColour(wx.Colour(237, 228, 199))

        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 2)

        sizer_1.Add(self.labelTitle, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.staticLine, 0, wx.EXPAND, 0)
        sizer_1.Add((-1, 10))
        grid_sizer_1.Add(self.labelSelect, 0, wx.LEFT|wx.RIGHT, 20)
        grid_sizer_1.Add(self.comboBoxSelect, 0, wx.LEFT|wx.RIGHT, 10)
        grid_sizer_1.Add((-1,30))
        grid_sizer_1.Add(self.buttonLaunch, 0, wx.LEFT|wx.TOP|wx.ALIGN_BOTTOM|wx.RIGHT, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1, 10))
        sizer_1.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

class UserNotificationsFrameGui(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: UserNotificationsFrameGui.__init__
        kwds["style"] = wx.CAPTION | wx.STAY_ON_TOP
        wx.Frame.__init__(self, *args, **kwds)
        #self.panel_main = wx.Panel(self, wx.ID_ANY)
        self.button_dismiss = wx.Button(self, wx.ID_ANY, "Recalibration Event")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_button_dismiss, self.button_dismiss)
        self.closed = False
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: UserNotificationsFrameGui.__set_properties
        self.SetTitle("User Notifications")
        self.SetSize((400, 100))
        self.button_dismiss.SetBackgroundColour(wx.Colour(204, 50, 50))
        self.button_dismiss.SetForegroundColour(wx.Colour(255, 255, 255))
        self.button_dismiss.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.button_dismiss.SetToolTipString("Click to dismiss notification")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: UserNotificationsFrameGui.__do_layout
        sizer_main = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(self.button_dismiss, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_main)
        self.Layout()
        # end wxGlade

    def on_button_dismiss(self, event):  # wxGlade: UserNotificationsFrameGui.<event_handler>
        self.Hide()
        self.closed = True

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = UserNotificationsFrameGui(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()