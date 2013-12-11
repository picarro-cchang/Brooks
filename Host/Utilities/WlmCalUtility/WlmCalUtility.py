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
from collections import deque
from configobj import ConfigObj
import sys
import getopt
from numpy import *
import os
from Queue import Queue, Empty
import time
import wx

from WlmCalUtilityGui import WlmCalUtilityGui

import Host.autogen.interface as interface
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes, WlmCalUtilities
from Host.Common.Listener import Listener
from Host.Common.GraphPanel import GraphPanel, Series
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
    
APP_NAME = "WlmCalUtility"

EventManagerProxy_Init(APP_NAME)

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection = False)

class Model(object):
    """A model consists of a set of properties which can be accessed using assignment notation.
    Use this by generating a subclass with the class variable propNames.

    propNames is the list of property names supported by the model
 
    Each property is associated with a field whose name is an underscore followed by the property name.
    The getter for the property returns the value of the field and the setter sets the field and calls
    any listeners who have registered an interest in the property.
    Attempting to access attributes which are not in the list of propNames raises an error
    """ 
    propNames = []
    def __init__(self):
        self.__class__.fieldNames = ["_" + p for p in self.__class__.propNames]
        object.__setattr__(self, "listeners", {})
        for propName, fieldName in zip(self.__class__.propNames, self.__class__.fieldNames):
            object.__setattr__(self, fieldName, None)
            def setter(self, value, f=fieldName, p=propName): 
                object.__setattr__(self, f, value)
                listeners = object.__getattribute__(self, "listeners")
                if p in listeners:
                    for listener in listeners[p]: 
                        listener(value)
            def getter(self, f=fieldName):
                return object.__getattribute__(self, f)
            setattr(self.__class__, propName, property(getter, setter))

    def __dir__(self):
        """List of available attributes and methods. Used by dir() in Python 2.6 and above"""
        return self.__class__.propNames + ['register_listener', 'remove_listener']

    def register_listener(self, propName, listener):
        """Specify a listener function that is called when property "propName" is assigned a value.
           The listener is passed the value which is assigned to propName"""
        if propName not in self.__class__.propNames:
            raise ValueError("No such property '%s'" % propName)
        listeners = object.__getattribute__(self, "listeners")
        if propName not in listeners:
            listeners[propName] = []
        listeners[propName].append(listener)

    def remove_listener(self, propName, listener):
        """Remove a listener that was previously registered"""
        listeners = object.__getattribute__(self, "listeners")
        if (propName not in listeners) or (listener not in listeners[propName]):
            raise ValueError("No such listener")
        listeners[propName].remove(listener)
        if not listeners[propName]: del listeners[propName]

    def __getattribute__(self, name):
        if name in object.__getattribute__(self,'__class__').propNames + \
            ['__class__', '__dir__', 'register_listener', 'remove_listener']:
            return object.__getattribute__(self, name)
        else:
            raise ValueError("No such property")

    def __setattr__(self, name, value):
        if name not in self.__class__.propNames:
            raise ValueError("No such property")
        else:
            object.__setattr__(self, name, value)

class WlmCalModel(Model):
    propNames = [ "etalon_1", "etalon_1_dark", "reference_1", "reference_1_dark", 
                   "etalon_2", "etalon_2_dark", "reference_2", "reference_2_dark", 
                   "ratio_1", "ratio_2", "center_1", "center_2",
                   "scale_1", "scale_2", "norm_scale_1", "norm_scale_2", 
                   "phase_deg", "phase_rad" ]
    pass

