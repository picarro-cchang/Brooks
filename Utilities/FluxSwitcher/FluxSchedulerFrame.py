#!/usr/bin/env python

import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime

class FluxSchedulerFrame(wx.Frame):
    def __init__(self, typeChoices, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Picarro Flux Scheduler")
        self.SetBackgroundColour("#E0FFFF")
        
        # labels
        self.labelTitle = wx.StaticText(self, -1, "Picarro Flux Scheduler", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelFooter = wx.StaticText(self, -1, "Copyright Picarro, Inc. 1999-2010", style=wx.ALIGN_CENTER)
        self.labelMode = wx.StaticText(self, -1, "Flux Mode", style=wx.ALIGN_CENTER)
        self.labelDwell = wx.StaticText(self, -1, "Dwell Time (min)", style=wx.ALIGN_CENTER)
        
        # Divider line
        self.staticLine = wx.StaticLine(self, -1)
        
        # Type select
        self.comboBoxSelect = []
        for i in range(3):
            self.comboBoxSelect.append(wx.ComboBox(self, -1, value = typeChoices[i], choices = typeChoices, style = wx.CB_READONLY|wx.CB_DROPDOWN))
        
        # dwell
        self.dwell = []
        for i in range(3):
            self.dwell.append(wx.TextCtrl(self, -1, "0", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE))
            
        # Button
        self.buttonLaunch = wx.Button(self, -1, "Launch", size=(100, 20))
        self.buttonLaunch.SetBackgroundColour(wx.Colour(237, 228, 199))
        
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.FlexGridSizer(-1, 2)

        sizer_1.Add(self.labelTitle, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.staticLine, 0, wx.EXPAND, 0)
        sizer_1.Add((-1, 10))
        grid_sizer_1.Add(self.labelMode, 0, wx.ALL, 10)
        grid_sizer_1.Add(self.labelDwell, 0, wx.ALL, 10)
        for i in range(3):
            grid_sizer_1.Add(self.comboBoxSelect[i], 0, wx.ALL, 10)
            grid_sizer_1.Add(self.dwell[i], 0, wx.ALL, 10)
        grid_sizer_1.Add((-1,30))
        grid_sizer_1.Add(self.buttonLaunch, 0, wx.LEFT|wx.TOP|wx.ALIGN_BOTTOM|wx.RIGHT, 10)
        sizer_2.Add((15,-1))
        sizer_2.Add(grid_sizer_1, 0)
        sizer_2.Add((15,-1))
        sizer_1.Add(sizer_2, 0)
        sizer_1.Add((-1, 10))
        sizer_1.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = FluxSchedulerFrame(["CO2_H2O", "H2O_CH4", "CO2_CH4"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()