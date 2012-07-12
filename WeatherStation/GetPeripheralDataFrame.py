"""
File name: GetPeripheralDataFrame.py
Purpose: The GUI frame for GetPeripheralDataWithGui.py

File History:
    2012-02-24 Alex Lee  Created
"""

import wx
import time

class GetPeripheralDataFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Picarro Peripheral Data Processor")
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iFile = wx.Menu()

        self.frameMenubar.Append(self.iFile,"File")
        
        self.idLoadFileGps = wx.NewId()
        self.iLoadFileGps = wx.MenuItem(self.iFile, self.idLoadFileGps, "Load GPS file (.dat)", "", wx.ITEM_NORMAL)
        self.iFile.AppendItem(self.iLoadFileGps)
        
        self.idLoadFileWs = wx.NewId()
        self.iLoadFileWs = wx.MenuItem(self.iFile, self.idLoadFileWs, "Load WS file (.dat)", "", wx.ITEM_NORMAL)
        self.iFile.AppendItem(self.iLoadFileWs)
        
        self.idOutFile = wx.NewId()
        self.iOutFile = wx.MenuItem(self.iFile, self.idOutFile, "Specify output file (.txt)", "", wx.ITEM_NORMAL)
        self.iFile.AppendItem(self.iOutFile)
        
        self.SetMenuBar(self.frameMenubar)
        
        # Other components
        self.textCtrlMsg = wx.TextCtrl(self.panel1, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrlMsg.SetMinSize((300, 100))        

        self.procButton = wx.Button(self.panel1, -1, "Convert", size = (120,22))
        self.closeButton = wx.Button(self.panel1, wx.ID_CLOSE, "", size = (120,22))
        
        self.labelFooter = wx.StaticText(self.panel2, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)

        sizer_1.Add((22,0))
        sizer_1.Add(self.procButton, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_1.Add(self.closeButton, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
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
    frame = GetPeripheralDataFrame(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
    