#!/usr/bin/env python

import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime

class DiagDataCollectorFrame(wx.Frame):
    def __init__(self, defaultHrs, maxHrs, *args, **kwds):
        kwds["style"] = wx.STAY_ON_TOP|wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("CRDS Diagnostic Data Collector")
        self.SetBackgroundColour("#E0FFFF")
        self.labelFooter = wx.StaticText(self, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        
        self.labelStartDate = wx.StaticText(self, -1, "Start Date/Time")
        self.ctrlStartDate = wx.DatePickerCtrl(self, -1, style = wx.DP_DROPDOWN)
        self.spinButtonStartTime = wx.SpinButton(self, -1, size=(17,22), style=wx.SP_VERTICAL)
        self.ctrlStartTime = TimeCtrl(self, -1, fmt24hr=True, spinButton=self.spinButtonStartTime)
        self.ctrlStartTime.SetValue(datetime.strftime(datetime.now(), "%H:%M:%S"))

        self.labelDataDur = wx.StaticText(self, -1, "Data Duration (hours)")
        self.spinCtrlDataDur = wx.SpinCtrl(self, -1, size=(89,-1), min=1, max=maxHrs, initial=defaultHrs)
        #self.labelEndDate = wx.StaticText(self, -1, "End Date/Time")
        #self.ctrlEndDate = wx.DatePickerCtrl(self, -1, style = wx.DP_DROPDOWN)
        #self.spinButtonEndTime = wx.SpinButton(self, -1, size=(17,22), style=wx.SP_VERTICAL)
        #self.ctrlEndTime = TimeCtrl(self, -1, fmt24hr=True, spinButton=self.spinButtonEndTime)  
        #self.ctrlEndTime.SetValue(datetime.strftime(datetime.now(), "%H:%M:%S"))

        self.textCtrlMsg = wx.TextCtrl(self, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH2)
        self.textCtrlMsg.SetMinSize((305, 50))
        
        self.buttonGetFile = wx.Button(self, -1, "Retrieve Diagnostic Data File", style=wx.BU_EXACTFIT)
        self.buttonGetFile.SetBackgroundColour(wx.Colour(237, 228, 199))
        
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.FlexGridSizer(-1, 4)
        grid_sizer_1.Add(self.labelStartDate, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.ctrlStartDate, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.ctrlStartTime, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.spinButtonStartTime, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.labelDataDur, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.spinCtrlDataDur, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        #grid_sizer_1.Add(self.labelEndDate, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        #grid_sizer_1.Add(self.ctrlEndDate, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        #grid_sizer_1.Add(self.ctrlEndTime, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        #grid_sizer_1.Add(self.spinButtonEndTime, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_2.Add(self.textCtrlMsg, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_3.Add((0,10), 0, wx.LEFT, 160)
        sizer_3.Add(self.buttonGetFile, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add(sizer_2, 0)
        sizer_1.Add(sizer_3, 0, wx.BOTTOM, 10)
        sizer_1.Add(self.labelFooter, 0, wx.EXPAND| wx.BOTTOM, 5)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = DiagDataCollectorFrame(12, 48, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()