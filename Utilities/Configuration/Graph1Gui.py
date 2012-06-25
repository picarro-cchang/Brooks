#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import wx
from Host.Common.GraphPanel import GraphPanel

class PageOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageOne object", (20,20))

class PageTwo(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageTwo object", (40,40))
     
class PageThree(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageThree object", (60,60))

class MyFrameGui(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.graphPanel1 = GraphPanel(self, -1)
        self.keys=['ambientPressure','pztValue','uncorrectedAbsorbance','ratio1','laserTemperature','ratio2','etalonTemperature','schemeTable','tunerValue','timestamp',
              'correctedAbsorbance','waveNumberSetpoint','ringdownThreshold','status','cavityPressure','subschemeId','lockerOffset','count','coarseLaserCurrent',
              'waveNumber','laserUsed','schemeRow','fineLaserCurrent','lockerError']
        
      
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_LISTBOX, self.OnListBoxYSelected, self.ListboxY)
        self.Bind(wx.EVT_LISTBOX, self.OnListBoxXSelected, self.ListboxX)
        self.Bind(wx.EVT_BUTTON, self.onClear, self.clearButton)

    def __set_properties(self):
        self.SetTitle("RD Graph")
        self.SetSize((640, 480))
        self.graphPanel1.SetMinSize((535, 325))

    def __do_layout(self):
        self.p = wx.Panel(self, -1)
        self.nb = wx.Notebook(self.p)
        
        self.panel_1 = wx.Panel(self.nb, -1)
        self.page1 = PageOne(self.nb)
        self.page2 = PageTwo(self.nb)
        self.page3 = PageThree(self.nb)
        
        self.ListBoxYLabel = wx.StaticText(self.panel_1,-1,"Y Axis")        
        self.ListboxY = wx.ListBox(self.panel_1, -1, choices=self.keys, style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        self.ListBoxXLabel = wx.StaticText(self.panel_1,-1,"X Axis")        
        self.ListboxX = wx.ListBox(self.panel_1, -1, choices=self.keys, style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        self.clearButton = wx.Button(self.panel_1, -1, "Clear")
        self.ListboxY.SetMinSize((140, 155))
        self.ListboxY.SetSelection(0)
        self.ListboxX.SetMinSize((140, 155))
        self.ListboxX.SetSelection(0)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.nb, 1, wx.EXPAND)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ListBoxYLabel, 0, wx.ALIGN_CENTER | wx.TOP, 10)
        sizer_2.Add(self.ListboxY, 0, wx.ALL, 0)
        sizer_2.Add(self.ListBoxXLabel, 0, wx.ALIGN_CENTER | wx.TOP, 10)
        sizer_2.Add(self.ListboxX, 0, wx.ALL, 0)
        sizer_2.Add(self.clearButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        sizer_1.Add(self.graphPanel1, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        
        self.nb.AddPage(self.panel_1, "Page 0")
        self.nb.AddPage(self.page1, "Page 1")
        self.nb.AddPage(self.page2, "Page 2")
        self.nb.AddPage(self.page3, "Page 3")
        
        #self.p.SetSizer(sizer)
        self.SetSizer(sizer)
        self.Layout()

    def OnListBoxXSelected(self, event): 
        print "Event handler `OnGraphTypeListBoxSelected' not implemented!"
        event.Skip()

    def OnListBoxYSelected(self, event): 
        print "Event handler `OnGraphTypeListBoxSelected' not implemented!"
        event.Skip()

    def onClear(self, event): 
        print "Event handler `onClear' not implemented!"
        event.Skip()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    Graph = (None, -1, "")
    app.SetTopWindow(Graph)
    Graph.Show()
    app.MainLoop()
