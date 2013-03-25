import wx
from exFrame1Gui import ExFrame1Gui
import zmq
try:
    import json
except:
    import simplejson as json

context = zmq.Context()

CMD_PORT = 5101
BROADCAST_PORT = 5102

class ExFrame1(ExFrame1Gui):
    def __init__(self,*args,**kwargs):
        ExFrame1Gui.__init__(self,*args,**kwargs)
        self.cmdSock = context.socket(zmq.REQ)
        self.cmdSock.connect("tcp://127.0.0.1:%d" % CMD_PORT)
        self.broadcastSock = context.socket(zmq.SUB)
        self.broadcastSock.connect("tcp://127.0.0.1:%d" % BROADCAST_PORT)
        self.broadcastSock.setsockopt(zmq.SUBSCRIBE, "")
        self.poller = zmq.Poller()
        self.poller.register(self.broadcastSock, zmq.POLLIN)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.Bind(wx.EVT_CLOSE,self.onClose)
        self.timer.Start(20)
        
    def onTimer(self,evt):
        self.timer.Stop()
        socks = dict(self.poller.poll(timeout=0))
        if socks.get(self.broadcastSock) == zmq.POLLIN:
            packet = self.broadcastSock.recv()
            msg,data = packet.split("\n",2)
            print "Received packet", data
            self.text_ctrl_output.SetValue(data)
        self.timer.Start()
    
    def onEvaluate(self,evt):
        self.cmdSock.send(json.dumps({"func": "squareAndStore", "args":( float(self.text_ctrl_input.GetValue()),) }))
        self.cmdSock.recv()
        
    def onClose(self,evt):
        self.timer.Stop()
        self.cmdSock.close()
        self.broadcastSock.close()
        evt.Skip()
        
if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_example = ExFrame1(None, -1, "")
    app.SetTopWindow(frame_example)
    frame_example.Show()
    app.MainLoop()
