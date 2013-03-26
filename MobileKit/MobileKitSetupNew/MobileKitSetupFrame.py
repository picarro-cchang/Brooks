#!/usr/bin/env python
import sys
import os
import wx
import time
from wx.lib.masked import IpAddrCtrl
import  wx.lib.colourselect as  csel

OPACITY = ["100%", "75%", "50%", "25%"]
PANEL0_COLOR = "#A0FFFF"
PANEL1_COLOR = "#E0FFFF"
PANEL2_COLOR = "#BDEDFF"
PANEL3_COLOR = "#64E986"
CONC_COLOR = "#BDEDFF"
        
#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class SysAlarmListCtrl(wx.ListCtrl):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, numAlarms=2):
        wx.ListCtrl.__init__(self, parent, id, pos, size,
                             style = wx.LC_REPORT
                             | wx.LC_VIRTUAL
                             | wx.BORDER_NONE
                             | wx.LC_NO_HEADER)
        self.ilEventIcons = wx.ImageList(31, 16)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        self.SetBackgroundColour(PANEL0_COLOR)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)
        thisDir = os.path.dirname(AppPath)
        self.IconAlarmClear = myIL.Add(wx.Bitmap(thisDir + '/LEDgreen2.ico',
                                                     wx.BITMAP_TYPE_ICO))
        self.IconAlarmSet = myIL.Add(wx.Bitmap(thisDir + '/LEDred2.ico',
                                                     wx.BITMAP_TYPE_ICO))
        iconWidth = 35
        self.InsertColumn(0,"Icon",width=iconWidth)
        sx,sy = self.GetSize()
        self.InsertColumn(1,"Name",width=sx-iconWidth)
        self.SetItemCount(numAlarms)
        self.status = [0, 0, 0]
        self.statusText = ["Stream", "Analyzer", "GPS"]

    def OnGetItemText(self,item,col):
        if col == 1:
            return self.statusText[item]
        else:
            return

    def OnGetItemAttr(self,item):
        return
            
    def OnGetItemImage(self, item):
        if self.status[item]:
            return self.IconAlarmClear
        else:
            return self.IconAlarmSet
         
    def setMainForm(self, mainForm):
        self.mainForm = mainForm

    def setStatus(self, item, status):
        self.status[item] = status
        
    def refreshList(self):
        self.RefreshItems(0,self.GetItemCount()-1)
        
class MobileKitSetupFrame(wx.Frame):
    def __init__(self, concList, *args, **kwds):
        self.concList = concList
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Picarro Mobile Kit Setup")
        self.panel0 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER)
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER)
        self.panel3 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB|wx.SUNKEN_BORDER)
        self.panel0.SetBackgroundColour(PANEL0_COLOR)
        self.panel1.SetBackgroundColour(PANEL1_COLOR)
        self.panel2.SetBackgroundColour(PANEL2_COLOR)
        self.panel3.SetBackgroundColour(PANEL3_COLOR)

        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iControl = wx.Menu()
        
        self.frameMenubar.Append(self.iControl, "Control")
        self.iShutdown = wx.MenuItem(self.iControl, -1, "Shut Down Analyzer", "", wx.ITEM_NORMAL)
        self.iShutdown.SetBackgroundColour("red")
        self.iControl.AppendItem(self.iShutdown)
        
        self.SetMenuBar(self.frameMenubar)
        
        # System status alarms
        self.sysAlarmView = SysAlarmListCtrl(parent=self.panel0, numAlarms=3)
        self.sysAlarmView.setMainForm(self)
        
        # General Settings
        titleFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")
        labelFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "")
        concFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")
        buttonSize = (150, 25)
        buttonColor = wx.Colour(237, 228, 199)
        comboBoxSize = (100, 20)
        
        # labels
        self.labelStatus = wx.StaticText(self.panel0, -1, "Status", style=wx.ALIGN_CENTRE)
        self.labelStatus.SetFont(titleFont)
        self.labelTitle1 = wx.StaticText(self.panel1, -1, "Server Setup", style=wx.ALIGN_CENTRE)
        self.labelTitle1.SetFont(titleFont)
        self.labelIp = wx.StaticText(self.panel1, -1, "Analyzer IP Address", style=wx.ALIGN_CENTRE)
        self.labelIp.SetFont(labelFont)
        
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
        
        self.labelFooter = wx.StaticText(self.panel3, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        
        # Controls
        self.ipCtrl = IpAddrCtrl(self.panel1, -1)
        self.buttonLaunchServer = wx.Button(self.panel1, -1, "Launch Mobile Kit Server", size=buttonSize)
        self.buttonLaunchServer.SetBackgroundColour(buttonColor)
        self.buttonLaunchServer.SetFont(labelFont)

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
        
        self.buttonApply = wx.Button(self.panel2, -1, "Apply", size=buttonSize)
        self.buttonApply.SetBackgroundColour(buttonColor)
        self.buttonApply.SetFont(labelFont)
               
        self.buttonNewRun = wx.Button(self.panel3, -1, "Start a New Run", size=buttonSize)
        self.buttonNewRun.SetBackgroundColour(buttonColor)
        self.buttonNewRun.SetFont(labelFont)
        
        self.__do_layout()
        
    def __do_layout(self):
        sizer_0 = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_0_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 4)

        sizer_0.Add(self.labelStatus, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        sizer_0.Add(self.sysAlarmView, 0, wx.LEFT, 10)
        self.panel0.SetSizer(sizer_0)
        
        sizer_1.Add(self.labelTitle1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 10)
        sizer_2.Add((25,0))
        sizer_2.Add(self.labelIp, 0, wx.ALL, 5)
        sizer_2.Add((5,0))
        sizer_2.Add(self.ipCtrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        sizer_2.Add((10,0))
        sizer_1.Add((5,0))
        sizer_1.Add(sizer_2, 0)
        sizer_1.Add((0,10))
        sizer_1.Add(self.buttonLaunchServer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        sizer_1.Add((0,10))
        self.panel1.SetSizer(sizer_1)
        
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
        #sizer_3.Add((0,10))
        sizer_3.Add(self.buttonApply, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        sizer_3.Add((0,15))
        self.panel2.SetSizer(sizer_3)
        
        sizer_5.Add((0,15))
        sizer_5.Add(self.buttonNewRun, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        sizer_5.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        self.panel3.SetSizer(sizer_5)
        
        sizer_0_1.Add(self.panel0, 0, wx.EXPAND)
        sizer_0_1.Add(self.panel1, 1, wx.EXPAND)
        sizer_all.Add(sizer_0_1, 0, wx.EXPAND)
        sizer_all.Add(self.panel2, 0, wx.EXPAND)
        sizer_all.Add(self.panel3, 0, wx.EXPAND)
        self.SetSizer(sizer_all)
        sizer_all.Fit(self)
        #self.SetSize((500,-1))    
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = MobileKitSetupFrame(["CH4", "H2S"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()