class SensorListener(object):
    # Listens to sensor broadcasts from the driver and lines up points with the
    # same timestamps.
    def __init__(self):
        self.doc = {}
        self.deque = deque()
        self.queue = Queue(0)                          
        self.listener = Listener(self.queue, SharedTypes.BROADCAST_PORT_SENSORSTREAM, SensorEntryType, self.streamFilter)
        self.sensorList = ["Laser1Temp", "Laser2Temp", "Laser3Temp", "Laser4Temp", "Etalon1", "Reference1", "Etalon2", "Reference2"]
        self.streams = [getattr(interface, "STREAM_" + s) for s in self.sensorList]
        self.sensorByStream = {}
        for st,s in zip(self.streams, self.sensorList):
            self.sensorByStream[st] = s
        self.fp = open(r"c:\temp\debug.txt","a")

    def streamFilter(self,result):
        while len(self.deque) >= 100: self.deque.popleft()
        self.deque.append((result.timestamp, result.streamNum, result.value))
        # This filter is designed to enqueue requested sensor entries which all have the same timestamp.
        if abs(self.doc.get("timestamp",0) - result.timestamp) > 1:
            if len(self.doc)>1:
                rDoc = self.doc.copy() 
                self.doc = { "timestamp": result.timestamp }
                if result.streamNum in self.sensorByStream:
                    self.doc[self.sensorByStream[result.streamNum]] = result.value
                if "Etalon1" not in rDoc:
                    for i in range(len(self.deque)):
                        d = self.deque[-i-1]
                        print >>self.fp, "%3d %15s %4s %15s" % (-i-1, d[0], d[1], d[2])
                    print >> self.fp
                return rDoc
            else:
                self.doc = { "timestamp": result.timestamp }
                if result.streamNum in self.sensorByStream:
                    self.doc[self.sensorByStream[result.streamNum]] = result.value
        else:
            self.doc[ "timestamp" ] = result.timestamp
            if result.streamNum in self.sensorByStream:
                self.doc[self.sensorByStream[result.streamNum]] = result.value

