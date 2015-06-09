import wx

from Host.MfgUtilities.Configuration.Graph1Gui import MyFrameGui
from Host.Common.GraphPanel import Series
from numpy import *

class MyFrame(MyFrameGui):
    def __init__(self,*a,**k):
        MyFrameGui.__init__(self,*a,**k)
        self.graphPanel1.SetGraphProperties(xlabel='Angle',timeAxes=(False,False),ylabel='Sine',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.waveform = Series(5000)
        self.graphPanel1.AddSeriesAsLine(self.waveform,colour='red',width=2)
        self.i0 = 0

    def  update(self):
        self.graphPanel1.Update(delay=0)

    def onPlot(self, event):
        for i in range(500):
            x = 2.0*pi*(self.i0+i)/500.0
            self.waveform.Add(x,sin(x))
        self.i0 += 500
        self.update()

    def onClear(self, event):
        self.waveform.Clear()
        self.update()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()