#!/usr/bin/env python

import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime

class StopSupervisorFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Stop CRDS Software")
        self.SetBackgroundColour("#E0FFFF")
        
        # labels
        self.labelTitle = wx.StaticText(self, -1, "Stop CRDS Software", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        
        # button
        self.buttonStop = wx.Button(self, -1, "Stop", style=wx.ALIGN_CENTRE, size=(110, 20))
        self.buttonStop.SetBackgroundColour(wx.Colour(237, 228, 199))
        
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_1.Add(self.labelTitle, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.buttonStop, 0, wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = StopSupervisorFrame(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()