"""
Copyright (c) 2015 Picarro, Inc. All rights reserved
"""

import threading
import serial
import time
import os
import sys
import wx
import gettext
import Queue
import math

from Host.O2SensorMonitor.O2SensorCalibration import O2CalDlg
from Host.autogen import interface
from Host.Common import CmdFIFO
from Host.Common.Listener import Listener
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_O2_SENSOR_MONITOR, BROADCAST_PORT_SENSORSTREAM
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init
from Host.Common.CustomConfigObj import CustomConfigObj 

APP_NAME = "O2DataStream"

EventManagerProxy_Init(APP_NAME)

class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
          
class O2SensorMonitor(O2CalDlg):
    def __init__(self, configFile, showGui, *args, **kwds):
        O2CalDlg.__init__(self, *args, **kwds)
        if not os.path.exists(configFile):
            raise Exception("Configuration file '%s' not found." % configFile)
        else:
            self.config = CustomConfigObj(configFile)
            self.port = self.config.get("SETUP", "Port", "COM2")
            self.baudrate = self.config.getint("SETUP", "BaudRate", 19200)
        self.GuiOn = False
        if showGui:
            self.showGui()
        self.sensorQueue = Queue.Queue(0)
        self.ser = None
        self.columnNames = [("O2_STATUS"), ("O2_PRESSURE"), ("O2_CONC"),
                            ("O2_TEMPERATURE"), ("O2_PHASE_SHIFT")]
        try:
            self.spectrumCollector = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
                                    APP_NAME, IsDontCareConnection=False)
        except:
            self.spectrumCollector = None
        self.SensorListener = Listener(None,
                                     BROADCAST_PORT_SENSORSTREAM,
                                     interface.SensorEntryType,
                                     self._SensorFilter,
                                     retry = True,
                                     name = "O2 Monitor sensor stream listener",logFunc = Log)
        self.startServer()  # RPC server is in a different thread
        self.startMonitor() # O2 monitor is also in a separate thread
        self.generateDummyData()
        
    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_O2_SENSOR_MONITOR),
                                       ServerName="O2DataStream",
                                       ServerDescription="O2DataStream",
                                       ServerVersion="1.0",
                                       threaded=True)
        #Register the rpc functions...
        self.rpcServer.register_function(self.showGui)
        # Start the rpc server on another thread...
        self.rpcThread = RpcServerThread(self.rpcServer, self.Destroy)
        self.rpcThread.start()
    
    def _SensorFilter(self, obj):
        if obj.streamNum == 20: # STREAM_CavityPressure
            self.sensorQueue.put(obj.value)
            
    def _getCavityPressure(self):
        valueList = []
        while True:
            try:
                valueList.append(self.sensorQueue.get(block=False))
            except:
                if len(valueList) > 0:
                    return sum(valueList) / len(valueList)  # average cavity pressure
                else:
                    return None
    
    def setTagalong(self,header,value):
        try:
            self.spectrumCollector.setTagalongData(header,value)
        except:
            pass
            
    def openPort(self):
        try:
            Log("Trying to open serial port") 
            ser = serial.Serial(self.port, self.baudrate, timeout=3)
            time.sleep(1)
            ser.write("mode0001\r") # request mode H2M
            time.sleep(0.5)
            ser.write("pcco0000\r")   # Pulse Counter will not be increased
            time.sleep(0.5)
            #ser.write("oxyu0001\r")   # unit %O2
            ser.write("oxyu0003\r")   # unit torr (partial pressure)
            time.sleep(0.5)
            ser.write("mmwr0000\r")   # Deactivate Saving to Flash Memory
            time.sleep(0.5)
            ser.write("data\r")
            identStr = ser.readline()
            if len(identStr) > 0:
                self.ser = ser
                self.btnNext.Enable()
                Log("O2 Sensor connected!")
            else:
                Log("Cannot open serial port", Level=3)
        except serial.SerialException:
            Log("Cannot open serial port, serial exception", Level=3)
            raise
        except ValueError:
            Log("Serial port parameters out of range!", Level=3)
            raise

    def generateDummyData(self):
        for header in self.columnNames:
            self.setTagalong(header, -9999.0)
            
    def calcData(self,datlist):
        valueList = []
        try:
            msg = datlist.split(";")
            status = int(msg[5][1:])
            try:
                o2pres = .01*float(msg[4][1:])  # partial pressure of O2
            except:
                if msg[4][1:].startswith("0000-"):
                    o2pres = 0.0
                else:
                    raise
            cavityPres = self._getCavityPressure()
            if cavityPres is not None:
                o2conc = o2pres / cavityPres * 100 
            else:
                Log("Error reading cavity pressure!")
                return False
            temperature = .01*float(msg[3][1:])
            phase = .01*float(msg[2][1:])
            valueList = [status, o2pres, o2conc, temperature, phase]
        except Exception, err:
            LogExc("%r" % err) 
            return False
        return valueList
    
    def showGui(self):
        if not self.GuiOn:
            self.Show(True)
            self.GuiOn = True
            self.labelInfo.SetLabel("STEP1: Connect analyzer to 0% O2 environment.")
            variation = u"\u00B1" + "0.1"
            self.labelInfo2.SetLabel("Click 'Next' when variation of PhaseShift < " + variation + u"\u00B0")
            self.labelInfo3.SetLabel("And variation of Temperature < " + variation + u"\u2103.")
            self.txtO2Concentration.SetValue("0.0%") 
            self.txtO2Concentration.SetEditable(False)
            
    def OnNext(self, event):  
        msg = self.txtO2Concentration.GetValue()
        self.ser.write(msg + "\r")
        msg = self.labelInfo.GetLabel()
        if msg.startswith("STEP1"):
            ps = float(self.labelPhaseShift.GetLabel())
            t = float(self.labelTemperature.GetLabel())
            self.cal1point = (ps, t)
            self.labelInfo.SetLabel("STEP2: Connect analyzer to atmosphere.")
            self.txtO2Concentration.SetValue("20.95%")
            self.btnCancel.SetLabel('Cancel')            
        elif msg.startswith("STEP2"):
            self.btnNext.Disable()
            self.btnCancel.Disable()
            o2 = self.txtO2Concentration.GetValue().strip()
            if o2.endswith('%'):
                o2 = o2[:-1]
            conc = math.modf(float(o2))     # Return the fractional and integer parts of O2
            self.ser.write("mmwr0001\r")   # activate Saving to Flash Memory
            time.sleep(0.5)
            self.ser.write("calt0001\r") # calibration with dry gases
            time.sleep(0.5)
            self.ser.write("malt0001\r")   # measurement with dry gases
            time.sleep(0.5)
            self.ser.write("clun0001\r")   # Oxygen unit (%O2) for the 2nd calibration value
            time.sleep(0.5)
            self.ser.write("cloi%04d\r" % conc[1])  # set the integer part of the oxygen concentration
            time.sleep(0.5)
            self.ser.write("clof%04d\r" % (conc[0]*1000))   # set the fraction part of the oxygen concentration
            time.sleep(0.5)
            if self.cal1point is not None:
                self.ser.write("clzp%04d\r" % (self.cal1point[0]*100))  # set the phase value for 1st calibration point
                time.sleep(0.5)
                self.ser.write("clzt%04d\r" % (self.cal1point[1]*100))  # set the temperature value for 1st calibration point
                time.sleep(0.5)
            self.ser.write("calh\r")    # set the current phase and temperature values for a 2nd calibration point
            time.sleep(0.5)
            p = self._getCavityPressure() * 1.333224    # unit: hPa
            self.ser.write("calp%04d\r" % p)    # Set atmospheric pressure during calibration
            time.sleep(0.5)
            self.ser.write("malp%04d\r" % p)    # Set the measurement atmospheric pressure
            time.sleep(0.5)
            self.ser.write("mmwr0000\r")   # Deactivate Saving to Flash Memory
            time.sleep(0.5)
            d = wx.MessageDialog(None, "Calibration done!", "Information", style=wx.OK | wx.ICON_INFORMATION)
            d.ShowModal()
            d.Destroy()
            self.btnNext.Enable()
            self.btnCancel.SetLabel('Skip')
            self.btnCancel.Enable()
            self.Show(False)
            self.GuiOn = False

    def OnCancel(self, event):
        if self.btnCancel.GetLabel() == 'Skip':
            self.cal1point = None
            self.btnCancel.SetLabel('Cancel')
            self.labelInfo.SetLabel("STEP2: Connect analyzer to atmosphere.")
            self.txtO2Concentration.SetValue("20.95%")
        else:
            if self.ser:
                self.ser.write("mmwr0000\r")   # Deactivate Saving to Flash Memory
                time.sleep(0.5)
            self.Show(False)
            self.GuiOn = False
            self.btnCancel.SetLabel('Skip')
    
    def MonitorLoop(self):
        lasttime = time.time()
        while True:
            while not self.ser:
                self.openPort()
                if self.ser:
                    break
                else:
                    time.sleep(5)
            try:
                wait_time = 2 - (time.time() - lasttime)
                if  wait_time <= 0:
                    self.ser.write(unicode("data\r"))
                    response = self.ser.readline()
                    lasttime = time.time()
                    valuesDat = self.calcData(response)
                    #print valuesDat
                    if valuesDat:
                        for value, header in zip(valuesDat,self.columnNames):
                            self.setTagalong(header, value)
                        if self.GuiOn:
                            self.labelPressure.SetLabel(str(valuesDat[1]))
                            self.labelTemperature.SetLabel(str(valuesDat[3]))
                            self.labelPhaseShift.SetLabel(str(valuesDat[4]))
                else:
                    time.sleep(wait_time)
            except:
                LogExc("Connection dropped!")
                self.ser.close()
                self.generateDummyData()
                self.ser = None
                time.sleep(1)
    
    def startMonitor(self):
        # make a new thread to execute monitor loop
        th = threading.Thread(target=self.MonitorLoop)
        th.setDaemon(True) # child is killed if parent dies
        th.start()

HELP_STRING = \
"""\
O2Sensor.py [--show_gui] [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h              Print this help.
-c              Specify a different config file.  Default = "O2Sensor.ini"
--show_gui      Display calibration panel
"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    shortOpts = 'c:h'
    longOpts = ["help", "show_gui"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a
    
    configFile = "O2Sensor.ini"
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        Log("Config file specified at command line", configFile)
        
    showGui = False
    if "--show_gui" in options:
        showGui = True
    
    return (configFile, showGui) 
    
if __name__ == '__main__':
    gettext.install("app")
    configFile, showGui = HandleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    O2CalDlg = O2SensorMonitor(configFile, showGui, None, wx.ID_ANY, "")
    app.SetTopWindow(O2CalDlg)
    app.MainLoop()