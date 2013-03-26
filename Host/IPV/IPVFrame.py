import sys
from os.path import dirname, abspath
import wx
import wx.grid

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = abspath(AppPath)
    
SEC_TITLES = ["Laser Status", "Wavelength Monitor Status", "Cavity Status"]

class IPVFrame(wx.Frame):
    def __init__(self, numRowsList, *args, **kwds):
        #kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        self.numRowsList = numRowsList
        self.numSections = len(self.numRowsList)
        wx.Frame.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.panel_2 = wx.Panel(self, -1)
        self.panel_3 = wx.Panel(self, -1)
        self.sizer_3_staticbox = wx.StaticBox(self.panel_2, -1, "")
        self.label_1 = wx.StaticText(self.panel_1, -1, "Picarro Instrument Performance Verification", style=wx.ALIGN_CENTRE)
        self.labelFooter = wx.StaticText(self.panel_3, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.gridList = []
        self.gridLabelList = []
        for i in range(self.numSections):
            self.gridList.append(wx.grid.Grid(self.panel_2, -1, size=(1, 1)))
            gridLabel = wx.StaticText(self.panel_2, -1, SEC_TITLES[i], style=wx.ALIGN_CENTRE)
            gridLabel.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            gridLabel.SetForegroundColour('white')
            #gridLabel.SetBackgroundColour('blue')
            gridLabel.SetBackgroundColour('#736AFF')
            self.gridLabelList.append(gridLabel)
        
        self.textCtrlStatus = wx.TextCtrl(self.panel_3, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE)
        self.textCtrlStatus.SetMinSize((800,100))
        
        self.labelTimestamp = wx.StaticText(self.panel_3, -1, "Timestamp", size=(-1,25))
        self.labelTimestamp.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.textCtrlTimestamp = wx.TextCtrl(self.panel_3, -1, size=(152,24), style=wx.TE_READONLY|wx.TE_CENTER)
        self.buttonRunIPV = wx.Button(self.panel_3, -1, "Run IPV", size = (152,25), style=wx.BU_EXACTFIT)
        self.buttonUpload = wx.Button(self.panel_3, -1, "Upload Files", size = (152,25), style=wx.BU_EXACTFIT)
        self.buttonCreateDiagFile = wx.Button(self.panel_3, -1, "Create Diagnostic File (.h5)", size = (152,25), style=wx.BU_EXACTFIT)
        
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Picarro Instrument Performance Verification")
        self.SetBackgroundColour("#E0FFFF")
        self.panel_2.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.label_1.SetFont(wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.panel_1.SetFont(wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        for i in range(self.numSections):
            numRows = self.numRowsList[i]
            self.gridList[i].EnableEditing(False)
            self.gridList[i].SetDefaultCellAlignment(wx.ALIGN_LEFT,wx.ALIGN_CENTRE)
            self.gridList[i].SetDefaultCellFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
            self.gridList[i].CreateGrid(numRows, 2)
            self.gridList[i].SetColLabelValue(0, "Status")
            self.gridList[i].SetColSize(0, 120)
            self.gridList[i].SetColLabelValue(1, "Action")
            self.gridList[i].SetColSize(1, 480)
            self.gridList[i].SetRowLabelSize(180)
            for rowIdx in range(numRows):
                self.gridList[i].SetRowSize(rowIdx, 30)
        self.buttonRunIPV.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonCreateDiagFile.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonUpload.SetBackgroundColour(wx.Colour(237, 228, 199))
        
        #self.okBmp = wx.Bitmap(dirname(AppPath)+'/ok.png',wx.BITMAP_TYPE_PNG)
        #self.warningBmp = wx.Bitmap(dirname(AppPath)+'/warning.png',wx.BITMAP_TYPE_PNG)

    def __do_layout(self):
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.StaticBoxSizer(self.sizer_3_staticbox, wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        
        sizer_4.Add(self.label_1, 1, wx.ALL|wx.EXPAND, 15)
        self.panel_1.SetSizer(sizer_4)
        
        for i in range(self.numSections):
            sizer_3.Add(self.gridLabelList[i], 0, wx.EXPAND|wx.ALL, 6)
            sizer_3.Add(self.gridList[i], self.numRowsList[i]+2, wx.EXPAND|wx.ALL, 6)
        self.panel_2.SetSizer(sizer_3)
        
        sizer_5.Add(self.labelTimestamp, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 25)
        sizer_5.Add((10,-1))
        sizer_5.Add(self.textCtrlTimestamp, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 23)
        sizer_5.Add(self.buttonRunIPV, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 23)
        sizer_5.Add(self.buttonCreateDiagFile, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 23)
        sizer_5.Add(self.buttonUpload, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer_6.Add((-1,10))
        sizer_6.Add(self.textCtrlStatus, 0, wx.BOTTOM|wx.EXPAND, 15)
        sizer_6.Add(sizer_5)
        sizer_6.Add(self.labelFooter, 0, wx.TOP|wx.BOTTOM|wx.EXPAND, 15)
        self.panel_3.SetSizer(sizer_6)
        
        sizer_2.Add(self.panel_1, 0, wx.ALL|wx.EXPAND, 5)
        sizer_2.Add(self.panel_2, 2, wx.ALL|wx.EXPAND, 5)
        sizer_2.Add(self.panel_3, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer_2)
        self.Layout()
        height = 0
        for i in range(self.numSections):
            height = height + 40*(self.numRowsList[i]+1)+25
        height = height + 200
        self.SetSize((820, height+130))


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = IPVFrame([3,3,3], None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
