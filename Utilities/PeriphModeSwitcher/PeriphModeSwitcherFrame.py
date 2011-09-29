#!/usr/bin/env python

import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime

class PeriphModeSwitcherFrame(wx.Frame):
    def __init__(self, typeChoices, defaultType, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Peripheral Mode Switcher")
        self.SetBackgroundColour("#E0FFFF")
        
        # labels
        self.labelTitle = wx.StaticText(self, -1, "Peripheral Mode Switcher", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelFooter = wx.StaticText(self, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.labelSelect = wx.StaticText(self, -1, "Select Peripheral Mode", style=wx.ALIGN_CENTER)
        
        # Divider line
        self.staticLine = wx.StaticLine(self, -1)
        
        # controls
        try:
            self.comboBoxSelect = wx.ComboBox(self, -1, value = defaultType, choices = typeChoices, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        except:
            self.comboBoxSelect = wx.ComboBox(self, -1, value = typeChoices[0], choices = typeChoices, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        # button
        self.buttonApply = wx.Button(self, -1, "Apply", size=(110, 20))
        self.buttonApply.SetBackgroundColour(wx.Colour(237, 228, 199))
        
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
        grid_sizer_1.Add(self.buttonApply, 0, wx.LEFT|wx.TOP|wx.ALIGN_BOTTOM|wx.RIGHT, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1, 10))
        sizer_1.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = PeriphModeSwitcherFrame(["None", "Gill", "CSAT3"], "None", None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()