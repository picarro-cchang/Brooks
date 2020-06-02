#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade HG on Sun Feb 19 22:29:31 2012

import wx

# begin wxGlade: extracode
from Host.Common.GraphPanel import GraphPanel
# end wxGlade


class GraphicsFrameGui(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: GraphicsFrameGui.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.graphPanelMain = GraphPanel(self, -1)
        self.panel_1 = wx.Panel(self, -1)
        self.buttonPlot = wx.Button(self.panel_1, -1, "Plot")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onPlot, self.buttonPlot)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: GraphicsFrameGui.__set_properties
        self.SetTitle("Graph Panel Test")
        self.SetSize((800, 600))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: GraphicsFrameGui.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.graphPanelMain, 1, wx.EXPAND, 0)
        sizer_2.Add(self.buttonPlot, 0, wx.ALL, 10)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def onPlot(self, event):  # wxGlade: GraphicsFrameGui.<event_handler>
        print "Event handler `onPlot' not implemented!"
        event.Skip()


# end of class GraphicsFrameGui

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frameMain = GraphicsFrameGui(None, -1, "")
    app.SetTopWindow(frameMain)
    frameMain.Show()
    app.MainLoop()
