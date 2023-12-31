#!/usr/bin/env python

import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime


class FluxSwitcherGuiFrame(wx.Frame):
    def __init__(self, typeChoices, flux, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        if flux:
            self.SetTitle("Picarro Flux Mode Switcher")
        else:
            self.SetTitle("Picarro Quick Mode Switcher")
        self.SetBackgroundColour("#E0FFFF")

        # labels
        if flux:
            self.labelTitle = wx.StaticText(self, -1, "Picarro Flux Mode Switcher", style=wx.ALIGN_CENTRE)
        else:
            self.labelTitle = wx.StaticText(self, -1, "Picarro Quick Mode Switcher", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelFooter = wx.StaticText(self, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.labelSelect = wx.StaticText(self, -1, "Select Measurement Mode", style=wx.ALIGN_CENTER)

        # Divider line
        self.staticLine = wx.StaticLine(self, -1)

        # controls
        self.comboBoxSelect = wx.ComboBox(self,
                                          -1,
                                          value=typeChoices[0],
                                          choices=typeChoices,
                                          style=wx.CB_READONLY | wx.CB_DROPDOWN)

        # button
        self.buttonLaunch = wx.Button(self, -1, "Launch", size=(110, 20))
        self.buttonLaunch.SetBackgroundColour(wx.Colour(237, 228, 199))

        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 2)

        sizer_1.Add(self.labelTitle, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.staticLine, 0, wx.EXPAND, 0)
        sizer_1.Add((-1, 10))
        grid_sizer_1.Add(self.labelSelect, 0, wx.LEFT, 20)
        grid_sizer_1.Add(self.comboBoxSelect, 0, wx.LEFT | wx.RIGHT, 10)
        grid_sizer_1.Add((100, -1))
        grid_sizer_1.Add(self.buttonLaunch, 0, wx.LEFT | wx.TOP | wx.ALIGN_BOTTOM | wx.RIGHT, 10)
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add((-1, 10))
        sizer_1.Add(self.labelFooter, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, 10)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = FluxSwitcherGuiFrame(["CO2_CH4", "CO2_H2O"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
