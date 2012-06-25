import wx
import socket
import sys

from ReceiverFrameGui import ReceiverFrameGui
from StreamDisplayPanel import StreamDisplayPanel
    
class ReceiverFrame(ReceiverFrameGui):
    MAX_DATA = 14
    MAX_ITEMS = 1000
    def __init__(self,*a,**k):
        ReceiverFrameGui.__init__(self,*a,**k)
        self.list_ctrl_stream.InsertColumn(0,"Identifier",width=100)
        self.list_ctrl_stream.InsertColumn(1,"Timestamp",width=150)
        self.list_ctrl_stream.InsertColumn(2,"Status",width=50)
        for dataCol in range(self.MAX_DATA):
            self.list_ctrl_stream.InsertColumn(3+dataCol,"Data %d" % (dataCol+1,),width=65)
        self.filterList = ["", "(Status & 256) != 0", "(Status & 512) != 0"]
        HOST, PORT = "", 5100
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.bind((HOST,PORT))
        self.socket.settimeout(0.1)
        self.seq = 0
        self.data = ""
        self.stream_display_panels = [self.stream_display_panel1, self.stream_display_panel2]
        for sdp in self.stream_display_panels:
            sdp.setSource(self.list_ctrl_stream,self.MAX_DATA+3,self.MAX_ITEMS)
            sdp.combo_box_data_source.Append('Status')
            for dataCol in range(self.MAX_DATA):
                sdp.combo_box_data_source.Append('Data%d' % (dataCol+1,))
            for filter in self.filterList:
                sdp.combo_box_filter.Append(filter)
        self.Bind(wx.EVT_IDLE, self.onIdle)
        self.updateTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onUpdateTimer,self.updateTimer)
        self.updateTimer.Start(milliseconds=1000)
        
    def onUpdateTimer(self,evt):
        wx.WakeUpIdle()
        evt.Skip()
        
    def onIdle(self,evt):
        try:
            self.data += self.socket.recv(1024)
            while True:
                sep = self.data.find("\n")
                if sep > 0:
                    data = self.data[:sep].strip().split(',')
                    while len(data)<self.MAX_DATA+3: data.append("") # Ensure that data has enough columns
                    if data:
                        index = self.list_ctrl_stream.InsertStringItem(sys.maxint,data[0])
                        if len(data)>1: self.list_ctrl_stream.SetStringItem(index,1,data[1])
                        if len(data)>2: self.list_ctrl_stream.SetStringItem(index,2,data[2])
                        for dataCol in range(self.MAX_DATA):
                            col = 3 + dataCol
                            if len(data)>col: 
                                self.list_ctrl_stream.SetStringItem(index,col,data[col])
                            else:
                                break
                        self.list_ctrl_stream.EnsureVisible(index)
                        if index > self.MAX_ITEMS: self.list_ctrl_stream.DeleteItem(0)
                    self.refreshGraphs(data)
                    self.data = self.data[sep+1:]
                else:
                    break
        except socket.timeout:
            pass
        evt.Skip()
    
    def refreshGraphs(self,dataList):
        for sdp in self.stream_display_panels:
            sdp.appendPlotDatum(dataList)
        
class ReceiverApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        frame_receiver = ReceiverFrame(None, -1, "")
        self.SetTopWindow(frame_receiver)
        frame_receiver.Show()
        return 1
        
    
# end of class ReceiverApp

if __name__ == "__main__":
    app = ReceiverApp(0)
    app.MainLoop()
    