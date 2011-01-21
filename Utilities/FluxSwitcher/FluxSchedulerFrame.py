#!/usr/bin/env python

import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime

class FluxSchedulerFrame(wx.Frame):
    def __init__(self, typeChoices, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.SetTitle("Flux Mode Scheduler")
        
        # labels
        self.labelTitle1 = wx.StaticText(self.panel1, -1, "Picarro Flux Mode Scheduler", style=wx.ALIGN_CENTRE)
        self.labelTitle1.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelTitle2 = wx.StaticText(self.panel2, -1, "Quick Flux Mode Switcher", style=wx.ALIGN_CENTRE)
        self.labelTitle2.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelFooter = wx.StaticText(self.panel2, -1, "Copyright Picarro, Inc. 1999-2010", style=wx.ALIGN_CENTER)
        self.labelMode = wx.StaticText(self.panel1, -1, "FLUX MODE", style=wx.ALIGN_CENTER)
        self.labelDwell = wx.StaticText(self.panel1, -1, "DWELL TIME (MIN)", style=wx.ALIGN_CENTER)
        
        # Divider line
        self.staticLine = wx.StaticLine(self.panel1, -1) 
        
        # Type select
        self.numTypes = len(typeChoices)
        self.comboBoxSelect1 = []
        for i in range(self.numTypes):
            self.comboBoxSelect1.append(wx.ComboBox(self.panel1, -1, value = typeChoices[i], choices = typeChoices, size=(150, 20), style = wx.CB_READONLY|wx.CB_DROPDOWN))
        self.comboBoxSelect2 = wx.ComboBox(self.panel2, -1, value = typeChoices[0], choices = typeChoices, size=(150, 20), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        # dwell
        self.dwell = []
        for i in range(self.numTypes):
            self.dwell.append(wx.TextCtrl(self.panel1, -1, "0", size=(150, 20), style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE))
            
        # Button
        self.buttonStop = wx.Button(self.panel1, -1, "Stop", size=(150, 20))
        self.buttonStop.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonLaunch1 = wx.Button(self.panel1, -1, "Launch", size=(150, 20))
        self.buttonLaunch1.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonLaunch2 = wx.Button(self.panel2, -1, "Launch", size=(150, 20))
        self.buttonLaunch2.SetBackgroundColour(wx.Colour(237, 228, 199))        
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(-1, 2)
        grid_sizer_2 = wx.FlexGridSizer(-1, 2)

        sizer_1.Add(self.labelTitle1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        grid_sizer_1.Add(self.labelMode, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        grid_sizer_1.Add(self.labelDwell, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        for i in range(self.numTypes):
            grid_sizer_1.Add(self.comboBoxSelect1[i], 0, wx.ALL, 10)
            grid_sizer_1.Add(self.dwell[i], 0, wx.ALL, 10)
        grid_sizer_1.Add(self.buttonStop, 0, wx.LEFT|wx.TOP|wx.ALIGN_BOTTOM|wx.RIGHT, 10)
        grid_sizer_1.Add(self.buttonLaunch1, 0, wx.LEFT|wx.TOP|wx.ALIGN_BOTTOM|wx.RIGHT, 10)
        sizer_2.Add((15,-1))
        sizer_2.Add(grid_sizer_1, 0)
        sizer_2.Add((15,-1))
        sizer_1.Add(sizer_2, 0)
        sizer_1.Add((-1, 20))
        sizer_1.Add(self.staticLine, 0, wx.EXPAND, 0)
        self.panel1.SetSizer(sizer_1)
        
        sizer_3.Add(self.labelTitle2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        grid_sizer_2.Add(self.comboBoxSelect2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        grid_sizer_2.Add(self.buttonLaunch2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        sizer_4.Add((15,-1))
        sizer_4.Add(grid_sizer_2, 0)
        sizer_4.Add((15,-1))
        sizer_3.Add(sizer_4, 0)
        sizer_3.Add((-1, 10))
        sizer_3.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        self.panel2.SetSizer(sizer_3)
        
        sizer_all.Add(self.panel1, 0, wx.EXPAND)
        sizer_all.Add(self.panel2, 0, wx.EXPAND)
        self.SetSizer(sizer_all)
        sizer_all.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = FluxSchedulerFrame(["CO2_H2O", "H2O_CH4", "CO2_CH4"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()