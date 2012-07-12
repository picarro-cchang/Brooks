#!/usr/bin/env python
import sys
import os
import wx
import time
from wx.lib.masked import IpAddrCtrl
import  wx.lib.colourselect as  csel

OPACITY = ["100%", "75%", "50%", "25%"]
PANEL1_COLOR = "#E0FFFF"
PANEL2_COLOR = "#BDEDFF"
CONC_COLOR = "#BDEDFF"
        
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)
        
class RemoteMobileKitSetupFrame(wx.Frame):
    def __init__(self, concList, *args, **kwds):
        self.concList = concList
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Picarro Mobile Kit Setup (Remote)")
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER)
        self.panel1.SetBackgroundColour(PANEL1_COLOR)
        self.panel2.SetBackgroundColour(PANEL2_COLOR)

        # General Settings
        titleFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")
        labelFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "")
        concFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")
        buttonSize = (150, 25)
        buttonColor = wx.Colour(237, 228, 199)
        comboBoxSize = (100, 20)
        longComboBoxSize = (300, 20)
        
        # labels
        self.labelAnalyzer = wx.StaticText(self.panel1, -1, "Analyzer", style=wx.ALIGN_CENTRE)
        self.labelAnalyzer.SetFont(titleFont)
        self.labelData = wx.StaticText(self.panel1, -1, "Data", style=wx.ALIGN_CENTRE)
        self.labelData.SetFont(titleFont)
        
        self.labelTitle1 = wx.StaticText(self.panel1, -1, "Select Analyzer Data", style=wx.ALIGN_CENTRE)
        self.labelTitle1.SetFont(titleFont)
        
        self.labelTitle2 = wx.StaticText(self.panel2, -1, "Graphical Properties", style=wx.ALIGN_CENTRE)
        self.labelTitle2.SetFont(titleFont)

        self.labelName = []
        self.labelDisplay = []
        self.labelBaseline = []
        self.labelScaling = []
        self.labelLineColor = []
        self.labelLineOpacity = []
        self.labelPolyColor = []
        self.labelPolyOpacity = []
        for conc in self.concList:
            label = wx.StaticText(self.panel2, -1, conc, style=wx.ALIGN_CENTRE)
            label.SetFont(titleFont)
            self.labelName.append(label)
            label = wx.StaticText(self.panel2, -1, "Visible", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelDisplay.append(label)
            label = wx.StaticText(self.panel2, -1, "Baseline", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelBaseline.append(label)
            label = wx.StaticText(self.panel2, -1, "Scaling", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelScaling.append(label)
            label = wx.StaticText(self.panel2, -1, "Line Color", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelLineColor.append(label)
            label = wx.StaticText(self.panel2, -1, "Line Opacity", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelLineOpacity.append(label)
            label = wx.StaticText(self.panel2, -1, "Polygon Color", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelPolyColor.append(label)
            label = wx.StaticText(self.panel2, -1, "Polygon Opacity", style=wx.ALIGN_CENTRE)
            label.SetFont(labelFont)
            self.labelPolyOpacity.append(label)
        
        self.labelFooter = wx.StaticText(self.panel2, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        
        # Controls
        self.analyzerCtrl = wx.ComboBox(self.panel1, -1, choices = [""], size=longComboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.dataCtrl = wx.ComboBox(self.panel1, -1, choices = [""], size=longComboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        self.comboBoxOnOff = []
        self.textCtrlConc = []
        self.textCtrlBaseline = []
        self.textCtrlScaling = []
        self.cselLineColor = []
        self.comboBoxLineOpacity = []
        self.cselPolyColor = []
        self.comboBoxPolyOpacity = []
        for conc in self.concList:
            self.comboBoxOnOff.append(wx.ComboBox(self.panel2, -1, value = "ON", choices = ["ON", "OFF"], size=comboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN))
            textCtrlConc = wx.TextCtrl(self.panel2, -1, "0.0", size=comboBoxSize, style=wx.TE_READONLY|wx.BORDER_NONE)
            textCtrlConc.SetBackgroundColour(CONC_COLOR)
            textCtrlConc.SetFont(titleFont)
            self.textCtrlConc.append(textCtrlConc)
            self.textCtrlBaseline.append(wx.TextCtrl(self.panel2, -1, "1.5", size=comboBoxSize))
            self.textCtrlScaling.append(wx.TextCtrl(self.panel2, -1, "100", size=comboBoxSize))
            self.cselLineColor.append(csel.ColourSelect(self.panel2, -1, "", (255, 0, 0), size = comboBoxSize))
            self.comboBoxLineOpacity.append(wx.ComboBox(self.panel2, -1, value = OPACITY[0], choices =OPACITY, size=comboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN))
            self.cselPolyColor.append(csel.ColourSelect(self.panel2, -1, "", (255, 128, 0), size = comboBoxSize))
            self.comboBoxPolyOpacity.append(wx.ComboBox(self.panel2, -1, value = OPACITY[0], choices =OPACITY, size=comboBoxSize, style = wx.CB_READONLY|wx.CB_DROPDOWN))
        
        self.buttonApplyTop = wx.Button(self.panel1, -1, "Apply", size=buttonSize)
        self.buttonApplyTop.SetBackgroundColour(buttonColor)
        self.buttonApplyTop.SetFont(labelFont)
        
        self.buttonApplyBottom = wx.Button(self.panel2, -1, "Apply", size=buttonSize)
        self.buttonApplyBottom.SetBackgroundColour(buttonColor)
        self.buttonApplyBottom.SetFont(labelFont) 
        
        self.__do_layout()
        
    def __do_layout(self):
        sizer_1 = wx.FlexGridSizer(0, 2)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 4)

        sizer_1.Add(self.labelAnalyzer, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
        sizer_1.Add(self.analyzerCtrl, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        sizer_1.Add(self.labelData, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
        sizer_1.Add(self.dataCtrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        
        sizer_2.Add(self.labelTitle1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        sizer_2.Add(sizer_1)
        sizer_2.Add(self.buttonApplyTop, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        self.panel1.SetSizer(sizer_2)
        
        sizer_3.Add(self.labelTitle2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        
        for i in range(len(self.concList)):
            grid_sizer_1.Add(self.labelName[i], 0, wx.ALL|wx.ALIGN_LEFT, 3)
            grid_sizer_1.Add(self.textCtrlConc[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelDisplay[i], 0, wx.ALL|wx.ALIGN_LEFT, 3)
            grid_sizer_1.Add(self.comboBoxOnOff[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelBaseline[i], 0, wx.ALL|wx.ALIGN_LEFT, 3)
            grid_sizer_1.Add(self.textCtrlBaseline[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelScaling[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.textCtrlScaling[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelLineColor[i], 0, wx.ALL|wx.ALIGN_LEFT, 3)
            grid_sizer_1.Add(self.cselLineColor[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelLineOpacity[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.comboBoxLineOpacity[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelPolyColor[i], 0, wx.ALL|wx.ALIGN_LEFT, 3)
            grid_sizer_1.Add(self.cselPolyColor[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.labelPolyOpacity[i], 0, wx.ALL, 3)
            grid_sizer_1.Add(self.comboBoxPolyOpacity[i], 0, wx.ALL, 3)
            for j in range(4):
                grid_sizer_1.Add((0,0), 0, wx.ALL, 5)

        sizer_4.Add((10,0))
        sizer_4.Add(grid_sizer_1, 0)
        sizer_4.Add((10,0))
        sizer_3.Add((5,0))
        sizer_3.Add(sizer_4, 0)
        sizer_3.Add((0,10))
        sizer_3.Add(self.buttonApplyBottom, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        sizer_3.Add((0,15))
        sizer_3.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        self.panel2.SetSizer(sizer_3)

        sizer_all.Add(self.panel1, 0, wx.EXPAND)
        sizer_all.Add(self.panel2, 0, wx.EXPAND)
        self.SetSizer(sizer_all)
        sizer_all.Fit(self)
        #self.SetSize((500,-1))    
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = RemoteMobileKitSetupFrame(["CH4", "H2S"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()