class WlmCalUtility(WlmCalUtilityGui):
    def __init__(self, *args, **kwds):
        WlmCalUtilityGui.__init__(self, *args, **kwds)
        self.clear = False
        self.measureDark = False
        self.maxDequeLength = 500
        self.ellipsePoints = 500
        self.etalon1Deque = deque()
        self.reference1Deque = deque()
        self.etalon2Deque = deque()
        self.reference2Deque = deque()
        self.ratio1Waveform = Series(self.maxDequeLength)
        self.ratio2Waveform = Series(self.maxDequeLength)
        self.polarWaveform  = Series(self.maxDequeLength)
        self.ellipse = Series(self.ellipsePoints)
        self.graph_ratios.RemoveAllSeries()
        self.graph_ratios.AddSeriesAsPoints(self.polarWaveform,colour='blue',fillcolour='blue',marker='square',size=1,width=1)
        self.graph_ratios.AddSeriesAsLine(self.ellipse,colour="red",width=2)

        self.model = WlmCalModel()
        self.displayNames = [ 
            ("etalon_1","%.1f"), 
            ("etalon_1_dark","%.1f"), 
            ("reference_1","%.1f"), 
            ("reference_1_dark","%.1f"), 
            ("etalon_2","%.1f"), 
            ("etalon_2_dark","%.1f"), 
            ("reference_2","%.1f"), 
            ("reference_2_dark","%.1f"), 
            ("ratio_1","%.3f"), 
            ("ratio_2","%.3f"), 
            ("center_1","%.3f"), 
            ("center_2","%.3f"),
            ("scale_1","%.3f"), 
            ("scale_2","%.3f"), 
            ("norm_scale_1","%.3f"), 
            ("norm_scale_2","%.3f"),
            ("phase_deg","%.1f"),
            ("phase_rad","%.3f")]
        # Make each edit box a listener to the corresponding model property
        for (name, fmt) in self.displayNames:
            def setTextCtrl(value, ctrlName="text_ctrl_"+name, fmt=fmt):
                getattr(self, ctrlName).SetValue(fmt % value)
            self.model.register_listener(name, setTextCtrl)

        self.editableNames = [ "etalon_1_dark", "reference_1_dark", 
                               "etalon_2_dark", "reference_2_dark" ]
        # Bind the events for text entry and loss of focus to change the model
        for name in self.editableNames:
            ctrlName = "text_ctrl_" + name
            def getTextCtrlValue(evt, varName = name):
                c = evt.GetEventObject()
                setattr(self.model, varName, float(c.GetValue()))
                if evt: evt.Skip()
            getattr(self, ctrlName).Bind(wx.EVT_TEXT_ENTER, getTextCtrlValue)
            getattr(self, ctrlName).Bind(wx.EVT_KILL_FOCUS, getTextCtrlValue)
        self.model.etalon_1_dark = 0
        self.model.etalon_2_dark = 0
        self.model.reference_1_dark = 0
        self.model.reference_2_dark = 0

        self.sL = SensorListener()
        bg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self.graph_ratios.SetGraphProperties(xlabel='Ratio 1',timeAxes=(False,False),ylabel='Ratio 2',
            grid=True,frameColour=bg,backgroundColour=bg,XSpec=(0,2),YSpec=(0,2))

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.onTimer,self.timer)
        self.timer.Start(1000)

    def onClearData(self, evt):
        self.clear = True

    def onMeasureDark(self, evt):
        self.measureDark = True
        
    def onSaveData(self, evt):
        print "onSaveData not yet implemented, coming soon!"

    def onTimer(self, evt):
        if self.clear or self.measureDark:
            self.etalon1Deque.clear()
            self.reference1Deque.clear()
            self.etalon2Deque.clear()
            self.reference2Deque.clear()
            self.clear = False
        while not self.sL.queue.empty():
            r = self.sL.queue.get()
            try:
                self.model.etalon_1 = r["Etalon1"]
                self.etalon1Deque.append(r["Etalon1"])
                if len(self.etalon1Deque) > self.maxDequeLength: self.etalon1Deque.popleft()
                self.model.etalon_2 = r["Etalon2"]
                self.etalon2Deque.append(r["Etalon2"])
                if len(self.etalon2Deque) > self.maxDequeLength: self.etalon2Deque.popleft()
                self.model.reference_1 = r["Reference1"]
                self.reference1Deque.append(r["Reference1"])
                if len(self.reference1Deque) > self.maxDequeLength: self.reference1Deque.popleft()
                self.model.reference_2 = r["Reference2"]
                self.reference2Deque.append(r["Reference2"])
                if len(self.reference2Deque) > self.maxDequeLength: self.reference2Deque.popleft()
            except:
                print "Error: ", r


        self.polarWaveform.Clear()
        self.ellipse.Clear()
        n = len(self.etalon1Deque)
        if self.measureDark and n>0:
            e1 = []
            r1 = []
            e2 = []
            r2 = []
            for i in range(n):
                e1.append(self.etalon1Deque[i])
                r1.append(self.reference1Deque[i])
                e2.append(self.etalon2Deque[i])
                r2.append(self.reference2Deque[i])
            e1 = asarray(e1)
            r1 = asarray(r1)
            e2 = asarray(e2)
            r2 = asarray(r2)
            self.model.etalon_1_dark = e1.mean()
            self.model.reference_1_dark = r1.mean()
            self.model.etalon_2_dark = e2.mean()
            self.model.reference_2_dark = r2.mean()
            self.measureDark = False
        r1 = []
        r2 = []
        for i in range(n):
            ratio1 = (self.etalon1Deque[i] - self.model.etalon_1_dark)/(self.reference1Deque[i] - self.model.reference_1_dark)
            ratio2 = (self.etalon2Deque[i] - self.model.etalon_2_dark)/(self.reference2Deque[i] - self.model.reference_2_dark)
            r1.append(ratio1)
            r2.append(ratio2)
            self.polarWaveform.Add(ratio1, ratio2)
        if n>0:
            self.model.ratio_1 = ratio1
            self.model.ratio_2 = ratio2
        r1 = asarray(r1)
        r2 = asarray(r2)
        self.model.center_1, self.model.center_2, self.model.scale_1, self.model.scale_2, phi = \
            WlmCalUtilities.parametricEllipse(r1, r2)

        if self.model.scale_1 < self.model.scale_2:
            self.model.norm_scale_2 = (self.model.scale_2 * float64(1.05)) / (self.model.scale_1)
            self.model.norm_scale_1  = float64(1.05)
        else:
            self.model.norm_scale_1 = (self.model.scale_1 * float64(1.05)) / (self.model.scale_2)
            self.model.norm_scale_2  = float64(1.05)

        self.model.phase_deg = phi * 180 / pi
        self.model.phase_rad = phi
        t = linspace(0.0, 2.0*pi, self.ellipsePoints)
        for x,y in zip(self.model.center_1 + self.model.scale_1 * cos(t),
                       self.model.center_2 + self.model.scale_2 * sin(t + phi)):
            self.ellipse.Add(x,y)
        self.graph_ratios.Update()


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = WlmCalUtility(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
