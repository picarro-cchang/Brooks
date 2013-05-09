#!/usr/bin/python
#
# FILE:
#   WlmCalUtility.py
#
# DESCRIPTION:
#   Utility for calibration of wavelength monitor, e.g. for Mid IR analyzer
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   7-May-2013  sze  Initial version.
#
#  Copyright (c) 2013 Picarro, Inc. All rights reserved
#
from configobj import ConfigObj
import sys
import getopt
import os
from Queue import Queue, Empty
import time
import wx

from WlmCalUtilityGui import WlmCalUtilityGui

import Host.autogen.interface as interface
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.GraphPanel import GraphPanel
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
    
APP_NAME = "WlmCalUtility"

EventManagerProxy_Init(APP_NAME)

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection = False)


class SensorListener(object):
    # Listens to sensor broadcasts from the driver and lines up points with the
    # same timestamps.
    def __init__(self):
        self.queue = Queue(0)                          
        self.listener = Listener(self.queue,SharedTypes.BROADCAST_PORT_SENSORSTREAM,SensorEntryType)
        self.sensorList = ["Laser1Temp", "Laser2Temp", "Laser3Temp", "Laser4Temp", "Etalon1", "Reference1", "Etalon2", "Reference2"]
        self.streams = [getattr(interface, "STREAM_" + s) for s in self.sensorList]
        self.sensorByStream = {}
        for st,s in zip(self.streams, self.sensorList):
            self.sensorByStream[st] = s 

    def run(self):
        doc = {}
        while self.listener.isAlive():
            try:
                result = self.queue.get(timeout = 1.0)
                if doc.get("timestamp",0) != result.timestamp:
                    if len(doc)>1: print doc
                    doc = { "timestamp": result.timestamp }
                else:
                    if result.streamNum in self.sensorByStream:
                        doc[self.sensorByStream[result.streamNum]] = result.value
            except Empty:
                print "Queue empty"
                continue

class WlmCalUtility(WlmCalUtilityGui):
    def __init__(self, *args, **kwds):
        WlmCalUtilityGui.__init__(self, *args, **kwds)
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graph_ratios.SetGraphProperties(xlabel='Ratio 1',timeAxes=(False,False),ylabel='Ratio 2',
            grid=True,frameColour=bg,backgroundColour=bg)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.timer.Start(250)

    def onTimer(self,evt):
        self.graph_ratios.Update()


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = WlmCalUtility(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
    # sL = SensorListener()
    # sL.run()
