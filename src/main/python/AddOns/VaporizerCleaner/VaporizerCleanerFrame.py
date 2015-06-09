# Embedded file name: VaporizerCleanerFrame.pyo
import wx

class VaporizerCleanerFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        kwds['style'] = wx.STAY_ON_TOP | wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle('Vaporizer Cleaner')
        self.SetBackgroundColour('#E0FFFF')
        self.frameMenubar = wx.MenuBar()
        self.iCtrl = wx.Menu()
        self.iHelp = wx.Menu()
        self.frameMenubar.Append(self.iCtrl, 'Control')
        self.idOutletValve = wx.NewId()
        self.iOutletValve = wx.MenuItem(self.iCtrl, self.idOutletValve, 'Open Outlet Valve', '', wx.ITEM_NORMAL)
        self.iCtrl.AppendItem(self.iOutletValve)
        self.idPumpdownRoutine = wx.NewId()
        self.iPumpdownRoutine = wx.MenuItem(self.iCtrl, self.idPumpdownRoutine, 'Start Vaporizer Pumpdown Routine', '', wx.ITEM_NORMAL)
        self.iCtrl.AppendItem(self.iPumpdownRoutine)
        self.frameMenubar.Append(self.iHelp, 'Help')
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, 'About Vaporizer Cleaner', '', wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)

        # copyright text updated with year info by main app
        self.labelFooter = wx.StaticText(self, -1, 'Copyright Picarro, Inc.', style=wx.ALIGN_CENTER)

        self.labelElapsedTime = wx.StaticText(self, -1, 'Elapsed Time (minutes)')
        self.textCtrlElapsedTime = wx.TextCtrl(self, -1, '0.00', style=wx.TE_READONLY)
        self.labelValve = []
        self.textCtrlValve = []
        for i in range(3):
            self.labelValve.append(wx.StaticText(self, -1, 'Valve %d Status' % (i + 1)))
            self.textCtrlValve.append(wx.TextCtrl(self, -1, 'Closed', style=wx.TE_READONLY))

        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(-1, 2)
        grid_sizer_1.Add(self.labelElapsedTime, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.textCtrlElapsedTime, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
        for i in range(len(self.labelValve)):
            grid_sizer_1.Add(self.labelValve[i], 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)
            grid_sizer_1.Add(self.textCtrlValve[i], 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, 10)

        grid_sizer_1.Add((-1, 10))
        sizer_1.Add(grid_sizer_1, 0)
        sizer_1.Add(self.labelFooter, 0, wx.EXPAND | wx.BOTTOM, 5)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()


if __name__ == '__main__':
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = VaporizerCleanerFrame(None, -1, '')
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()