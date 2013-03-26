#!/usr/bin/env python

import wx
import time
from wx.lib.masked import IpAddrCtrl
import  wx.lib.colourselect as  csel

COLORS = ["RED", "ORANGE", "YELLOW", "GREEN", "BLUE", "BLACK"]
OPACITY = ["100%", "75%", "50%", "25%"]

class MobileKitSetupFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Mobile Kit Setup")
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.panel3.SetBackgroundColour("#64E986")

        # General Settings
        titleFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")
        labelFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "")
        buttonSize = (150, 25)
        buttonColor = wx.Colour(237, 228, 199)
        comboBoxSize = (100, 20)
        
        # labels
        self.labelTitle1 = wx.StaticText(self.panel1, -1, "Server Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle1.SetFont(titleFont)
        self.labelIp = wx.StaticText(self.panel1, -1, "Analyzer IP Address", style=wx.ALIGN_CENTRE)
        self.labelIp.SetFont(labelFont)
        
        self.labelTitle2 = wx.StaticText(self.panel2, -1, "Graphical Properties", style=wx.ALIGN_CENTRE)
        self.labelTitle2.SetFont(titleFont)
        self.labelBaseline = wx.StaticText(self.panel2, -1, "Baseline", style=wx.ALIGN_CENTRE)
        self.labelBaseline.SetFont(labelFont)
        self.labelScaling = wx.StaticText(self.panel2, -1, "Scaling", style=wx.ALIGN_CENTRE)
        self.labelScaling.SetFont(labelFont)
        self.labelLineColor = wx.StaticText(self.panel2, -1, "Line Color", style=wx.ALIGN_CENTRE)
        self.labelLineColor.SetFont(labelFont)
        self.labelLineOpacity = wx.StaticText(self.panel2, -1, "Line Opacity", style=wx.ALIGN_CENTRE)
        self.labelLineOpacity.SetFont(labelFont)
        self.labelPolyColor = wx.StaticText(self.panel2, -1, "Polygon Color", style=wx.ALIGN_CENTRE)
        self.labelPolyColor.SetFont(labelFont)
        self.labelPolyOpacity = wx.StaticText(self.panel2, -1, "Polygon Opacity", style=wx.ALIGN_CENTRE)
        self.labelPolyOpacity.SetFont(labelFont)

        self.labelTitle3 = wx.StaticText(self.panel3, -1, "Control", style=wx.ALIGN_CENTRE)
        self.labelTitle3.SetFont(titleFont)
        self.labelFooter = wx.StaticText(self.panel3, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        
        # Divider lines
        self.staticLine1 = wx.StaticLine(self.panel1, -1, size=(0,3))
        self.staticLine2 = wx.StaticLine(self.panel2, -1, size=(0,3))
        
        # Controls
        self.ipCtrl = IpAddrCtrl(self.panel1, -1)
        self.buttonLaunchServer = wx.Button(self.panel1, -1, "Launch Mobile Kit Server", size=buttonSize)
        self.buttonLaunchServer.SetBackgroundColour(buttonColor)
        self.buttonLaunchServer.SetFont(labelFont)
        
        self.textCtrlBaseline = wx.TextCtrl(self.panel2, -1, "1.5", size=comboBoxSize)
        self.textCtrlScaling = wx.TextCtrl(self.panel2, -1, "100", size=comboBoxSize)
        self.cselLineColor = csel.ColourSelect(self.panel2, -1, "", (255, 0, 0), size = comboBoxSize)
        self.comboBoxLineOpacity = wx.ComboBox(self.panel2, -1, value = OPACITY[0], choices =OPACITY, size=comboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.cselPolyColor = csel.ColourSelect(self.panel2, -1, "", (255, 128, 0), size = comboBoxSize)
        self.comboBoxPolyOpacity = wx.ComboBox(self.panel2, -1, value = OPACITY[0], choices =OPACITY, size=comboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.buttonApply = wx.Button(self.panel2, -1, "Apply", size=buttonSize)
        self.buttonApply.SetBackgroundColour(buttonColor)
        self.buttonApply.SetFont(labelFont)
               
        self.buttonNewRun = wx.Button(self.panel3, -1, "Start a New Run", size=buttonSize)
        self.buttonNewRun.SetBackgroundColour(buttonColor)
        self.buttonNewRun.SetFont(labelFont)
        
        self.__do_layout()
        
    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 2)

        sizer_1.Add(self.labelTitle1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        sizer_2.Add((5,0))
        sizer_2.Add(self.labelIp, 0, wx.ALL, 5)
        sizer_2.Add((5,0))
        sizer_2.Add(self.ipCtrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        sizer_2.Add((10,0))
        sizer_1.Add((5,0))
        sizer_1.Add(sizer_2, 0)
        sizer_1.Add((0,10))
        sizer_1.Add(self.buttonLaunchServer, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 5)
        sizer_1.Add((0,10))
        sizer_1.Add(self.staticLine1, 0, wx.EXPAND)
        self.panel1.SetSizer(sizer_1)
        
        sizer_3.Add(self.labelTitle2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        grid_sizer_1.Add(self.labelBaseline, 0, wx.ALL|wx.ALIGN_LEFT, 3)
        grid_sizer_1.Add(self.textCtrlBaseline, 0, wx.ALL, 3)
        grid_sizer_1.Add(self.labelScaling, 0, wx.ALL|wx.ALIGN_LEFT, 3)
        grid_sizer_1.Add(self.textCtrlScaling, 0, wx.ALL, 3)
        grid_sizer_1.Add(self.labelLineColor, 0, wx.ALL|wx.ALIGN_LEFT, 3)
        grid_sizer_1.Add(self.cselLineColor, 0, wx.ALL, 3)
        grid_sizer_1.Add(self.labelPolyColor, 0, wx.ALL|wx.ALIGN_LEFT, 3)
        grid_sizer_1.Add(self.cselPolyColor, 0, wx.ALL, 3)
        grid_sizer_1.Add(self.labelLineOpacity, 0, wx.ALL|wx.ALIGN_LEFT, 3)
        grid_sizer_1.Add(self.comboBoxLineOpacity, 0, wx.ALL, 3)
        grid_sizer_1.Add(self.labelPolyOpacity, 0, wx.ALL|wx.ALIGN_LEFT, 3)
        grid_sizer_1.Add(self.comboBoxPolyOpacity, 0, wx.ALL, 3)
        sizer_4.Add((25,0))
        sizer_4.Add(grid_sizer_1, 0)
        #sizer_4.Add((5,0))
        sizer_3.Add((5,0))
        sizer_3.Add(sizer_4, 0)
        sizer_3.Add((0,10))
        sizer_3.Add(self.buttonApply, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 5)
        sizer_3.Add((0,10))
        sizer_3.Add(self.staticLine2, 0, wx.EXPAND)
        self.panel2.SetSizer(sizer_3)
        
        sizer_5.Add(self.labelTitle3, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        sizer_5.Add(self.buttonNewRun, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 3)
        #sizer_5.Add((0,5))
        sizer_5.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        self.panel3.SetSizer(sizer_5)
        
        sizer_all.Add(self.panel1, 0, wx.EXPAND)
        sizer_all.Add(self.panel2, 0, wx.EXPAND)
        sizer_all.Add(self.panel3, 0, wx.EXPAND)
        self.SetSizer(sizer_all)
        sizer_all.Fit(self)
        #self.SetSize((500,-1))    
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = MobileKitSetupFrame(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()