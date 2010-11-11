# -*- coding: iso-8859-15 -*-
import os
import sys
import wx
import wx.lib.agw.aui as aui
from SetupToolPages import *

BACKGROUND_COLOR_1 = "#FFF380"
BACKGROUND_COLOR_2 = "#E0FFFF"
BACKGROUND_COLOR_3 = "#BDEDFF"
BACKGROUND_COLOR_4 = "#BCE954"
BACKGROUND_COLOR_BOTTOM = "#43C6DB"

class SetupToolFrame(wx.Frame):
    def __init__(self, comPortList, *args, **kwds):
        #kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel4 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panelBottom = wx.Panel(self, -1)
        
        self.panel1.SetBackgroundColour(BACKGROUND_COLOR_1)
        self.panel2.SetBackgroundColour(BACKGROUND_COLOR_2)
        self.panel3.SetBackgroundColour(BACKGROUND_COLOR_3)
        self.panel4.SetBackgroundColour(BACKGROUND_COLOR_4)
        self.panelBottom.SetBackgroundColour(BACKGROUND_COLOR_BOTTOM)
        
        self.nb = aui.AuiNotebook(self, -1, agwStyle=aui.AUI_NB_CLOSE_ON_ALL_TABS|aui.AUI_NB_SCROLL_BUTTONS)
        #self.nb = aui.AuiNotebook(self, -1)
        self.nb.AddPage(self.panel1, "Data Logger")
        self.nb.AddPage(self.panel2, "Port Manager")
        self.nb.AddPage(self.panel3, "Data Delivery")
        self.nb.AddPage(self.panel4, "GUI Properties")
        for pageIdx in range(self.nb.GetPageCount()):
            self.nb.SetCloseButton(pageIdx, False)
        self.nbManager = self.nb.GetAuiManager()

        # Pages
        self.pages = []
        self.pages.append(Page1(self.panel1, -1))
        self.pages.append(Page2(comPortList, self.coordinatorPortList, self.panel2, -1))
        self.pages.append(Page3(self.panel3, -1))
        self.pages.append(Page4(self.panel4, -1))

        # Menu bar
        
        self.frameMenubar = wx.MenuBar()
        
        self.iSettings = wx.Menu()
        self.frameMenubar.Append(self.iSettings,"Settings")
        self.idInterface = wx.NewId()
        self.iInterface = wx.MenuItem(self.iSettings, self.idInterface, "Switch to Service Mode", "", wx.ITEM_NORMAL)
        self.iSettings.AppendItem(self.iInterface)
        self.SetMenuBar(self.frameMenubar)
        
        self.iHelp = wx.Menu()
        self.frameMenubar.Append(self.iHelp,"Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "About Setup Tool", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)
        
        # Overall properties
        self.SetTitle("Picarro Analyzer Setup Tool")
        self.labelFooter = wx.StaticText(self.panelBottom, -1, "Copyright Picarro, Inc. 1999-2010", style=wx.ALIGN_CENTER)

        # Mode selection
        self.labelMode = wx.StaticText(self.panelBottom, -1, "Mode")
        self.labelMode.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.comboBoxMode = wx.ComboBox(self.panelBottom, -1, choices = self.modeList, value = self.modeList[0], size = (150, -1), style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        # Buttons     
        self.buttonApply = wx.Button(self.panelBottom, -1, "Apply", style=wx.BU_EXACTFIT)                  
        self.buttonApply.SetMinSize((150, 20))
        self.buttonApply.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonApply.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonExit = wx.Button(self.panelBottom, -1, "Exit", style=wx.BU_EXACTFIT) 
        self.buttonExit.SetMinSize((150, 20))
        self.buttonExit.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonExit.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        
        self.doLayout()
  
    def doLayout(self):
        sizerToplevel = wx.BoxSizer(wx.VERTICAL)
        sizerToplevel.SetMinSize((650,700))
        
        # Add notebook
        sizerToplevel.Add(self.nb, 1, wx.EXPAND, 0)
        
        # Bottom section
        sizerPanelBottom = wx.BoxSizer(wx.HORIZONTAL)
        sizerPanelBottomMargin = wx.BoxSizer(wx.VERTICAL)

        sizerPanelBottom.Add(self.labelMode, 0, wx.ALL, 6)
        sizerPanelBottom.Add(self.comboBoxMode, 0, wx.ALL, 6)
        sizerPanelBottom.Add((20,-1))
        sizerPanelBottom.Add(self.buttonApply, 0, wx.ALL|wx.EXPAND, 6)
        sizerPanelBottom.Add((20,-1))
        sizerPanelBottom.Add(self.buttonExit, 0, wx.ALL|wx.EXPAND, 6)
        sizerPanelBottomMargin.Add(sizerPanelBottom, 0, wx.EXPAND|wx.ALL, 10)
        sizerPanelBottomMargin.Add(self.labelFooter, 0, wx.EXPAND|wx.BOTTOM, 5)
        self.panelBottom.SetSizer(sizerPanelBottomMargin)
        sizerToplevel.Add(self.panelBottom, 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 0)
        
        # Finalize the main frame and panel
        self.SetSizer(sizerToplevel)
        sizerToplevel.Fit(self)     
        self.Layout()
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = SetupToolFrame(["CFADS"], ["COM1", "COM2"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()