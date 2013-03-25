import wx
import calendar
import time
from StreamDisplayPanelGui import StreamDisplayPanelGui
from Host.Common.GraphPanel import Series

def toUnixTime(s):
    x = s.split(".")
    t = calendar.timegm(time.strptime(x[0],"%Y%m%dT%H%M%S")) 
    if len(x)>1: t += float("." + x[1])
    return t
    
def safeFloat(s):
    try:
        return float(s)
    except:
        return 0.0

def makeEnv(dataList):
    env = {}
    env['Status'] = int(dataList[2])
    for i in range(14): env['Data%d' % (i+1,)] = safeFloat(dataList[3+i])
    return env
    
class StreamDisplayPanel(StreamDisplayPanelGui):
    def setSource(self,source,nCols,maxPoints):
        self.source = source
        self.nCols = nCols
        self.maxPoints = maxPoints
        self.waveform = Series(self.maxPoints)
        self.graph_panel_stream_display.SetGraphProperties(xlabel='Time',timeAxes=(True,False),ylabel='Value',
            grid=True,frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.graph_panel_stream_display.AddSeriesAsPoints(self.waveform,colour='blue',width=1,fillcolour='blue',marker='square',size=1)        
        self.whichColumn = wx.NOT_FOUND
        self.filter = ""
        self.update()
        
    def onDataSourceChange(self, event): # wxGlade: StreamDisplayPanelGui.<event_handler>
        self.getPlotData()
        event.Skip()

    def onFilterChange(self, event): # wxGlade: StreamDisplayPanelGui.<event_handler>
        self.getPlotData()
        event.Skip()
        
    def addToWaveform(self,dataList):
        t = toUnixTime(dataList[1])
        d = safeFloat(dataList[self.whichColumn+2])
        if self.filter:
            if eval(self.filter,makeEnv(dataList)):
                self.waveform.Add(t,d)
        else:
            self.waveform.Add(t,d)
        
    def getPlotData(self):
        ctl = self.combo_box_data_source
        self.whichColumn = ctl.GetSelection()
        self.filter = self.combo_box_filter.GetValue().strip()
        if self.whichColumn != wx.NOT_FOUND:
            self.waveform.Clear()
            for itemId in range(self.source.GetItemCount()):
                dataList = [self.source.GetItem(itemId,col).GetText() for col in range(self.nCols)]
                self.addToWaveform(dataList)
        self.update()
    
    def appendPlotDatum(self,dataList):
        if self.whichColumn != wx.NOT_FOUND:
            self.addToWaveform(dataList)
            self.update()
        
    def update(self):
        self.graph_panel_stream_display.Update(delay=0)
    