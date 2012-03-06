"""
File name: DrawOnPlatFrame.py
Purpose: The GUI frame for DrawOnPlatWithGui.py

File History:
    2012-03-01 Alex Lee  Created
"""

import wx
import time
import os

class DrawOnPlatFrame(wx.Frame):
    def __init__(self, defaults, *args, **kwds):
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Picarro Draw-On-Plat Utility")
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        
        self.platChoices = [""]

        # Other components
        buttonLabels = ["Load DAT file (.dat)", "Load PEAKS file (.peaks)", "Load PLAT BOUNDARIES file (.npz)",
                        "Load MISSED LEAKS file (.txt)", "Change TIF FILES directory", "Change OUTPUT directory",
                        "Change Minimum Amplitude"]
        self.buttonList = []
        self.textCtrlButton = []
        for i in range(len(buttonLabels)):
            button = wx.Button(self.panel1, -1, buttonLabels[i])   
            button.SetMinSize((300, 22))
            self.buttonList.append(button)
            textCtrl = wx.TextCtrl(self.panel1, -1, defaults[i], style = wx.TE_READONLY)
            textCtrl.SetMinSize((400, 22)) 
            self.textCtrlButton.append(textCtrl)
            
        self.textCtrlMsg = wx.TextCtrl(self.panel1, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrlMsg.SetMinSize((720, 100))        

        self.procButton = wx.Button(self.panel1, -1, "Create Plots", size = (400,22))
        
        self.labelFooter = wx.StaticText(self.panel2, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.FlexGridSizer(0, 2)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)

        for i in range(len(self.buttonList)):
            sizer_1.Add(self.buttonList[i], 0, wx.RIGHT|wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
            sizer_1.Add(self.textCtrlButton[i], 0, wx.RIGHT|wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_1.Add((0,0))
        sizer_1.Add(self.procButton, 0, wx.RIGHT|wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_2.Add(self.textCtrlMsg, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_2.Add(sizer_1, 0, wx.BOTTOM, 10)
        self.panel1.SetSizer(sizer_2)

        sizer_3.Add(self.labelFooter, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.panel2.SetSizer(sizer_3)

        sizer_4.Add(self.panel1, 0, wx.EXPAND, 0)
        sizer_4.Add(self.panel2, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_4)
        sizer_4.Fit(self)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = DrawOnPlatFrame(("", "", "", "", os.getcwd(), os.getcwd(), "0.1"), None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
    