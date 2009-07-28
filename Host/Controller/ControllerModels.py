#!/usr/bin/python
#
# FILE:
#   ControllerModels.py
#
# DESCRIPTION:
#   Model objects for the controller
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   7-April-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import wx

from Host.Common import CmdFIFO, SharedTypes, timestamp
from Host.Common.Listener import Listener
from Host.Common.TextListener import TextListener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.autogen import interface

import inspect
from Queue import Queue
import socket

EventManagerProxy_Init("Controller")

waveforms = {}
parameterForms = {}
panels = {}

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="Controller")
            self.initialized = True

class RingdownListener(SharedTypes.Singleton):
    def __init__(self):
        self.listener = Listener(queue=None,
                            port = SharedTypes.BROADCAST_PORT_RDRESULTS,
                            elementType = interface.RingdownEntryType,
                            streamFilter = self.filter,
                            retry = True,
                            name = "Controller ringdown stream listener",
                            logFunc = Log)
    def  filter(self,data):
        panels["Ringdown"].appendData(data)

class SensorListener(SharedTypes.Singleton):
    def __init__(self):
        self.listener = Listener(queue=None,
                            port = SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                            elementType = interface.SensorEntryType,
                            streamFilter = self.filter,
                            retry = True,
                            name = "Controller sensor stream listener",
                            logFunc = Log)
        self.tempBuffer = dict(etalon1={},reference1={},etalon2={},reference2={})
        
    def  filter(self,data):
        utime = timestamp.unixTime(data.timestamp)
        value = data.value.asFloat
        if data.streamNum == interface.STREAM_Laser1Temp:
            waveforms["Laser1"]["temperature"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser2Temp:
            waveforms["Laser2"]["temperature"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser3Temp:
            waveforms["Laser3"]["temperature"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser4Temp:
            waveforms["Laser4"]["temperature"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser1Tec:
            waveforms["Laser1"]["tec"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser2Tec:
            waveforms["Laser2"]["tec"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser3Tec:
            waveforms["Laser3"]["tec"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser4Tec:
            waveforms["Laser4"]["tec"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser1Current:
            waveforms["Laser1"]["current"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser2Current:
            waveforms["Laser2"]["current"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser3Current:
            waveforms["Laser3"]["current"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Laser4Current:
            waveforms["Laser4"]["current"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Etalon1:
            waveforms["Wlm"]["etalon1"].Add(utime,value)
            if utime in self.tempBuffer["reference1"]:
                waveforms["Wlm"]["ratio1"].Add(utime,value/self.tempBuffer["reference1"][utime])
                del self.tempBuffer["reference1"][utime]
            else:
                self.tempBuffer["etalon1"][utime] = value
        elif data.streamNum == interface.STREAM_Reference1:
            waveforms["Wlm"]["reference1"].Add(utime,value)
            if utime in self.tempBuffer["etalon1"]:
                waveforms["Wlm"]["ratio1"].Add(utime,self.tempBuffer["etalon1"][utime]/value)
                del self.tempBuffer["etalon1"][utime]
            else:
                self.tempBuffer["reference1"][utime] = value
        elif data.streamNum == interface.STREAM_Etalon2:
            waveforms["Wlm"]["etalon2"].Add(utime,value)
            if utime in self.tempBuffer["reference2"]:
                waveforms["Wlm"]["ratio2"].Add(utime,value/self.tempBuffer["reference2"][utime])
                del self.tempBuffer["reference2"][utime]
            else:
                self.tempBuffer["etalon2"][utime] = value
        elif data.streamNum == interface.STREAM_Reference2:
            waveforms["Wlm"]["reference2"].Add(utime,value)
            if utime in self.tempBuffer["etalon2"]:
                waveforms["Wlm"]["ratio2"].Add(utime,self.tempBuffer["etalon2"][utime]/value)
                del self.tempBuffer["etalon2"][utime]
            else:
                self.tempBuffer["reference2"][utime] = value
        elif data.streamNum == interface.STREAM_Etalon2:
            waveforms["Wlm"]["etalon2"].Add(utime,value)
        elif data.streamNum == interface.STREAM_Reference2:
            waveforms["Wlm"]["reference2"].Add(utime,value)
        elif data.streamNum == interface.STREAM_CavityTemp:
            waveforms["HotBox"]["cavityTemperature"].Add(utime,value)
        elif data.streamNum == interface.STREAM_HotChamberTecTemp:
            waveforms["HotBox"]["heatsinkTemperature"].Add(utime,value)
        elif data.streamNum == interface.STREAM_HotChamberTec:
            waveforms["HotBox"]["tec"].Add(utime,value)
        elif data.streamNum == interface.STREAM_HotChamberHeater:
            waveforms["HotBox"]["heater"].Add(utime,value)

class LogListener(SharedTypes.Singleton):
    def __init__(self):
        self.queue = Queue()
        self.listener = TextListener(queue=self.queue,
                            port = SharedTypes.BROADCAST_PORT_EVENTLOG,
                            retry = True,
                            name = "Controller event log listener",
                            logFunc = Log)
    def  getLogMessage(self):
        if not self.queue.empty():
            wx.WakeUpIdle()
            return self.queue.get()

class ControllerRpcHandler(SharedTypes.Singleton):
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.server = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_CONTROLLER),
                                                 ServerName = "Controller",
                                                 ServerDescription = "Controller for CRDS hardware",
                                                 threaded = True)
            self._register_rpc_functions()
            self.notificationFunctions = []
            self.initialized = True

    def _register_rpc_functions_for_object(self, obj):
        """ Registers the functions in ControllerRpcHandler class which are accessible by XML-RPC

        NOTE - this automatically registers ALL member functions that don't start with '_'.

        i.e.:
          - if adding new rpc calls, just define them (with no _) and you're done
          - if putting helper calls in the class for some reason, use a _ prefix
        """
        classDir = dir(obj)
        for s in classDir:
            attr = obj.__getattribute__(s)
            if callable(attr) and (not s.startswith("_")) and (not inspect.isclass(attr)):
                #if __debug__: print "registering", s
                self.server.register_function(attr,DefaultMode=CmdFIFO.CMD_TYPE_Blocking)

    def _register_rpc_functions(self):
        """ Registers the functions accessible by XML-RPC """
        #register the functions contained in this file...
        self._register_rpc_functions_for_object( self )
        Log("Registered RPC functions")

    def version(self):
        return "Controller 1.0"

    def _registerNotification(self,func):
        """Register a notification function and return a token (the index
        in self.notificationFunctions) which is used to dispatch the
        function"""
        index = len(self.notificationFunctions)
        self.notificationFunctions.append(func)
        return index

    def notify(self,token):
        self.notificationFunctions[token]()
