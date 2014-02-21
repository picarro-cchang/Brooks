APP_NAME = "Autosampler"
APP_DESCRIPTION = "CRDS Autosampler"
__version__ = 1.0
#EMULATION = True
EMULATION = False
SW_VERSION = "1.0024"
DEFAULT_CONFIG_NAME = "Autosampler.ini"
DEFAULT_STATE_CONFIG_NAME = "AutosamplerState.ini"
DEFAULT_TD_NAME = "Parameter.td"

import wx
import sys
import getopt
import os
import socket
import time
import datetime
import time
import string
import random
import _winreg as winreg
import itertools
import shutil
import serial
from numpy import *

try:
    from Host.Common import CmdFIFO
    from Host.Common.CustomConfigObj import CustomConfigObj
    from Host.Common.EventManagerProxy import *
    if not EMULATION:
        from Host.Common.SharedTypes import RPC_PORT_AUTOSAMPLER
except:
    import CmdFIFO
    from CustomConfigObj import CustomConfigObj
    from EventManagerProxy import *
    if not EMULATION:
        from SharedTypes import RPC_PORT_AUTOSAMPLER
        
from AutosamplerGUI import AutosamplerGUI
from ctypes import *
from ctypes import addressof
from ctypes import c_char, c_byte, c_float, c_int, c_longlong
from ctypes import c_short, c_uint, c_ushort, sizeof, Structure
from random import randrange
import threading
import serial


EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

LED = 0

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

NameString='Graph2'

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
            
def enumerate_serial_ports():
    """ Uses the Win32 registry to return an
        iterator of serial (COM) ports
        existing on this computer.
    """
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
    except WindowsError:
        return

    for i in itertools.count():
        try:
            val = winreg.EnumValue(key, i)
            yield str(val[1])
        except EnvironmentError:
            break

import ctypes
import re

def ValidHandle(value):
    if value == 0:
        raise ctypes.WinError()
    return value

NULL = 0
HDEVINFO = ctypes.c_int
BOOL = ctypes.c_int
CHAR = ctypes.c_char
PCTSTR = ctypes.c_char_p
HWND = ctypes.c_uint
DWORD = ctypes.c_ulong
PDWORD = ctypes.POINTER(DWORD)
ULONG = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(ULONG)
#~ PBYTE = ctypes.c_char_p
PBYTE = ctypes.c_void_p

class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte*8),
    ]
    def __str__(self):
        return "{%08x-%04x-%04x-%s-%s}" % (
            self.Data1,
            self.Data2,
            self.Data3,
            ''.join(["%02x" % d for d in self.Data4[:2]]),
            ''.join(["%02x" % d for d in self.Data4[2:]]),
        )

class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('ClassGuid', GUID),
        ('DevInst', DWORD),
        ('Reserved', ULONG_PTR),
    ]
    def __str__(self):
        return "ClassGuid:%s DevInst:%s" % (self.ClassGuid, self.DevInst)
PSP_DEVINFO_DATA = ctypes.POINTER(SP_DEVINFO_DATA)

class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('InterfaceClassGuid', GUID),
        ('Flags', DWORD),
        ('Reserved', ULONG_PTR),
    ]
    def __str__(self):
        return "InterfaceClassGuid:%s Flags:%s" % (self.InterfaceClassGuid, self.Flags)

PSP_DEVICE_INTERFACE_DATA = ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)

PSP_DEVICE_INTERFACE_DETAIL_DATA = ctypes.c_void_p

class dummy(ctypes.Structure):
    _fields_=[("d1", DWORD), ("d2", CHAR)]
    _pack_ = 1
SIZEOF_SP_DEVICE_INTERFACE_DETAIL_DATA_A = ctypes.sizeof(dummy)

SetupDiDestroyDeviceInfoList = ctypes.windll.setupapi.SetupDiDestroyDeviceInfoList
SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
SetupDiDestroyDeviceInfoList.restype = BOOL

SetupDiGetClassDevs = ctypes.windll.setupapi.SetupDiGetClassDevsA
SetupDiGetClassDevs.argtypes = [ctypes.POINTER(GUID), PCTSTR, HWND, DWORD]
SetupDiGetClassDevs.restype = ValidHandle # HDEVINFO

SetupDiEnumDeviceInterfaces = ctypes.windll.setupapi.SetupDiEnumDeviceInterfaces
SetupDiEnumDeviceInterfaces.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, ctypes.POINTER(GUID), DWORD, PSP_DEVICE_INTERFACE_DATA]
SetupDiEnumDeviceInterfaces.restype = BOOL

SetupDiGetDeviceInterfaceDetail = ctypes.windll.setupapi.SetupDiGetDeviceInterfaceDetailA
SetupDiGetDeviceInterfaceDetail.argtypes = [HDEVINFO, PSP_DEVICE_INTERFACE_DATA, PSP_DEVICE_INTERFACE_DETAIL_DATA, DWORD, PDWORD, PSP_DEVINFO_DATA]
SetupDiGetDeviceInterfaceDetail.restype = BOOL

SetupDiGetDeviceRegistryProperty = ctypes.windll.setupapi.SetupDiGetDeviceRegistryPropertyA
SetupDiGetDeviceRegistryProperty.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, DWORD, PDWORD, PBYTE, DWORD, PDWORD]
SetupDiGetDeviceRegistryProperty.restype = BOOL


GUID_CLASS_COMPORT = GUID(0x86e0d1e0L, 0x8089, 0x11d0,
    (ctypes.c_ubyte*8)(0x9c, 0xe4, 0x08, 0x00, 0x3e, 0x30, 0x1f, 0x73))

DIGCF_PRESENT = 2
DIGCF_DEVICEINTERFACE = 16
INVALID_HANDLE_VALUE = 0
ERROR_INSUFFICIENT_BUFFER = 122
SPDRP_HARDWAREID = 1
SPDRP_FRIENDLYNAME = 12
SPDRP_LOCATION_INFORMATION = 13
ERROR_NO_MORE_ITEMS = 259

def comports(available_only=True):
    """This generator scans the device registry for com ports and yields
    (order, port, desc, hwid).  If available_only is True only return currently
    existing ports. Order is a helper to get sorted lists. it can be ignored
    otherwise."""
    flags = DIGCF_DEVICEINTERFACE
    if available_only:
        flags |= DIGCF_PRESENT
    g_hdi = SetupDiGetClassDevs(ctypes.byref(GUID_CLASS_COMPORT), None, NULL, flags);
    #~ for i in range(256):
    for dwIndex in range(256):
        did = SP_DEVICE_INTERFACE_DATA()
        did.cbSize = ctypes.sizeof(did)

        if not SetupDiEnumDeviceInterfaces(
            g_hdi,
            None,
            ctypes.byref(GUID_CLASS_COMPORT),
            dwIndex,
            ctypes.byref(did)
        ):
            if ctypes.GetLastError() != ERROR_NO_MORE_ITEMS:
                raise ctypes.WinError()
            break

        dwNeeded = DWORD()
        # get the size
        if not SetupDiGetDeviceInterfaceDetail(
            g_hdi,
            ctypes.byref(did),
            None, 0, ctypes.byref(dwNeeded),
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                raise ctypes.WinError()
        # allocate buffer
        class SP_DEVICE_INTERFACE_DETAIL_DATA_A(ctypes.Structure):
            _fields_ = [
                ('cbSize', DWORD),
                ('DevicePath', CHAR*(dwNeeded.value - ctypes.sizeof(DWORD))),
            ]
            def __str__(self):
                return "DevicePath:%s" % (self.DevicePath,)
        idd = SP_DEVICE_INTERFACE_DETAIL_DATA_A()
        idd.cbSize = SIZEOF_SP_DEVICE_INTERFACE_DETAIL_DATA_A
        devinfo = SP_DEVINFO_DATA()
        devinfo.cbSize = ctypes.sizeof(devinfo)
        if not SetupDiGetDeviceInterfaceDetail(
            g_hdi,
            ctypes.byref(did),
            ctypes.byref(idd), dwNeeded, None,
            ctypes.byref(devinfo)
        ):
            raise ctypes.WinError()

        # hardware ID
        szHardwareID = ctypes.create_string_buffer(250)
        if not SetupDiGetDeviceRegistryProperty(
            g_hdi,
            ctypes.byref(devinfo),
            SPDRP_HARDWAREID,
            None,
            ctypes.byref(szHardwareID), ctypes.sizeof(szHardwareID) - 1,
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                raise ctypes.WinError()

        # friendly name
        szFriendlyName = ctypes.create_string_buffer(1024)
        if not SetupDiGetDeviceRegistryProperty(
            g_hdi,
            ctypes.byref(devinfo),
            SPDRP_FRIENDLYNAME,
            None,
            ctypes.byref(szFriendlyName), ctypes.sizeof(szFriendlyName) - 1,
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                #~ raise ctypes.WinError()
                # not getting friendly name for com0com devices, try something else
                szFriendlyName = ctypes.create_string_buffer(1024)
                if SetupDiGetDeviceRegistryProperty(
                    g_hdi,
                    ctypes.byref(devinfo),
                    SPDRP_LOCATION_INFORMATION,
                    None,
                    ctypes.byref(szFriendlyName), ctypes.sizeof(szFriendlyName) - 1,
                    None
                ):
                    port_name = "\\\\.\\" + szFriendlyName.value
                    order = None
                else:
                    port_name = szFriendlyName.value
                    order = None
        else:
            try:
                m = re.search(r"\((.*?(\d+))\)", szFriendlyName.value)
                #~ print szFriendlyName.value, m.groups()
                port_name = m.group(1)
                order = int(m.group(2))
            except AttributeError, msg:
                port_name = szFriendlyName.value
                order = None
        yield order, port_name, szFriendlyName.value, szHardwareID.value

    SetupDiDestroyDeviceInfoList(g_hdi)

class AutosamplerFrame(AutosamplerGUI):
    def __init__(self, configFile, stateFile, tdFile, *a, **k):
        self.configFile = configFile
        self.stateConfigFile = stateFile
        self.tdFile = tdFile
        AutosamplerGUI.__init__(self,*a,**k)
        self.ComPorts=[]
        for portname in enumerate_serial_ports():
            self.ComPorts.append(portname)
        self.SampleVolNumEdit.SetDigits(2)
        self.SampleVolNumEdit.SetFormat("%f")
        self.FillSpeedNumEdit.SetDigits(2)
        self.FillSpeedNumEdit.SetFormat("%f")
        self.InjSpdNumEdit.SetDigits(3)
        self.InjSpdNumEdit.SetFormat("%f")
        self.SampleWashVolNumEdit.SetDigits(2)
        self.SampleWashVolNumEdit.SetFormat("%f")
        self.PullupDlyNumEdit.SetDigits(2)
        self.PullupDlyNumEdit.SetFormat("%f")
        self.PreInjDlyNumEdit.SetDigits(2)
        self.PreInjDlyNumEdit.SetFormat("%f")
        self.PostInjDlyNumEdit.SetDigits(2)
        self.PostInjDlyNumEdit.SetFormat("%f")
        self.WasteEjectNumEdit.SetDigits(2)
        self.WasteEjectNumEdit.SetFormat("%f")
        self.RinseVolNumEdit.SetDigits(2)
        self.RinseVolNumEdit.SetFormat("%f")
        self.InjectionPointOffsetNumEdit.SetDigits(2)
        self.InjectionPointOffsetNumEdit.SetFormat("%f")
        self.stop= False
        self.assertInj= False
        self.injectionComplete= False
        self.FillSpdRinse1NumEdit.SetDigits(2)
        self.ViscosityDelayNumEdit.SetDigits(2)
        self.FillSpdRinse1NumEdit.SetFormat("%f")
        self.ViscosityDelayNumEdit.SetFormat("%f")
        self.EndBtn.Enable(False)
        self.PauseBtn.Enable(False)
        self.running=False
        self.paused=False
        self.stalledAtWait=False        
        self.jobQueue=[]
        self.jobNum=0
        self.slot1Inkwell = False
        self.slot2Inkwell = False
        self.slot3Inkwell = False
        self.slot4Inkwell = False
        self.slot5Inkwell = False
        self.slot6Inkwell = False
        self.slot7Inkwell = False
        self.slot8Inkwell = False
        self.slot9Inkwell = False
        self.slot10Inkwell = False
        
        self.slot1CB.Enable(False)
        self.slot2CB.Enable(False)
        self.slot3CB.Enable(False)
        self.slot4CB.Enable(False)
        self.slot5CB.Enable(False)
        self.slot6CB.Enable(False)
        self.slot7CB.Enable(False)
        self.slot8CB.Enable(False)
        self.slot9CB.Enable(False)
        self.slot10CB.Enable(False)

        self.HeartBeat=0
        self.jobNum=0
        self.nInj=0
        self.errCode=0
        self.method=""
        self.ActiveMethod=""        
        self.ErrorRecoveryMode=False
        
        size=[512,640]
        self.SetSize(size)
        
        self.Cfg=CustomConfigObj(self.configFile)
        self.StateCfg=CustomConfigObj(self.stateConfigFile)
        
        self.updateCfg()
        self.status=[0,0,0,0,0,0,"defaultMethod"]
        self.statusbar.SetFieldsCount(5)
        self.statusbar.SetStatusWidths([-6,-1,-1,-1,-1])
        self.lib = windll.LoadLibrary('ALSG_API.dll')
        self.ASConnect()

        self.LoadMethodChoice.SetStringSelection(self.StateCfg["MethodChoice"])
        self.OnLoadMethodChoice(wx.EVT_CHOICE)
        self.ASReadInit()
        time.sleep(0.35)
        self.syringeSize=self.ASGetConfigSyringeVol()        
        self.SampleWashVolNumEdit._max =self.SampleVolNumEdit._max = self.syringeSize
        self.updateQueue()

        self.tray = 0
        self.v=1
        self.running=False
        self.exchangePosition=False
        self.lastStatus=''
        self.numInjDone=0
        self.pausedAndInjStarted=False
        self.timer.Start(250)
        self.RinseBetweenVialsCB
        self.lastVial=0
        self.abortInProgress = False
        try:            
            self.SetIcon(wx.Icon("cogwheel.ico", wx.BITMAP_TYPE_ICO))
        finally:
            pass  # - don't sweat it if it doesn't load
        
        self.startServer()

    def updateQueue(self):
        print self.StateCfg["Slot1Choice"]
        self.Slot1Choice.SetStringSelection(self.StateCfg["Slot1Choice"])
        self.slot1Inkwell = (bool(self.StateCfg["slot1Inkwell"]=="True")) 
        self.setInkwell1_UIState()
        self.Slot1TrayNumEdit.SetValue(int(self.StateCfg["slot1Tray"]))
        self.Slot1EndVialNumEdit.SetValue(int(self.StateCfg["Slot1EndVialNumEdit"]))
        self.Slot1InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot1InjPerVialNumEdit"]))
        self.Slot1StartVialNumEdit.SetValue(float(self.StateCfg["Slot1StartVialNumEdit"]))
        self.ChgSyringeBtn.Enable(True)
        if self.Slot1Choice.GetStringSelection()!="":
            self.slot1CB.Enable()
            self.slot1CB.SetValue(bool(self.StateCfg["slot1CB"]=="True"))

        print self.StateCfg["Slot2Choice"]
        self.slot2Inkwell = (bool(self.StateCfg["slot2Inkwell"]=="True")) 
        self.setInkwell2_UIState()
        self.Slot2Choice.SetStringSelection(self.StateCfg["Slot2Choice"])
        self.Slot2TrayNumEdit.SetValue(int(self.StateCfg["slot2Tray"]))
        self.Slot2EndVialNumEdit.SetValue(int(self.StateCfg["Slot2EndVialNumEdit"]))
        self.Slot2InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot2InjPerVialNumEdit"]))
        self.Slot2StartVialNumEdit.SetValue(float(self.StateCfg["Slot2StartVialNumEdit"]))
        if self.Slot2Choice.GetStringSelection()!="":
            self.slot2CB.Enable()
            self.slot2CB.SetValue(bool(self.StateCfg["slot2CB"]=="True"))

        print self.StateCfg["Slot3Choice"]
        self.slot3Inkwell = (bool(self.StateCfg["slot3Inkwell"]=="True")) 
        self.setInkwell3_UIState()
        self.Slot3Choice.SetStringSelection(self.StateCfg["Slot3Choice"])
        self.Slot3TrayNumEdit.SetValue(int(self.StateCfg["slot3Tray"]))
        self.Slot3EndVialNumEdit.SetValue(int(self.StateCfg["Slot3EndVialNumEdit"]))
        self.Slot3InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot3InjPerVialNumEdit"]))
        self.Slot3StartVialNumEdit.SetValue(float(self.StateCfg["Slot3StartVialNumEdit"]))
        if self.Slot3Choice.GetStringSelection()!="":
            self.slot3CB.Enable()
            self.slot3CB.SetValue(bool(self.StateCfg["slot3CB"]=="True"))

        print self.StateCfg["Slot4Choice"]
        self.slot4Inkwell = (bool(self.StateCfg["slot4Inkwell"]=="True")) 
        self.setInkwell4_UIState()
        self.Slot4Choice.SetStringSelection(self.StateCfg["Slot4Choice"])
        self.Slot4TrayNumEdit.SetValue(int(self.StateCfg["slot4Tray"]))
        self.Slot4EndVialNumEdit.SetValue(int(self.StateCfg["Slot4EndVialNumEdit"]))
        self.Slot4InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot4InjPerVialNumEdit"]))
        self.Slot4StartVialNumEdit.SetValue(float(self.StateCfg["Slot4StartVialNumEdit"]))
        if self.Slot4Choice.GetStringSelection()!="":
            self.slot4CB.Enable()
            self.slot4CB.SetValue(bool(self.StateCfg["slot4CB"]=="True"))

        print self.StateCfg["Slot5Choice"]
        self.slot5Inkwell = (bool(self.StateCfg["slot5Inkwell"]=="True")) 
        self.setInkwell5_UIState()
        self.Slot5Choice.SetStringSelection(self.StateCfg["Slot5Choice"])
        self.Slot5TrayNumEdit.SetValue(int(self.StateCfg["slot5Tray"]))
        self.Slot5EndVialNumEdit.SetValue(int(self.StateCfg["Slot5EndVialNumEdit"]))
        self.Slot5InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot5InjPerVialNumEdit"]))
        self.Slot5StartVialNumEdit.SetValue(float(self.StateCfg["Slot5StartVialNumEdit"]))
        if self.Slot5Choice.GetStringSelection()!="":
            self.slot5CB.Enable()
            self.slot5CB.SetValue(bool(self.StateCfg["slot5CB"]=="True"))

        print self.StateCfg["Slot6Choice"]
        self.slot6Inkwell = (bool(self.StateCfg["slot6Inkwell"]=="True")) 
        self.setInkwell6_UIState()
        self.Slot6Choice.SetStringSelection(self.StateCfg["Slot6Choice"])
        self.Slot6TrayNumEdit.SetValue(int(self.StateCfg["slot6Tray"]))
        self.Slot6EndVialNumEdit.SetValue(int(self.StateCfg["Slot6EndVialNumEdit"]))
        self.Slot6InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot6InjPerVialNumEdit"]))
        self.Slot6StartVialNumEdit.SetValue(float(self.StateCfg["Slot6StartVialNumEdit"]))
        if self.Slot6Choice.GetStringSelection()!="":
            self.slot6CB.Enable()
            self.slot6CB.SetValue(bool(self.StateCfg["slot6CB"]=="True"))

        print self.StateCfg["Slot7Choice"]
        self.slot7Inkwell = (bool(self.StateCfg["slot7Inkwell"]=="True")) 
        self.setInkwell7_UIState()
        self.Slot7Choice.SetStringSelection(self.StateCfg["Slot7Choice"])
        self.Slot7TrayNumEdit.SetValue(int(self.StateCfg["slot7Tray"]))
        self.Slot7EndVialNumEdit.SetValue(int(self.StateCfg["Slot7EndVialNumEdit"]))
        self.Slot7InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot7InjPerVialNumEdit"]))
        self.Slot7StartVialNumEdit.SetValue(float(self.StateCfg["Slot7StartVialNumEdit"]))
        if self.Slot7Choice.GetStringSelection()!="":
            self.slot7CB.Enable()
            self.slot7CB.SetValue(bool(self.StateCfg["slot7CB"]=="True"))

        print self.StateCfg["Slot8Choice"]
        self.slot8Inkwell = (bool(self.StateCfg["slot8Inkwell"]=="True")) 
        self.setInkwell8_UIState()
        self.Slot8Choice.SetStringSelection(self.StateCfg["Slot8Choice"])
        self.Slot8TrayNumEdit.SetValue(int(self.StateCfg["slot8Tray"]))
        self.Slot8EndVialNumEdit.SetValue(int(self.StateCfg["Slot8EndVialNumEdit"]))
        self.Slot8InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot8InjPerVialNumEdit"]))
        self.Slot8StartVialNumEdit.SetValue(float(self.StateCfg["Slot8StartVialNumEdit"]))
        if self.Slot8Choice.GetStringSelection()!="":
            self.slot8CB.Enable()
            self.slot8CB.SetValue(bool(self.StateCfg["slot8CB"]=="True"))

        print self.StateCfg["Slot9Choice"]
        self.slot9Inkwell = (bool(self.StateCfg["slot9Inkwell"]=="True")) 
        self.setInkwell9_UIState()
        self.Slot9Choice.SetStringSelection(self.StateCfg["Slot9Choice"])
        self.Slot9TrayNumEdit.SetValue(int(self.StateCfg["slot9Tray"]))
        self.Slot9EndVialNumEdit.SetValue(int(self.StateCfg["Slot9EndVialNumEdit"]))
        self.Slot9InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot9InjPerVialNumEdit"]))
        self.Slot9StartVialNumEdit.SetValue(float(self.StateCfg["Slot9StartVialNumEdit"]))
        if self.Slot9Choice.GetStringSelection()!="":
            self.slot9CB.Enable()
            self.slot9CB.SetValue(bool(self.StateCfg["slot9CB"]=="True"))

        print self.StateCfg["Slot10Choice"]
        self.slot10Inkwell = (bool(self.StateCfg["slot10Inkwell"]=="True")) 
        self.setInkwell10_UIState()
        self.Slot10Choice.SetStringSelection(self.StateCfg["Slot10Choice"])
        self.Slot10TrayNumEdit.SetValue(int(self.StateCfg["slot10Tray"]))
        self.Slot10EndVialNumEdit.SetValue(int(self.StateCfg["Slot10EndVialNumEdit"]))
        self.Slot10InjPerVialNumEdit.SetValue(int(self.StateCfg["Slot10InjPerVialNumEdit"]))
        self.Slot10StartVialNumEdit.SetValue(float(self.StateCfg["Slot10StartVialNumEdit"]))
        if self.Slot10Choice.GetStringSelection()!="":
            self.slot10CB.Enable()
            self.slot10CB.SetValue(bool(self.StateCfg["slot10CB"]=="True"))

    def startServer(self):
        if not EMULATION:
            self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_AUTOSAMPLER),
                                                    ServerName = APP_NAME,
                                                    ServerDescription = APP_DESCRIPTION,
                                                    ServerVersion = __version__,
                                                    threaded = True)  
            self.rpcServer.register_function(self.assertStart)
            self.rpcServer.register_function(self.deassertStart)
            self.rpcServer.register_function(self.assertInject)
            self.rpcServer.register_function(self.deassertInject)
            self.rpcServer.register_function(self.getLog)
            self.rpcServer.register_function(self.getInjected)
            self.rpcThread = RpcServerThread(self.rpcServer, self.Destroy)
            self.rpcThread.start()

    def assertStart(self):
        #self.OnRunBtn(None)
        pass

    def deassertStart(self):
        self.OnStopBtn(None)

    def assertInject(self):
        if(self.assertInj==False):
            self.assertInj=True
            self.injectionComplete=False

    def deassertInject(self):
        if(self.assertInj==True):
            self.assertInj=False
            self.injectionComplete=False

    def getLog(self):
        # Need to implement:
        # This is hardcoded to tray 1, need to add support for 2 trays if we ever get that working in hardware
        timeString = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        return (timeString, 1, self.v, self.jobNum, self.method, self.errCode)

    def getInjected(self):
        return self.injectionComplete
    
    def updateCfg(self):
        choices=self.Cfg.keys()
        choices.sort()
        self.LoadMethodChoice.Clear()
        saved1=self.Slot1Choice.GetStringSelection()
        saved2=self.Slot2Choice.GetStringSelection()
        saved3=self.Slot3Choice.GetStringSelection()
        saved4=self.Slot4Choice.GetStringSelection()
        saved5=self.Slot5Choice.GetStringSelection()
        saved6=self.Slot6Choice.GetStringSelection()
        saved7=self.Slot7Choice.GetStringSelection()
        saved8=self.Slot8Choice.GetStringSelection()
        saved9=self.Slot9Choice.GetStringSelection()
        saved10=self.Slot10Choice.GetStringSelection()
        self.Slot1Choice.Clear()
        self.Slot2Choice.Clear()
        self.Slot3Choice.Clear()
        self.Slot4Choice.Clear()
        self.Slot5Choice.Clear()
        self.Slot6Choice.Clear()
        self.Slot7Choice.Clear()
        self.Slot8Choice.Clear()
        self.Slot9Choice.Clear()
        self.Slot10Choice.Clear()
        for k in choices:
            self.LoadMethodChoice.Append(k)
            self.Slot1Choice.Append(k)
            self.Slot2Choice.Append(k)
            self.Slot3Choice.Append(k)
            self.Slot4Choice.Append(k)
            self.Slot5Choice.Append(k)
            self.Slot6Choice.Append(k)
            self.Slot7Choice.Append(k)
            self.Slot8Choice.Append(k)
            self.Slot9Choice.Append(k)
            self.Slot10Choice.Append(k)
        lst=self.Slot1Choice.GetItems()
        if not(saved1 in lst):
            self.slot1CB.Value = False
            self.slot1CB.Enable(False)
        else: 
            self.Slot1Choice.SetStringSelection(saved1)

        if not(saved2 in lst):
            self.slot2CB.Value = False
            self.slot2CB.Enable(False)
        else: 
            self.Slot2Choice.SetStringSelection(saved2)
        
        if not(saved3 in lst):
            self.slot3CB.Value = False
            self.slot3CB.Enable(False)
        else: 
            self.Slot3Choice.SetStringSelection(saved3)
        
        if not(saved4 in lst):
            self.slot4CB.Value = False
            self.slot4CB.Enable(False)
        else: 
            self.Slot4Choice.SetStringSelection(saved4)

        if not(saved5 in lst):
            self.slot5CB.Value = False
            self.slot5CB.Enable(False)
        else: 
            self.Slot5Choice.SetStringSelection(saved5)

        if not(saved6 in lst):
            self.slot6CB.Value = False
            self.slot6CB.Enable(False)
        else: 
            self.Slot6Choice.SetStringSelection(saved6)

        if not(saved7 in lst):
            self.slot7CB.Value = False
            self.slot7CB.Enable(False)
        else: 
            self.Slot7Choice.SetStringSelection(saved7)

        if not(saved8 in lst):
            self.slot8CB.Value = False
            self.slot8CB.Enable(False)
        else: 
            self.Slot8Choice.SetStringSelection(saved8)

        if not(saved9 in lst):
            self.slot9CB.Value = False
            self.slot9CB.Enable(False)
        else: 
            self.Slot9Choice.SetStringSelection(saved9)

        if not(saved10 in lst):
            self.slot10CB.Value = False
            self.slot10CB.Enable(False)
        else: 
            self.Slot10Choice.SetStringSelection(saved10)
    
    def MsgBox(self,msg,title):
        dlg=wx.TextEntryDialog(None,msg,title)
        rtnVal=""
        if dlg.ShowModal()==wx.ID_OK:
            rtnVal=dlg.GetValue()
        dlg.Destroy()
        return rtnVal

    def update(self):
        pass

    def Log(self, s):
        self.LogTextCtrl.Value+= s
        self.statusbar.SetStatusText("%s"%s)
        print s
        
    def datetimeToTimestamp(self,t):
        ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
        td = t - ORIGIN
        return (td.days*86400 + td.seconds)*1000 + td.microseconds//1000
    
    def getTimestamp(self):
        return self.datetimeToTimestamp(datetime.datetime.utcnow())

    def logFilter(self,text):
        ignore="Running without Sample Manager - always returns stable status"
        tf = text.find(ignore)
        if tf<0:
            self.EventLog.AppendText(text+'\n')
            self.eventCount+=1
            if self.eventCount>100:
                self.EventLog.Clear()
                self.eventCount=0

    def OnCloseWindow(self, event): 
        print "In Event handler `OnCloseWindow'"
        self.outputQueue()
        event.Skip()
    
    def outputQueue(self):
        self.StateCfg["MethodChoice"]= self.LoadMethodChoice.GetStringSelection()

        self.StateCfg["slot1CB"]=self.slot1CB.GetValue()
        self.StateCfg["Slot1Choice"]=self.Slot1Choice.GetStringSelection()
        self.StateCfg["slot1Inkwell"]=self.slot1Inkwell
        self.StateCfg["slot1Tray"]=self.Slot1TrayNumEdit.GetValue()
        self.StateCfg["Slot1StartVialNumEdit"]=self.Slot1StartVialNumEdit.GetValue()
        self.StateCfg["Slot1EndVialNumEdit"]=self.Slot1EndVialNumEdit.GetValue()
        self.StateCfg["Slot1InjPerVialNumEdit"]=self.Slot1InjPerVialNumEdit.GetValue()

        self.StateCfg["slot2CB"]=self.slot2CB.GetValue()
        self.StateCfg["Slot2Choice"]=self.Slot2Choice.GetStringSelection()
        self.StateCfg["slot2Inkwell"]=self.slot2Inkwell
        self.StateCfg["slot2Tray"]=self.Slot2TrayNumEdit.GetValue()
        self.StateCfg["Slot2StartVialNumEdit"]=self.Slot2StartVialNumEdit.GetValue()
        self.StateCfg["Slot2EndVialNumEdit"]=self.Slot2EndVialNumEdit.GetValue()
        self.StateCfg["Slot2InjPerVialNumEdit"]=self.Slot2InjPerVialNumEdit.GetValue()

        self.StateCfg["slot3CB"]=self.slot3CB.GetValue()
        self.StateCfg["Slot3Choice"]=self.Slot3Choice.GetStringSelection()
        self.StateCfg["slot3Inkwell"]=self.slot3Inkwell
        self.StateCfg["slot3Tray"]=self.Slot3TrayNumEdit.GetValue()
        self.StateCfg["Slot3EndVialNumEdit"]=self.Slot3EndVialNumEdit.GetValue()
        self.StateCfg["Slot3StartVialNumEdit"]=self.Slot3StartVialNumEdit.GetValue()
        self.StateCfg["Slot3InjPerVialNumEdit"]=self.Slot3InjPerVialNumEdit.GetValue()

        self.StateCfg["slot4CB"]=self.slot4CB.GetValue()
        self.StateCfg["Slot4Choice"]=self.Slot4Choice.GetStringSelection()
        self.StateCfg["slot4Inkwell"]=self.slot4Inkwell
        self.StateCfg["slot4Tray"]=self.Slot4TrayNumEdit.GetValue()
        self.StateCfg["Slot4StartVialNumEdit"]=self.Slot4StartVialNumEdit.GetValue()
        self.StateCfg["Slot4EndVialNumEdit"]=self.Slot4EndVialNumEdit.GetValue()
        self.StateCfg["Slot4InjPerVialNumEdit"]=self.Slot4InjPerVialNumEdit.GetValue()

        self.StateCfg["slot5CB"]=self.slot5CB.GetValue()
        self.StateCfg["Slot5Choice"]=self.Slot5Choice.GetStringSelection()
        self.StateCfg["slot5Inkwell"]=self.slot5Inkwell
        self.StateCfg["slot5Tray"]=self.Slot5TrayNumEdit.GetValue()
        self.StateCfg["Slot5StartVialNumEdit"]=self.Slot5StartVialNumEdit.GetValue()
        self.StateCfg["Slot5EndVialNumEdit"]=self.Slot5EndVialNumEdit.GetValue()
        self.StateCfg["Slot5InjPerVialNumEdit"]=self.Slot5InjPerVialNumEdit.GetValue()

        self.StateCfg["slot6CB"]=self.slot6CB.GetValue()
        self.StateCfg["Slot6Choice"]=self.Slot6Choice.GetStringSelection()
        self.StateCfg["slot6Inkwell"]=self.slot6Inkwell
        self.StateCfg["slot6Tray"]=self.Slot6TrayNumEdit.GetValue()
        self.StateCfg["Slot6StartVialNumEdit"]=self.Slot6StartVialNumEdit.GetValue()
        self.StateCfg["Slot6EndVialNumEdit"]=self.Slot6EndVialNumEdit.GetValue()
        self.StateCfg["Slot6InjPerVialNumEdit"]=self.Slot6InjPerVialNumEdit.GetValue()

        self.StateCfg["slot7CB"]=self.slot7CB.GetValue()
        self.StateCfg["Slot7Choice"]=self.Slot7Choice.GetStringSelection()
        self.StateCfg["slot7Inkwell"]=self.slot7Inkwell
        self.StateCfg["slot7Tray"]=self.Slot7TrayNumEdit.GetValue()
        self.StateCfg["Slot7StartVialNumEdit"]=self.Slot7StartVialNumEdit.GetValue()
        self.StateCfg["Slot7EndVialNumEdit"]=self.Slot7EndVialNumEdit.GetValue()
        self.StateCfg["Slot7InjPerVialNumEdit"]=self.Slot7InjPerVialNumEdit.GetValue()

        self.StateCfg["slot8CB"]=self.slot8CB.GetValue()
        self.StateCfg["Slot8Choice"]=self.Slot8Choice.GetStringSelection()
        self.StateCfg["slot8Inkwell"]=self.slot8Inkwell
        self.StateCfg["slot8Tray"]=self.Slot8TrayNumEdit.GetValue()
        self.StateCfg["Slot8StartVialNumEdit"]=self.Slot8StartVialNumEdit.GetValue()
        self.StateCfg["Slot8EndVialNumEdit"]=self.Slot8EndVialNumEdit.GetValue()
        self.StateCfg["Slot8InjPerVialNumEdit"]=self.Slot8InjPerVialNumEdit.GetValue()

        self.StateCfg["slot9CB"]=self.slot9CB.GetValue()
        self.StateCfg["Slot9Choice"]=self.Slot9Choice.GetStringSelection()
        self.StateCfg["slot9Inkwell"]=self.slot9Inkwell
        self.StateCfg["slot9Tray"]=self.Slot9TrayNumEdit.GetValue()
        self.StateCfg["Slot9StartVialNumEdit"]=self.Slot9StartVialNumEdit.GetValue()
        self.StateCfg["Slot9EndVialNumEdit"]=self.Slot9EndVialNumEdit.GetValue()
        self.StateCfg["Slot9InjPerVialNumEdit"]=self.Slot9InjPerVialNumEdit.GetValue()

        self.StateCfg["slot10CB"]=self.slot10CB.GetValue()
        self.StateCfg["Slot10Choice"]=self.Slot10Choice.GetStringSelection()
        self.StateCfg["slot10Inkwell"]=self.slot10Inkwell
        self.StateCfg["slot10Tray"]=self.Slot10TrayNumEdit.GetValue()
        self.StateCfg["Slot10StartVialNumEdit"]=self.Slot10StartVialNumEdit.GetValue()
        self.StateCfg["Slot10EndVialNumEdit"]=self.Slot10EndVialNumEdit.GetValue()
        self.StateCfg["Slot10InjPerVialNumEdit"]=self.Slot10InjPerVialNumEdit.GetValue()

        self.StateCfg.write()
        self.updateCfg()
    
    def OnRunBtn(self, event): 
        self.Log("Run\r\n")
        if not self.RunBtn.Enabled:
            return
        if(not self.slot1CB.GetValue() and not self.slot2CB.GetValue()
           and not self.slot3CB.GetValue() and not self.slot4CB.GetValue()           
           and not self.slot5CB.GetValue() and not self.slot6CB.GetValue()           
           and not self.slot7CB.GetValue() and not self.slot8CB.GetValue()           
           and not self.slot9CB.GetValue() and not self.slot10CB.GetValue()           
            ):
            return

        if(self.slot1CB.GetValue()):
            jobName=self.Slot1Choice.GetStringSelection()
            start=self.Slot1StartVialNumEdit.GetValue()
            end=self.Slot1EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot1InjPerVialNumEdit.GetValue()
            tray = self.Slot1TrayNumEdit.GetValue() - 1
            if self.slot1Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot2CB.GetValue()):
            jobName=self.Slot2Choice.GetStringSelection()
            start=self.Slot2StartVialNumEdit.GetValue()
            end=self.Slot2EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot2InjPerVialNumEdit.GetValue()
            tray = self.Slot2TrayNumEdit.GetValue() - 1
            if self.slot2Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot3CB.GetValue()):
            jobName=self.Slot3Choice.GetStringSelection()
            start=self.Slot3StartVialNumEdit.GetValue()
            end=self.Slot3EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot3InjPerVialNumEdit.GetValue()
            tray = self.Slot3TrayNumEdit.GetValue() - 1
            if self.slot3Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot4CB.GetValue()):
            jobName=self.Slot4Choice.GetStringSelection()
            start=self.Slot4StartVialNumEdit.GetValue()
            end=self.Slot4EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot4InjPerVialNumEdit.GetValue()
            tray = self.Slot4TrayNumEdit.GetValue() - 1
            if self.slot4Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot5CB.GetValue()):
            jobName=self.Slot5Choice.GetStringSelection()
            start=self.Slot5StartVialNumEdit.GetValue()
            end=self.Slot5EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot5InjPerVialNumEdit.GetValue()
            tray = self.Slot5TrayNumEdit.GetValue() - 1
            if self.slot5Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot6CB.GetValue()):
            jobName=self.Slot6Choice.GetStringSelection()
            start=self.Slot6StartVialNumEdit.GetValue()
            end=self.Slot6EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot6InjPerVialNumEdit.GetValue()
            tray = self.Slot6TrayNumEdit.GetValue() - 1
            if self.slot6Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot7CB.GetValue()):
            jobName=self.Slot7Choice.GetStringSelection()
            start=self.Slot7StartVialNumEdit.GetValue()
            end=self.Slot7EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot7InjPerVialNumEdit.GetValue()
            tray = self.Slot7TrayNumEdit.GetValue() - 1
            if self.slot7Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot8CB.GetValue()):
            jobName=self.Slot8Choice.GetStringSelection()
            start=self.Slot8StartVialNumEdit.GetValue()
            end=self.Slot8EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot8InjPerVialNumEdit.GetValue()
            tray = self.Slot8TrayNumEdit.GetValue() - 1
            if self.slot8Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot9CB.GetValue()):
            jobName=self.Slot9Choice.GetStringSelection()
            start=self.Slot9StartVialNumEdit.GetValue()
            end=self.Slot9EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot9InjPerVialNumEdit.GetValue()
            tray = self.Slot9TrayNumEdit.GetValue() - 1
            if self.slot9Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if(self.slot10CB.GetValue()):
            jobName=self.Slot10Choice.GetStringSelection()
            start=self.Slot10StartVialNumEdit.GetValue()
            end=self.Slot10EndVialNumEdit.GetValue()
            VialsToDo=1+end-start
            inj= self.Slot10InjPerVialNumEdit.GetValue()
            tray = self.Slot10TrayNumEdit.GetValue() - 1
            if self.slot10Inkwell:
                job= {'JobName':jobName,'startVial':1,'endVial':1,'numInj':inj, 'Tray':-100}
            else:
                job= {'JobName':jobName,'startVial':start,'endVial':end,'numInj':inj, 'Tray':tray}
            if VialsToDo>=1:
                self.jobQueue.append(job)
        if len(self.jobQueue) > 0:
            self.jobNum=1 
            j = self.jobQueue[0]  #This is the first one
            self.tray = int(j["Tray"])
            self.method=(j["JobName"])
            self.Log("Starting job number %s with method %s\r\n"%(self.jobNum, self.method))
            self.nInj=int(j["numInj"])
            self.startVial=int(j["startVial"])
            self.endVial=int(j["endVial"])
            self.v=self.startVial
            self.EnableQueueUIElements(False)
            self.EndBtn.Enable(True)
            self.RunBtn.Enable(False)
            self.ChgSyringeBtn.Enable(False)
            self.LoadQueueBtn.Enable(False)
            self.SaveQueueBtn.Enable(False)        
            self.stop=False
            self.running=True
            self.paused=False
            self.numInjDone=0
            try:
                self.jobQueue.pop(0)
            except:
                pass
            self.running=True

    def ClearQueue(self):
        self.OnClearSlot1Btn(None)
        self.OnClearSlot2Btn(None)
        self.OnClearSlot3Btn(None)
        self.OnClearSlot4Btn(None)
        self.OnClearSlot5Btn(None)
        self.OnClearSlot6Btn(None)
        self.OnClearSlot7Btn(None)
        self.OnClearSlot8Btn(None)
        self.OnClearSlot9Btn(None)
        self.OnClearSlot10Btn(None)

    def OnLoadQueueBtn(self, event):
        print "In Event handler `OnLoadQueueBtn'"
        self.ClearQueue()
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.Que", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            # Change the GUI state
            loadedStateConfigFile = dirname + "/" + filename
            self.StateCfg=CustomConfigObj(loadedStateConfigFile)
            self.updateCfg()
            self.updateQueue()
            # Revert back to original state
            self.StateCfg=CustomConfigObj(self.stateConfigFile)
        dlg.Destroy()

    def OnSaveQueueBtn(self, event): 
        print "In Event handler `OnSaveQueueBtn'"
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.Que", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            targetStateConfigFile = dirname + "/" + filename
            self.outputQueue()
            shutil.copy2(self.stateConfigFile, targetStateConfigFile)
        dlg.Destroy()

    def EnableQueueUIElements(self, tf):
        self.ClrSlot1Btn.Enable(tf)
        self.slot1CB.Enable(tf)
        self.Slot1Choice.Enable(tf)
        self.Slot1TrayNumEdit.Enable(tf)        
        self.Slot1StartVialNumEdit.Enable(tf)
        self.Slot1EndVialNumEdit.Enable(tf)
        self.Slot1InjPerVialNumEdit.Enable(tf)

        self.ClrSlot2Btn.Enable(tf)
        self.slot2CB.Enable(tf)
        self.Slot2Choice.Enable(tf)
        self.Slot2TrayNumEdit.Enable(tf)        
        self.Slot2StartVialNumEdit.Enable(tf)
        self.Slot2EndVialNumEdit.Enable(tf)
        self.Slot2InjPerVialNumEdit.Enable(tf)

        self.ClrSlot3Btn.Enable(tf)
        self.slot3CB.Enable(tf)
        self.Slot3Choice.Enable(tf)
        self.Slot3TrayNumEdit.Enable(tf)        
        self.Slot3StartVialNumEdit.Enable(tf)
        self.Slot3EndVialNumEdit.Enable(tf)
        self.Slot3InjPerVialNumEdit.Enable(tf)

        self.ClrSlot4Btn.Enable(tf)
        self.slot4CB.Enable(tf)
        self.Slot4Choice.Enable(tf)
        self.Slot4TrayNumEdit.Enable(tf)        
        self.Slot4StartVialNumEdit.Enable(tf)
        self.Slot4EndVialNumEdit.Enable(tf)
        self.Slot4InjPerVialNumEdit.Enable(tf)

        self.ClrSlot5Btn.Enable(tf)
        self.slot5CB.Enable(tf)
        self.Slot5Choice.Enable(tf)
        self.Slot5TrayNumEdit.Enable(tf)        
        self.Slot5StartVialNumEdit.Enable(tf)
        self.Slot5EndVialNumEdit.Enable(tf)
        self.Slot5InjPerVialNumEdit.Enable(tf)

        self.ClrSlot6Btn.Enable(tf)
        self.slot6CB.Enable(tf)
        self.Slot6Choice.Enable(tf)
        self.Slot6TrayNumEdit.Enable(tf)        
        self.Slot6StartVialNumEdit.Enable(tf)
        self.Slot6EndVialNumEdit.Enable(tf)
        self.Slot6InjPerVialNumEdit.Enable(tf)

        self.ClrSlot7Btn.Enable(tf)
        self.slot7CB.Enable(tf)
        self.Slot7Choice.Enable(tf)
        self.Slot7TrayNumEdit.Enable(tf)        
        self.Slot7StartVialNumEdit.Enable(tf)
        self.Slot7EndVialNumEdit.Enable(tf)
        self.Slot7InjPerVialNumEdit.Enable(tf)

        self.ClrSlot8Btn.Enable(tf)
        self.slot8CB.Enable(tf)
        self.Slot8Choice.Enable(tf)
        self.Slot8TrayNumEdit.Enable(tf)        
        self.Slot8StartVialNumEdit.Enable(tf)
        self.Slot8EndVialNumEdit.Enable(tf)
        self.Slot8InjPerVialNumEdit.Enable(tf)

        self.ClrSlot9Btn.Enable(tf)
        self.slot9CB.Enable(tf)
        self.Slot9Choice.Enable(tf)
        self.Slot9TrayNumEdit.Enable(tf)        
        self.Slot9StartVialNumEdit.Enable(tf)
        self.Slot9EndVialNumEdit.Enable(tf)
        self.Slot9InjPerVialNumEdit.Enable(tf)

        self.ClrSlot10Btn.Enable(tf)
        self.slot10CB.Enable(tf)
        self.Slot10Choice.Enable(tf)
        self.Slot10TrayNumEdit.Enable(tf)        
        self.Slot10StartVialNumEdit.Enable(tf)
        self.Slot10EndVialNumEdit.Enable(tf)
        self.Slot10InjPerVialNumEdit.Enable(tf)

    def OnChgSyringeBtn(self, event):
        if (self.ASGetBusy() or not self.ASGetIdle()):
            s=self.ASGetStatus()
            if (s!="No Error\r\n" and s!="Abort\r\n" and s!="Move to Wait Position\r\n"):
                return 
        if not self.exchangePosition:
            self.exchangePosition=True
            self.RunWasEnabled = self.RunBtn.Enabled
            self.HaltWasEnabled = self.EndBtn.Enabled
            self.StopWasEnabled = self.StopBtn.Enabled
            self.RunBtn.Enable(False)
            self.ChgSyringeBtn.SetLabel("Swap Done")
            self.Log("Chg Syringe\r\n")
            self.ASReadInit()
            self.ASStepGoToSyrExchange(0)
            time.sleep(1)
            self.ASStepGoToSyrExchange(1)
            time.sleep(1)
        else:
            self.exchangePosition=False
            self.ChgSyringeBtn.SetLabel("Chg Syringe")
            self.Log("Go To Wait\r\n")
            self.ASStepGoToSyrExchange(2)
            time.sleep(1)
            self.ASStepGoToSyrExchange(3)
            time.sleep(1)
            self.ASReadInit()
            self.ASStepGoToWait()
            time.sleep(1)
            self.RunBtn.Enable(self.RunWasEnabled)
            self.StopBtn.Enable(self.StopWasEnabled)
            self.EndBtn.Enable(self.HaltWasEnabled)
            
    def ASWaitIdle(self):
        count=0.0
        maxWait=2.0
        bsy = self.ASGetBusy()
        if not bsy:
            return
        while bsy and count<maxWait:
            time.sleep(0.1)
            bsy = self.ASGetBusy()
            count+=0.1


    def ASConnect(self):
        ASComNum=0
        import serial
        print "-"*78
        print "Serial ports"
        print "-"*78
        for order, port, desc, hwid in sorted(comports()):
            print "%-10s: %s (%s) ->\n" % (port, desc, hwid)
            if hwid.find("FTDIBUS\COMPORT&VID_0403&PID_6001") >=0: 
                ASComNum=(int)(port[3:])
        
        rtn=self.lib.alsgConnect(ASComNum)
        if(rtn==ASComNum):
            self.Log("Autosampler Connected\r\n")
            return True
        else:
            self.Log("ASConnect Failed\r\n")
            self.Log("Port=%s, Error =%s\r\n"%(ASComNum,self.ASGetError()))
        return

    def ASDisconnect(self):
        self.ASWaitIdle()
        rtn=self.lib.alsgDisConnect()
        if(rtn==1):
            self.Log("Autosampler Disconnected\r\n")
            return True
        else:
            self.Log("ASDisConnect Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASReadInit(self):
        fn = os.path.abspath(self.tdFile)
        self.ASWaitIdle()
        rtn=self.lib.alsgReadInit(c_char_p(fn))
        if(rtn==1):
            self.Log("ASReadInit successful\r\n")
            return True
        else:
            self.Log("ASReadInit Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallTraySampleDepth(self, nTray, dzDepth):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallTraySampleDepth(c_short(nTray), c_double(dzDepth))
        if(rtn==1):
            self.Log("ASSetInstallTraySampleDepth successful\r\n")
            return True
        else:
            self.Log("ASSetInstallTraySampleDepth Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallTrayPos(self, nTray, dxPos, dyPos, dzPos):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallTrayPos(c_short(nTray), c_double(dxPos), c_double(dyPos), c_double(dzPos))
        if(rtn==1):
            self.Log("ASSetInstallTrayPos successful\r\n")
            return True
        else:
            self.Log("ASSetInstallTrayPos Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallWashStationPos(self, dxPos, dyPos):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallWashStationPos(c_double(dxPos), c_double(dyPos))
        if(rtn==1):
            self.Log("ASSetInstallWashStationPos successful\r\n")
            return True
        else:
            self.Log("ASSetInstallWashStationPos Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallWashStationSolventDepth(self, dzDepth):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallWashStationSolventDepth(c_double(dzDepth))
        if(rtn==1):
            self.Log("ASSetInstallWashStationSolventDepth successful\r\n")
            return True
        else:
            self.Log("ASSetInstallWashStationSolventDepth Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallWashStationWasteDepth(self, dzDepth):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallWashStationWasteDepth(c_double(dzDepth))
        if(rtn==1):
            self.Log("ASSetInstallWashStationWasteDepth successful\r\n")
            return True
        else:
            self.Log("ASSetInstallWashStationWasteDepth Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallWashStationISTDDepth(self, dzDepth):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallWashStationISTDDepth(c_double(dzDepth))
        if(rtn==1):
            self.Log("ASSetInstallWashStationISTDDepth successful\r\n")
            return True
        else:
            self.Log("ASSetInstallWashStationISTDDepth Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetInstallMotorSpeed(self, dxSpd, dySpd):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallMotorSpeed(c_short(dxSpd), c_short(dySpd))
        if(rtn==1):
            self.Log("ASSetInstallMotorSpeed successful\r\n")
            return True
        else:
            self.Log("ASSetInstallMotorSpeed Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False

    def ASSetInstallInjPointPos(self, nInjPoint, dxPos, dyPos, dzPos):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetInstallInjPointPos(c_short(nInjPoint), c_double(dxPos), c_double(dyPos), c_double(dzPos))
        if(rtn==1):
            self.Log("ASSetInstallInjPointPos successful\r\n")
            return True
        else:
            self.Log("ASSetInstallInjPointPos Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigMode(self, nMode):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigMode(c_short(nMode))
        if(rtn==1):
            self.Log("ASSetConfigMode successful\r\n")
            return True
        else:
            self.Log("ASSetConfigMode Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigStartSignal(self, nContact):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigStartSignal(c_short(nContact))
        if(rtn==1):
            self.Log("ASSetConfigStartSignal successful\r\n")
            return True
        else:
            self.Log("ASSetConfigStartSignal Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigReadyContact(self, nLogic):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigReadyContact(c_short(nLogic))
        if(rtn==1):
            self.Log("ASSetConfigReadyContact successful\r\n")
            return True
        else:
            self.Log("ASSetConfigReadyContact Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigWaitPos(self, nWaitPos):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigWaitPos(c_short(nWaitPos))
        if(rtn==1):
            self.Log("ASSetConfigWaitPos successful\r\n")
            return True
        else:
            self.Log("ASSetConfigWaitPos Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigTray(self, nTray, nTrayTyp):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigTray(c_short(nTray), c_short(nTrayTyp))
        if(rtn==1):
            self.Log("ASSetConfigTray successful\r\n")
            return True
        else:
            self.Log("ASSetConfigTray Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigTrayMetrics(self, nTray, nVials, nCols, nRows, dColDist, dRowDist):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigTrayMetrics(c_short(nTray), c_short(nVials),  c_short(nCols),  c_short(nRows), c_double(dColDist), c_double(dRowDist))
        if(rtn==1):
            self.Log("ASSetConfigTrayMetrics successful\r\n")
            return True
        else:
            self.Log("ASSetConfigTrayMetrics Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigWashStation(self, nType):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigWashStation(c_short(nType))
        if(rtn==1):
            self.Log("ASSetConfigWashStation successful\r\n")
            return True
        else:
            self.Log("ASSetConfigWashStation Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigSyringeVol(self, nSyrVol):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigSyringeVol(c_short(nSyrVol))
        if(rtn==1):
            self.Log("ASSetConfigSyringeVol successful\r\n")
            return True
        else:
            self.Log("ASSetConfigSyringeVol Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigSyringeSpeed(self, nzUpSpd, nzDwnSpd):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigSyringeSpeed(c_short(nzUpSpd),c_short(nzDwnSpd))
        if(rtn==1):
            self.Log("ASSetConfigSyringeSpeed successful\r\n")
            return True
        else:
            self.Log("ASSetConfigSyringeSpeed Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetConfigStartCycleBuzzer(self, nBuzzer):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetConfigStartCycleBuzzer(c_short(nBuzzer))
        if(rtn==1):
            self.Log("ASSetConfigStartCycleBuzzer successful\r\n")
            return True
        else:
            self.Log("ASSetConfigStartCycleBuzzer Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodInjPointNo(self, nInjPoint):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetMethodInjPointNo(c_short(nInjPoint))
        if(rtn==1):
            self.Log("ASSetMethodInjPointNo successful\r\n")
            return True
        else:
            self.Log("ASSetMethodInjPointNo Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodSimpleInjection(self, dSampleVol, nPumps, dAirGapVol):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetMethodSimpleInjection(c_double(dSampleVol), c_short(nPumps), c_double(dAirGapVol))
        if(rtn==1):
            self.Log("ASSetMethodSimpleInjection successful\r\n")
            return True
        else:
            self.Log("ASSetMethodSimpleInjection Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodSandwichInjection(self, nSolvent, dSolventVol, dAirGapVolPre, dSampleVol, dAirGapVolPost):
        self.ASWaitIdle()
        rtn=self.lib.alsgSetMethodSandwichInjection(c_short(nSolvent), c_double(dSolventVol), c_double(dAirGapVolPre), c_double(dSampleVol), c_double(dAirGapVolPost))
        if(rtn==1):
            self.Log("ASSetMethodSandwichInjection successful\r\n")
            return True
        else:
            self.Log("ASSetMethodSandwichInjection Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodISTDInjection(self, dAirGapVolPre, dISTDVol, dAirGapVolPost, dSampleVol, dAirGapVol):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodISTDInjection(c_double(dAirGapVolPre), c_double(dISTDVol), c_double(dAirGapVolPost), c_double(dSampleVol), c_double(dAirGapVol))
        if(rtn==1):
            self.Log("ASSetMethodISTDInjection successful\r\n")
            return True
        else:
            self.Log("ASSetMethodISTDInjection Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodPreInjWashes(self, nSolvent1, nSolvent2, nSolvent3, nSample ):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodPreInjWashes(c_short(nSolvent1), c_short(nSolvent2), c_short(nSolvent3), c_short(nSample))
        if(rtn==1):
            self.Log("ASSetMethodPreInjWashes successful\r\n")
            return True
        else:
            self.Log("ASSetMethodPreInjWashes Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodPostInjWashes(self, nSolvent1, nSolvent2, nSolvent3):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodPostInjWashes(c_short(nSolvent1), c_short(nSolvent2), c_short(nSolvent3))
        if(rtn==1):
            self.Log("ASSetMethodPostInjWashes successful\r\n")
            return True
        else:
            self.Log("ASSetMethodPostInjWashes Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodSampleWashVol(self, dWashVol):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodSampleWashVol(c_double(dWashVol))
        if(rtn==1):
            self.Log("ASSetMethodSampleWashVol successful\r\n")
            return True
        else:
            self.Log("ASSetMethodSampleWashVol Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodPreInjWashVol(self, dWashVol1,  dWashVol2,  dWashVol3):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodPreInjWashVol(c_double(dWashVol1), c_double(dWashVol2), c_double(dWashVol3))
        if(rtn==1):
            self.Log("ASSetMethodPreInjWashVol successful\r\n")
            return True
        else:
            self.Log("ASSetMethodPreInjWashVol Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodPostInjWashVol(self, dWashVol1,  dWashVol2,  dWashVol3):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodPostInjWashVol(c_double(dWashVol1), c_double(dWashVol2), c_double(dWashVol3))
        if(rtn==1):
            self.Log("ASSetMethodPostInjWashVol successful\r\n")
            return True
        else:
            self.Log("ASSetMethodPostInjWashVol Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodValveWashes(self, nSolvent1, nSolvent2):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodValveWashes(c_short(nSolvent1), c_short(nSolvent2))
        if(rtn==1):
            self.Log("ASSetMethodValveWashes successful\r\n")
            return True
        else:
            self.Log("ASSetMethodValveWashes Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodInjDepth(self, dDepth):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodInjDepth(c_double(dDepth))
        if(rtn==1):
            self.Log("ASSetMethodInjDepth successful\r\n")
            return True
        else:
            self.Log("ASSetMethodInjDepth Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodSpeed(self, dSolventDraw, dSampleDraw, dInj, dSolventDisp, dSampleDisp, nSyrInsert):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodSpeed(c_double(dSolventDraw), c_double(dSampleDraw), c_double(dInj), c_double(dSolventDisp), c_double(dSampleDisp), c_short(nSyrInsert) )
        if(rtn==1):
            self.Log("ASSetMethodSpeed successful\r\n")
            return True
        else:
            self.Log("ASSetMethodSpeed Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASSetMethodDelay(self, dPreInjDelay, dPostInjDelay, nViscDelay, nSolvDelay):
        self.ASWaitIdle()
        rtn= self.lib.alsgSetMethodDelay(c_double(dPreInjDelay), c_double(dPostInjDelay), c_short(nViscDelay), c_short(nSolvDelay))
        if(rtn==1):
            self.Log("ASSetMethodDelay successful\r\n")
            return True
        else:
            self.Log("ASSetMethodDelay Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASRunMethod(self, nTray, nVial, nReps):
        self.ASWaitIdle()
        rtn= self.lib.alsgRunMethod(c_short(nTray), c_short(nVial), c_short(nReps))
        if(rtn==1):
            self.Log("ASRunMethod successful\r\n")
            return True
        else:
            self.Log("ASRunMethod Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASStepGoToSyrExchange(self, nStep):
        self.ASWaitIdle()
        rtn= self.lib.alsgStepGoToSyrExchange(c_short(nStep))
        if(rtn>=0):
            self.Log("ASStepGoToSyrExchange successful\r\n")
            return True
        else:
            self.Log("ASStepGoToSyrExchange Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASRunSyringeWash(self, nMode, nTray, nVial, nWashes):
        self.ASWaitIdle()
        rtn= self.lib.alsgRunSyringeWash(c_short(nMode), c_short(nTray), c_short(nVial), c_short(nWashes))
        if(rtn==1):
            self.Log("ASRunSyringeWash successful\r\n")
            return True
        else:
            self.Log("ASRunSyringeWash Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASRunValveWash(self, nMode, nWashes):
        self.ASWaitIdle()
        rtn= self.lib.alsgRunValveWash(c_short(nMode), c_short(nWashes))
        if(rtn==1):
            self.Log("ASRunValveWash successful\r\n")
            return True
        else:
            self.Log("ASRunValveWash Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASRunReference(self, nAxis, nDirection):
        self.ASWaitIdle()
        rtn= self.lib.alsgRunReference(c_short(nAxis), c_short(nDirection))
        if(rtn==1):
            self.Log("ASRunReference successful\r\n")
            return True
        else:
            self.Log("ASRunReference Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASRunAbort(self):
        self.ASWaitIdle()
        rtn= self.lib.alsgRunAbort()
        if(rtn==1):
            self.Log("ASRunAbort successful\r\n")
            return True
        else:
            self.Log("ASRunAbort Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASGetBusy(self):
        rtn= self.lib.alsgGetBusy()
        if(rtn==1):
            return True
        else:
            return False
    
    def ASGetIdle(self):
        rtn= int(self.lib.alsgGetStatus())
        if(rtn==5):  #idle
            return True
        else:
            return False
    
    def ASGetConfigSyringeVol(self):
        sze = 0xff & self.lib.alsgGetConfigSyringeVol()
        rtn=5.0
        if(sze==2):
            rtn= 10.0
        if(sze==1):
            rtn= 5.0
        return rtn

    def ASGetStatus(self):
        rtn= int(self.lib.alsgGetStatus())
        s=""
        if(rtn==0):
            s="No Error\r\n"
        if(rtn==1):
            s="Err"
            err= int(self.lib.alsgGetError()) & 0xffff
            if(err>0 and err!=70 and not self.abortInProgress):
                self.assertInj= False
                self.errCode=err
                s=s+str(self.errCode)+"\r\n"
                self.Log("Error Code=%s<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\r\n"%self.errCode)
                self.Log("Error String=%s\r\n"%self.ASGetError())
                self.ErrorRecoveryMode=True
                self.ASStepGoToWaste(0,20)
                self.ErrorRecoveryMode=False
                time.sleep(8.0)
                self.OnPauseBtn(None)
                time.sleep(3.0)
                self.OnPauseBtn(None)
                self.injectionComplete= True
            else:
                s="No Error\r\n"
        if(rtn==2):
            s="Abort\r\n"
        if(rtn==5):
            s="Idle\r\n"
        if(rtn==6):
            s="Move to Wait Position\r\n"
        if(rtn==7):
            s="Wait for GC Ready\r\n"
        if(rtn==11):
            s="GC Clean\r\n"
        if(rtn==12):
            s="GC Pre Clean\r\n"
        if(rtn==13):
            s="GC Prepare Inject\r\n"
        if(rtn==14):
            s="GC Inject\r\n"
        if(rtn==15):
            s="GC Post Clean\r\n"
        if(rtn==21):
            s="HPLC Clean\r\n"
        if(rtn==22):
            s="HPLC Pre Clean\r\n"
        if(rtn==23):
            s="HPLC Prepare Inject\r\n"
        if(rtn==24):
            s="HPLC Load\r\n"
        if(rtn==25):
            s="HPLC Inject\r\n"
        if(rtn==26):
            s="HPLC Extract\r\n"
        if(rtn==27):
            s="HPLC Post Clean\r\n"
        if(rtn==28):
            s="HPLC Valve Clean\r\n"
        return s
    
    def ASBeep(self, nReps):
        self.ASWaitIdle()
        rtn= self.lib.alsgBeep(c_short(nReps))
        if(rtn==1):
            self.Log("ASBeep successful\r\n")
            return True
        else:
            self.Log("ASBeep Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASGetDiagPlungerStrokes(self):
        self.ASWaitIdle()
        rtn= self.lib.alsgGetDiagPlungerStrokes()
        self.Log("ASGetDiagPlungerStrokes = %d Plunger Strokes\r\n"%rtn)
        return rtn
    
    def ASResetDiagPlungerStrokes(self):
        self.ASWaitIdle()
        rtn= 0 #self.lib.alsgResetDiagPlungerStrokes()  #This explodes<<<<<
        self.Log("ASResetDiagPlungerStrokes = %d Plunger Strokes\r\n"%rtn)
        return rtn
    
    def ASGetDiagInjections(self, nInjPoint):
        self.ASWaitIdle()
        rtn= self.lib.alsgGetDiagInjections(c_short(nInjPoint))
        self.Log("ASGetDiagInjections = %d Plunger Strokes\r\n"%rtn)
        return rtn
    
    def ASResetDiagInjections(self, nInjPoint):
        self.ASWaitIdle()
        rtn= 0 #self.lib.alsgResetDiagInjections(nInjPoint)    #This explodes<<<<<
        self.Log("ASResetDiagInjections = %d Injections\r\n"%rtn)
        return rtn
    
    def ASStepGoToVial(self, nTray, nPos, dRelDepth):
        self.ASWaitIdle()
        rtn= 0#self.lib.alsgStepGoToVial(c_short(nTray), c_short(nPos), c_double(dRelDepth))  #This isn't exported from the dll!!    
        if(rtn==1):
            self.Log("ASStepGoToVial successful\r\n")
            return True
        else:
            self.Log("ASStepGoToVial Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASStepGoToInject(self, nInjPoint, dRelDepth):
        self.ASWaitIdle()
        rtn= self.lib.alsgStepGoToInject(c_short(nInjPoint), c_double(dRelDepth))      
        if(rtn==1):
            self.Log("ASStepGoToInject successful\r\n")
            return True
        else:
            self.Log("ASStepGoToInject Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
            
    def ASStepGoToSolvent(self, nPos, dRelDepth):
        self.ASWaitIdle()
        rtn= self.lib.alsgStepGoToSolvent(c_short(nPos), c_double(dRelDepth))      
        if(rtn==1):
            self.Log("ASStepGoToSolvent successful\r\n")
            return True
        else:
            self.Log("ASStepGoToSolvent Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASStepGoToWaste(self, nPos, dRelDepth):
        self.ASWaitIdle()
        rtn= self.lib.alsgStepGoToWaste(c_short(nPos), c_double(dRelDepth))  #This isn't exported from the dll!!    
        if(rtn==1):
            self.Log("ASStepGoToWaste successful\r\n")
            return True
        else:
            if(self.ErrorRecoveryMode == False):
                self.Log("ASStepGoToWaste Failed\r\n")
                self.Log("Error =%s\r\n"%self.ASGetError())
                return False
    
    def ASStepGoToWait(self):
        self.ASWaitIdle()
        rtn= self.lib.alsgStepGoToWait()    #This isn't exported from the dll!!
        if(rtn==1):
            self.Log("ASStepGoToWait successful\r\n")
            return True
        else:
            self.Log("ASStepGoToWait Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASStepDraw(self, dAmount, dSpeed):
        self.ASWaitIdle()
        rtn= 0#self.lib.alsgStepDraw()    #This isn't exported from the dll!!
        if(rtn==1):
            self.Log("ASStepDraw successful\r\n")
            return True
        else:
            self.Log("ASStepDraw Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASStepDispense(self, dAmount, dSpeed):
        self.ASWaitIdle()
        rtn= 0#self.lib.alsgStepDispense()    #This isn't exported from the dll!!
        if(rtn==1):
            self.Log("ASStepDispense successful\r\n")
            return True
        else:
            self.Log("ASStepDispense Failed\r\n")
            self.Log("Error =%s\r\n"%self.ASGetError())
            return False
    
    def ASGetError(self):
        err=int(self.lib.alsgGetError()) & 0xffff
        if(err==0):
            return "00=No Error"
        if(err==1):
            return "01=Parameter file not found"
        if(err==2):
            return "02=Open Interface Failed"
        if(err==3):
            return "03=COM Port could not be opened"
        if(err==10):
            return "10=Error Mode Range"
        if(err==11):
            return "11=Injection Point Range"
        if(err==12):
            return "12=Start Signal Range"
        if(err==13):
            return "13=GC Ready Contact Range"
        if(err==14):
            return "14=Wait Position Range"
        if(err==15):
            return "15=Tray Type Range"
        if(err==16):
            return "16=Wash Station Type Range"
        if(err==17):
            return "17=Syringe Volume Range"
        if(err==18):
            return "18=Plunger Zero Position Range"
        if(err==19):
            return "19=Z Up Speed Range"
        if(err==20):
            return "20=Z down Speed Range"
        if(err==21):
            return "21=Buzzer Range"
        if(err==30):
            return "30=X Speed Range"
        if(err==31):
            return "31=Y Speed Range"
        if(err==32):
            return "32=Injection Point Position Range"
        if(err==33):
            return "33=Syringe Exchange Position Range"
        if(err==34):
            return "34=Tray 1 Position Range"
        if(err==35):
            return "35=Tray 2 Position Range"
        if(err==36):
            return "36=Sample Depth 1 Range"
        if(err==37):
            return "37=Sample Depth 2 Range"
        if(err==38):
            return "38=Wash Station Position Range"
        if(err==39):
            return "39=Solvent Depth Range"
        if(err==40):
            return "40=Waste Depth Range"
        if(err==41):
            return "41=ISTD Depth Range"
        if(err==50):
            return "50=Injection Mode Range"
        if(err==51):
            return "51=Injection Technique Range"
        if(err==52):
            return "52=Injection Mode Parameter Range"
        if(err==53):
            return "53=Injection Volume Range"
        if(err==54):
            return "54=Wash Syringe Range"
        if(err==55):
            return "55=Valve Clean Range"
        if(err==56):
            return "56=Tray Range"
        if(err==57):
            return "57=Vial Range"
        if(err==58):
            return "58=Solvent Range"
        if(err==59):
            return "59=Waste Range"
        if(err==60):
            return "60=Washes Range"
        if(err==61):
            return "61=Volume Range"
        if(err==62):
            return "62=Delay Range"
        if(err==70):
            return "70=Cmd"
        if(err==71):
            return "71=No HPLC Function"
        if(err==72):
            return "72=Axis Range"
        if(err==73):
            return "73=Ref Start Freq Range"
        if(err==74):
            return "74=Ref End Freq Range"
        if(err==75):
            return "75=VEK Start Freq Range"
        if(err==76):
            return "76=VEK End Freq Range"
        if(err==77):
            return "77=Z Speed Range"
        if(err==78):
            return "78=U Speed Range"
        if(err==79):
            return "79=HPLC Valve Position Error"
        if(err==80):
            return "80=Vial Missing"
        if(err==81):
            return "81=Missing Step Goto Wait"
        if(err==82):
            return "82=Z Position Range"
        if(err==83):
            return "83=U Position Range"
        if(err==90):
            return "90=Throw Abort"

    def getInjectionComplete(self):
        return self.injectionComplete

    def getStatus(self):
        status=[]
        status.append("Date")
        status.append("Time")
        status.append("injTime")
        status.append("TrayName")
        status.append("SampleNum")
        status.append("jobNum")
        status.append("methodName")
        #self.Log(s)
        return status
    
    def OnPauseBtn(self, event): 
        if(not self.paused and self.nInj-self.numInjDone <=0):
            self.Log("Pause\r\n")
            self.EndBtn.Enable(True)
            self.PauseBtn.Enable(True)
            self.ChgSyringeBtn.Enable(True)
            self.PauseBtn.Label = 'Pause'
            self.RunBtn.Enable(True)
            self.paused=False
            self.pausedAndInjStarted=False
        if(self.paused):
            if(self.exchangePosition):
                return
            self.Log("Resume\r\n")
            cfg = self.Cfg
            self.Log("Using Vial #%d\r\n"%self.v)
            self.ASReadInit()
            self.syringeSize=self.ASGetConfigSyringeVol()        
            #self.ASSetInstallMotorSpeed(180,150)#self.ASSetInstallMotorSpeed(160,130)
            self.ASSetInstallMotorSpeed(260,150)
            self.ASSetMethodSampleWashVol((float)(cfg[self.method]['SampleWashVol']))      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            self.ASSetMethodInjPointNo(0)
            self.ASSetMethodSimpleInjection((float)(cfg[self.method]['SampleVol']), (int)(cfg[self.method]['FillStrokes']), 0.0)
            self.ASSetMethodPreInjWashes((int)(cfg[self.method]['PreRinse1']),(int)(cfg[self.method]['PreRinse2']),0,(int)(cfg[self.method]['PreSampleRinse']))   #ASSetMethodPreInjWashes(self, nSolvent1, nSolvent2, nSolvent3, nSample ):
            self.ASSetMethodPostInjWashes((int)(cfg[self.method]['PostRinse1']),(int)(cfg[self.method]['PostRinse2']),0)    #ASSetMethodPostInjWashes(self, nSolvent1, nSolvent2, nSolvent3):
            self.ASSetMethodSpeed((float)(cfg[self.method]['FillSpdRinse1']),(float)(cfg[self.method]['FillSpeed']),(float)(cfg[self.method]['InjSpd']),(float)(cfg[self.method]['WasteEject']),(float)(cfg[self.method]['WasteEject']),1)  #ASSetMethodSpeed(self, dSolventDraw, dSampleDraw, dInj, WasteDispenseSpeed20, dSampleDisp, nSyrInsert):
            self.ASSetMethodDelay((float)(cfg[self.method]['PreInjDly']),(float)(cfg[self.method]['PostInjDly']),(int)((float)(cfg[self.method]['ViscosityDly'])),(int)((float)(cfg[self.method]['SolventViscosityDelay'])))          #ASSetMethodDelay(self, dPreInjDelay, dPostInjDelay, nViscDelay, nSolvDelay):
            self.PauseBtn.Enable(True)
            self.EndBtn.Enable(True)
            self.PauseBtn.Enable(True)
            self.ChgSyringeBtn.Enable(False)
            self.PauseBtn.Label = 'Pause'
            self.RunBtn.Enable(False)
            self.paused=False
            self.running=True
        else:
            self.Log("Pause\r\n")
            self.EndBtn.Enable(True)
            self.PauseBtn.Enable(True)
            self.ChgSyringeBtn.Enable(True)
            self.PauseBtn.Label = 'Resume'
            self.RunBtn.Enable(False)
            self.paused=True
            self.running=False
            self.pausedAndInjStarted=False

    def OnClearSlot1Btn(self, event): 
        print "In Event handler `OnClearSlot1Btn'"
        self.Slot1Choice.SetLabel("")
        self.slot1CB.SetValue(False)
        self.slot1CB.Enable(False)
        self.slot1Inkwell = False
        self.setInkwell1_UIState()
        self.Slot1TrayNumEdit.SetValue(1)
        self.Slot1StartVialNumEdit.SetValue(1)
        self.Slot1EndVialNumEdit.SetValue(1)
        self.Slot1InjPerVialNumEdit.SetValue(1)

    def OnClearSlot2Btn(self, event): 
        print "In Event handler `OnClearSlot2Btn'"
        self.Slot2Choice.SetLabel("")
        self.slot2CB.SetValue(False)
        self.slot2CB.Enable(False)
        self.slot2Inkwell = False
        self.setInkwell2_UIState()
        self.Slot2TrayNumEdit.SetValue(1)
        self.Slot2StartVialNumEdit.SetValue(1)
        self.Slot2EndVialNumEdit.SetValue(1)
        self.Slot2InjPerVialNumEdit.SetValue(1)

    def OnClearSlot3Btn(self, event): 
        print "In Event handler `OnClearSlot3Btn'"
        self.Slot3Choice.SetLabel("")
        self.slot3CB.SetValue(False)
        self.slot3CB.Enable(False)
        self.slot3Inkwell = False
        self.setInkwell3_UIState()
        self.Slot3TrayNumEdit.SetValue(1)
        self.Slot3StartVialNumEdit.SetValue(1)
        self.Slot3EndVialNumEdit.SetValue(1)
        self.Slot3InjPerVialNumEdit.SetValue(1)

    def OnClearSlot4Btn(self, event): 
        print "In Event handler `OnClearSlot4Btn'"
        self.Slot4Choice.SetLabel("")
        self.slot4CB.SetValue(False)
        self.slot4CB.Enable(False)
        self.slot4Inkwell = False
        self.setInkwell4_UIState()
        self.Slot4TrayNumEdit.SetValue(1)
        self.Slot4StartVialNumEdit.SetValue(1)
        self.Slot4EndVialNumEdit.SetValue(1)
        self.Slot4InjPerVialNumEdit.SetValue(1)

    def OnClearSlot5Btn(self, event): 
        print "In Event handler `OnClearSlot5Btn'"
        self.Slot5Choice.SetLabel("")
        self.slot5CB.SetValue(False)
        self.slot5CB.Enable(False)
        self.slot5Inkwell = False
        self.setInkwell5_UIState()
        self.Slot5TrayNumEdit.SetValue(1)
        self.Slot5StartVialNumEdit.SetValue(1)
        self.Slot5EndVialNumEdit.SetValue(1)
        self.Slot5InjPerVialNumEdit.SetValue(1)

    def OnClearSlot6Btn(self, event): 
        print "In Event handler `OnClearSlot6Btn'"
        self.Slot6Choice.SetLabel("")
        self.slot6CB.SetValue(False)
        self.slot6CB.Enable(False)
        self.slot6Inkwell = False
        self.setInkwell6_UIState()
        self.Slot6TrayNumEdit.SetValue(1)
        self.Slot6StartVialNumEdit.SetValue(1)
        self.Slot6EndVialNumEdit.SetValue(1)
        self.Slot6InjPerVialNumEdit.SetValue(1)

    def OnClearSlot7Btn(self, event):
        print "In Event handler `OnClearSlot7Btn'"
        self.Slot7Choice.SetLabel("")
        self.slot7CB.SetValue(False)
        self.slot7CB.Enable(False)
        self.slot7Inkwell = False
        self.setInkwell7_UIState()
        self.Slot7TrayNumEdit.SetValue(1)
        self.Slot7StartVialNumEdit.SetValue(1)
        self.Slot7EndVialNumEdit.SetValue(1)
        self.Slot7InjPerVialNumEdit.SetValue(1)

    def OnClearSlot8Btn(self, event): 
        print "In Event handler `OnClearSlot8Btn'"
        self.Slot8Choice.SetLabel("")
        self.slot8CB.SetValue(False)
        self.slot8CB.Enable(False)
        self.slot8Inkwell = False
        self.setInkwell8_UIState()
        self.Slot8TrayNumEdit.SetValue(1)
        self.Slot8StartVialNumEdit.SetValue(1)
        self.Slot8EndVialNumEdit.SetValue(1)
        self.Slot8InjPerVialNumEdit.SetValue(1)

    def OnClearSlot9Btn(self, event):
        print "In Event handler `OnClearSlot9Btn'"
        self.Slot9Choice.SetLabel("")
        self.slot9CB.SetValue(False)
        self.slot9CB.Enable(False)
        self.slot9Inkwell = False
        self.setInkwell9_UIState()
        self.Slot9TrayNumEdit.SetValue(1)
        self.Slot9StartVialNumEdit.SetValue(1)
        self.Slot9EndVialNumEdit.SetValue(1)
        self.Slot9InjPerVialNumEdit.SetValue(1)

    def OnClearSlot10Btn(self, event): 
        print "In Event handler `OnClearSlot10Btn'"
        self.Slot10Choice.SetLabel("")
        self.slot10CB.SetValue(False)
        self.slot10CB.Enable(False)
        self.slot10Inkwell = False
        self.setInkwell10_UIState()
        self.Slot10TrayNumEdit.SetValue(1)
        self.Slot10StartVialNumEdit.SetValue(1)
        self.Slot10EndVialNumEdit.SetValue(1)
        self.Slot10InjPerVialNumEdit.SetValue(1)

    def OnLoadMethodChoice(self, event): 
        print "In Event handler `OnLoadMethodChoice'"
        method= self.LoadMethodChoice.GetStringSelection()
        if method!="":
            self.SampleVolNumEdit.SetValue(float(self.Cfg[method]['SampleVol']))
            self.FillSpeedNumEdit.SetValue(float(self.Cfg[method]['FillSpeed']))
            self.InjSpdNumEdit.SetValue(float(self.Cfg[method]['InjSpd']))
            self.SampleWashVolNumEdit.SetValue(float(self.Cfg[method]['SampleWashVol']))
            self.FillStrokesNumEdit.SetValue(int(self.Cfg[method]['FillStrokes']))
            self.PullupDlyNumEdit.SetValue(float(self.Cfg[method]['ViscosityDly']))
            self.PreInjDlyNumEdit.SetValue(float(self.Cfg[method]['PreInjDly']))
            self.PostInjDlyNumEdit.SetValue(float(self.Cfg[method]['PostInjDly']))
            self.WasteEjectNumEdit.SetValue(float(self.Cfg[method]['WasteEject']))
            self.RinseVolNumEdit.SetValue(float(self.Cfg[method]['RinseVol']))
            self.PreRinse1NumEdit.SetValue(int(self.Cfg[method]['PreRinse1']))
            self.PostRinse1NumEdit.SetValue(int(self.Cfg[method]['PostRinse1']))
            self.FillSpdRinse1NumEdit.SetValue(float(self.Cfg[method]['FillSpdRinse1']))
            self.PreRinse2NumEdit.SetValue(int(self.Cfg[method]['PreRinse2']))
            self.PreSampleRinseNumEdit.SetValue(int(self.Cfg[method]['PreSampleRinse']))
            self.PostRinse2NumEdit.SetValue(int(self.Cfg[method]['PostRinse2']))
            self.ViscosityDelayNumEdit.SetValue(float(self.Cfg[method]['SolventViscosityDelay']))
            self.RinseBetweenVialsCB.SetValue(bool(self.Cfg[method]["RinseBetweenVials"]=="True"))
            self.InjectionPointOffsetNumEdit.SetValue(float(self.Cfg[method]['InjectionPointOffset']))
            self.SetUITitle(method)

    def SetUITitle(self, method):
        self.ActiveMethod = method
        title = "Autosampler UI "+SW_VERSION+" | "+method
        self.SetTitle(title)

    def OnSlot1Choice(self, event): 
        print "In Event handler `OnSlot1Choice'"
        method= self.Slot1Choice.GetStringSelection()
        if method!="":
            self.slot1CB.Enable(True)

    def OnSlot2Choice(self, event): 
        print "In Event handler `OnSlot2Choice'"
        method= self.Slot2Choice.GetStringSelection()
        if method!="":
            self.slot2CB.Enable(True)

    def OnSlot3Choice(self, event): 
        print "In Event handler `OnSlot3Choice'"
        method= self.Slot3Choice.GetStringSelection()
        if method!="":
            self.slot3CB.Enable(True)

    def OnSlot4Choice(self, event): 
        print "In Event handler `Slot4Choice'"
        method= self.Slot4Choice.GetStringSelection()
        if method!="":
            self.slot4CB.Enable(True)

    def OnSlot5Choice(self, event): 
        print "In Event handler `OnSlot5Choice'"
        method= self.Slot5Choice.GetStringSelection()
        if method!="":
            self.slot5CB.Enable(True)

    def OnSlot6Choice(self, event):
        print "In Event handler `OnSlot6Choice'"
        method= self.Slot6Choice.GetStringSelection()
        if method!="":
            self.slot6CB.Enable(True)

    def OnSlot7Choice(self, event):
        print "In Event handler `OnSlot7Choice'"
        method= self.Slot7Choice.GetStringSelection()
        if method!="":
            self.slot7CB.Enable(True)

    def OnSlot8Choice(self, event):
        print "In Event handler `OnSlot8Choice'"
        method= self.Slot8Choice.GetStringSelection()
        if method!="":
            self.slot8CB.Enable(True)

    def OnSlot9Choice(self, event):
        print "In Event handler `OnSlot9Choice'"
        method= self.Slot9Choice.GetStringSelection()
        if method!="":
            self.slot9CB.Enable(True)

    def OnSlot10Choice(self, event):
        print "In Event handler `OnSlot10Choice'"
        method= self.Slot10Choice.GetStringSelection()
        if method!="":
            self.slot10CB.Enable(True)

    def OnSlot9CBChanged(self, event):
        print "In Event handler `OnSlot9CBChanged'"

    def OnSlot9StartVialNumEdit(self, event):
        print "In Event handler `OnSlot9StartVialNumEdit'"

    def OnSlot9EndVialNumEdit(self, event):
        print "In Event handler `OnSlot9EndVialNumEdit'"
    
    def OnSlot1TrayNumEdit(self, event):
        print "In Event handler `OnSlot1TrayNumEdit'"

    def OnSlot2TrayNumEdit(self, event):
        print "In Event handler `OnSlot2TrayNumEdit'"

    def OnSlot3TrayNumEdit(self, event):
        print "In Event handler `OnSlot3TrayNumEdit'"

    def OnSlot4TrayNumEdit(self, event):
        print "In Event handler `OnSlot4TrayNumEdit'"

    def OnSlot5TrayNumEdit(self, event):
        print "In Event handler `OnSlot5TrayNumEdit'"

    def OnSlot6TrayNumEdit(self, event):
        print "In Event handler `OnSlot6TrayNumEdit'"

    def OnSlot7TrayNumEdit(self, event):
        print "In Event handler `OnSlot7TrayNumEdit'"

    def OnSlot8TrayNumEdit(self, event):
        print "In Event handler `OnSlot8TrayNumEdit'"

    def OnSlot9TrayNumEdit(self, event):
        print "In Event handler `OnSlot9TrayNumEdit'"

    def OnSlot10TrayNumEdit(self, event):
        print "In Event handler `OnSlot10TrayNumEdit'"

    def OnSlot10CBChanged(self, event):
        print "In Event handler `OnSlot10CBChanged'"

    def OnSlot10StartVialNumEdit(self, event):
        print "In Event handler `OnSlot10StartVialNumEdit'"

    def OnSlot10EndVialNumEdit(self, event):
        print "In Event handler `OnSlot10EndVialNumEdit'"
    
    def OnSlot9InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot9InjPerVialNumEdit'"

    def OnSlot10InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot10InjPerVialNumEdit'"
        
    def OnInjectionPointOffsetNumEdit(self, event):
        print "In Event handler `OnInjectionPointOffsetNumEdit'"
        event.Skip()

    def OnSaveMethodBtn(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSaveMethodBtn'"
        method= self.MsgBox("Enter Method Name", "Save Method")
        methodList=self.LoadMethodChoice.GetStrings()
        for m in methodList:
            if m == method:
                print "Method Name Found!"
                msgString = "Method "+m+" will be overwritten"
                dlg = wx.MessageDialog( self, msgString, "Warning", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
                result = dlg.ShowModal()
                dlg.Destroy() 
                if result == wx.ID_OK:
                    if method!="":
                        self.Cfg[method]={}
                        self.Cfg[method]['SampleVol']=self.SampleVolNumEdit.GetValue()
                        self.Cfg[method]['FillSpeed']=self.FillSpeedNumEdit.GetValue()
                        self.Cfg[method]['InjSpd']=self.InjSpdNumEdit.GetValue()
                        self.Cfg[method]['SampleWashVol']=self.SampleWashVolNumEdit.GetValue()
                        self.Cfg[method]['FillStrokes']=self.FillStrokesNumEdit.GetValue()
                        self.Cfg[method]['ViscosityDly']=self.PullupDlyNumEdit.GetValue()
                        self.Cfg[method]['PreInjDly']=self.PreInjDlyNumEdit.GetValue()
                        self.Cfg[method]['PostInjDly']=self.PostInjDlyNumEdit.GetValue()
                        self.Cfg[method]['WasteEject']=self.WasteEjectNumEdit.GetValue()
                        self.Cfg[method]['RinseVol']=self.RinseVolNumEdit.GetValue()
                        self.Cfg[method]['PreRinse1']=self.PreRinse1NumEdit.GetValue()
                        self.Cfg[method]['PostRinse1']=self.PostRinse1NumEdit.GetValue()
                        self.Cfg[method]['FillSpdRinse1']=self.FillSpdRinse1NumEdit.GetValue()
                        self.Cfg[method]['PreRinse2']=self.PreRinse2NumEdit.GetValue()
                        self.Cfg[method]['PreSampleRinse']=self.PreSampleRinseNumEdit.GetValue()
                        self.Cfg[method]['PostRinse2']=self.PostRinse2NumEdit.GetValue()
                        self.Cfg[method]['SolventViscosityDelay']=self.ViscosityDelayNumEdit.GetValue()
                        self.Cfg[method]['RinseBetweenVials']=self.RinseBetweenVialsCB.GetValue()
                        self.Cfg[method]['InjectionPointOffset']=self.InjectionPointOffsetNumEdit.GetValue()
                        self.Cfg.write()
                        self.updateCfg()
                        self.LoadMethodChoice.SetStringSelection(method)
                        self.SetUITitle(method)
                        return
        if method!="":
            self.Cfg[method]={}
            self.Cfg[method]['SampleVol']=self.SampleVolNumEdit.GetValue()
            self.Cfg[method]['FillSpeed']=self.FillSpeedNumEdit.GetValue()
            self.Cfg[method]['InjSpd']=self.InjSpdNumEdit.GetValue()
            self.Cfg[method]['SampleWashVol']=self.SampleWashVolNumEdit.GetValue()
            self.Cfg[method]['FillStrokes']=self.FillStrokesNumEdit.GetValue()
            self.Cfg[method]['ViscosityDly']=self.PullupDlyNumEdit.GetValue()
            self.Cfg[method]['PreInjDly']=self.PreInjDlyNumEdit.GetValue()
            self.Cfg[method]['PostInjDly']=self.PostInjDlyNumEdit.GetValue()
            self.Cfg[method]['WasteEject']=self.WasteEjectNumEdit.GetValue()
            self.Cfg[method]['RinseVol']=self.RinseVolNumEdit.GetValue()
            self.Cfg[method]['PreRinse1']=self.PreRinse1NumEdit.GetValue()
            self.Cfg[method]['PostRinse1']=self.PostRinse1NumEdit.GetValue()
            self.Cfg[method]['FillSpdRinse1']=self.FillSpdRinse1NumEdit.GetValue()
            self.Cfg[method]['PreRinse2']=self.PreRinse2NumEdit.GetValue()
            self.Cfg[method]['PreSampleRinse']=self.PreSampleRinseNumEdit.GetValue()
            self.Cfg[method]['PostRinse2']=self.PostRinse2NumEdit.GetValue()
            self.Cfg[method]['SolventViscosityDelay']=self.ViscosityDelayNumEdit.GetValue()
            self.Cfg[method]['RinseBetweenVials']=self.RinseBetweenVialsCB.GetValue()
            self.Cfg[method]['InjectionPointOffset']=self.InjectionPointOffsetNumEdit.GetValue()
            self.Cfg.write()
            self.updateCfg()
            self.LoadMethodChoice.SetStringSelection(method)
            self.SetUITitle(method)

    def OnDeleteMethodBtn(self, event):
        print "In Event handler `OnDeleteMethodBtn'"
        method= self.MsgBox("Enter Method Name", "Delete Method")
        if method!="":
            self.Cfg[method]={}
            self.Cfg.__delitem__(method)
            self.Cfg.write()
            self.updateCfg()
            self.SetUITitle(method)            

    def OnTimer(self, event):
        #print "In Event handler `OnTimer'"
        if self.abortInProgress:
            return
        sa=""
        si=""
        so=""
        if self.assertInj:
            sa="A"
        else: 
            sa="a"
        if self.injectionComplete:
            si="I"
        else:
            si="i"
        if self.HeartBeat == 0:
            so="O"
            self.HeartBeat+=1
        else:
            so="+"
            self.HeartBeat=0
        s="%s%s%s"%(sa,si,so)
        self.statusbar.SetStatusText(s,4)
        
        running=""
        paused=""
        busy=""
        status=""
        if EMULATION:
            return

        if self.stop and (not self.ASGetBusy() or self.ASGetIdle()):
            self.EndBtn.Enable(False)
            self.RunBtn.Enable(True)
            self.ChgSyringeBtn.Enable(True)
            self.running=False
            self.paused=False
            self.numInjDone=0
            self.jobQueue=[]
            self.stop=False
            self.Log("Stopped\r\n")
        if self.paused:
            paused="Paused"
            self.running=False
        if self.running:
            running="Running"
        if self.ASGetBusy():
            busy="Busy"
        status=self.ASGetStatus()
        if status=="Move To Wait Position\r\n":
            self.stalledAtWait=True
        else:
            self.stalledAtWait=False
        self.statusbar.SetFieldsCount(5)
        self.statusbar.SetStatusText("V%d I%d"%(self.v,self.numInjDone),1)
        self.statusbar.SetStatusText("%s"%paused,2)
        self.statusbar.SetStatusText("%s"%running,2)
        self.statusbar.SetStatusText("%s"%status,3)
        if self.lastStatus != "GC Prepare Inject\r\n": 
            if status=="GC Prepare Inject\r\n":
                self.numInjDone+=1
                if self.paused:
                    self.pausedAndInjStarted=True
                    self.injectionComplete=True
        if self.lastStatus == "GC Prepare Inject\r\n" or self.lastStatus == "GC Post Clean\r\n": 
            if status=="Move to Wait Position\r\n":
                self.assertInj=False
                self.injectionComplete=True
                self.Log("#Injections Done=%d\r\n"%self.numInjDone)
        if self.pausedAndInjStarted==True:
            if status=="Move to Wait Position\r\n":
                self.ASRunAbort()
                self.pausedAndInjStarted=False            
        self.lastStatus=status    
        self.statusbar.SetStatusWidths([-10,-4,-6,-10,-3])
        if running and ((not self.ASGetBusy() or self.ASGetIdle()) or self.stalledAtWait):
            todo=self.nInj-self.numInjDone
            if(todo==0 and self.v < (self.endVial)):
                self.v+=1
                self.numInjDone=0                        
            elif(self.assertInj and todo>0):
                cfg = self.Cfg
                rinse = (bool(cfg[self.method]['RinseBetweenVials']=="True")) 
                self.Log("Using Vial #%d\r\n"%self.v)
                self.ASReadInit()
                self.syringeSize=self.ASGetConfigSyringeVol()        
                self.ASSetInstallMotorSpeed(260,150)#self.ASSetInstallMotorSpeed(160,130)
                self.ASSetMethodSampleWashVol((float)(cfg[self.method]['SampleWashVol']))      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.ASSetMethodPreInjWashVol((double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']) )      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.ASSetMethodPostInjWashVol((double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']))      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.ASSetMethodInjPointNo(0)
                self.ASSetMethodSimpleInjection((float)(cfg[self.method]['SampleVol']), (int)(cfg[self.method]['FillStrokes']), 0.0)
                if(not rinse or (rinse and self.lastVial!=self.v)):
                    self.ASSetMethodPreInjWashes((int)(cfg[self.method]['PreRinse1']),(int)(cfg[self.method]['PreRinse2']),0,(int)(cfg[self.method]['PreSampleRinse']))   #ASSetMethodPreInjWashes(self, nSolvent1, nSolvent2, nSolvent3, nSample ):
                    self.ASSetMethodPostInjWashes((int)(cfg[self.method]['PostRinse1']),(int)(cfg[self.method]['PostRinse2']),0)    #ASSetMethodPostInjWashes(self, nSolvent1, nSolvent2, nSolvent3):
                else:  #don't do rinses in this case
                    self.ASSetMethodPreInjWashes(0,0,0,0)   
                    self.ASSetMethodPostInjWashes(0,0,0)    
                self.ASSetMethodSpeed((float)(cfg[self.method]['FillSpdRinse1']),(float)(cfg[self.method]['FillSpeed']),(float)(cfg[self.method]['InjSpd']),(float)(cfg[self.method]['WasteEject']),(float)(cfg[self.method]['WasteEject']),1)  #ASSetMethodSpeed(self, dSolventDraw, dSampleDraw, dInj, WasteDispenseSpeed20, dSampleDisp, nSyrInsert):
                self.ASSetMethodDelay((float)(cfg[self.method]['PreInjDly']),(float)(cfg[self.method]['PostInjDly']),(int)((float)(cfg[self.method]['ViscosityDly'])),(int)((float)(cfg[self.method]['SolventViscosityDelay'])))          #ASSetMethodDelay(self, dPreInjDelay, dPostInjDelay, nViscDelay, nSolvDelay):
                self.ASSetMethodInjDepth((double)(cfg[self.method]['InjectionPointOffset']))
                self.ASRunMethod(self.tray,self.v,1)
                self.assertInj = False
                self.errCode = 0
                self.PauseBtn.Enable(True)
                self.lastVial = self.v
            elif(self.assertInj and self.v < (self.endVial)):
                cfg = self.Cfg
                rinse = (bool(cfg[self.method]['RinseBetweenVials']=="True")) 
                self.Log("Using Vial #%d\r\n"%self.v)
                self.ASReadInit()
                self.syringeSize=self.ASGetConfigSyringeVol()        
                self.ASSetInstallMotorSpeed(260,150)#self.ASSetInstallMotorSpeed(160,130)
                self.ASSetMethodSampleWashVol((float)(cfg[self.method]['SampleWashVol']))      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.ASSetMethodPreInjWashVol((double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']))      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.ASSetMethodPostInjWashVol((double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']),(double)(cfg[self.method]['RinseVol']))      #ASSetMethodSampleWashVol(self, dWashVol):<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tbd<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.ASSetMethodInjPointNo(0)
                self.ASSetMethodSimpleInjection((float)(cfg[self.method]['SampleVol']), (int)(cfg[self.method]['FillStrokes']), 0.0)
                if(not rinse or (rinse and self.lastVial!=self.v)):
                    self.ASSetMethodPreInjWashes((int)(cfg[self.method]['PreRinse1']),(int)(cfg[self.method]['PreRinse2']),0,(int)(cfg[self.method]['PreSampleRinse']))   #ASSetMethodPreInjWashes(self, nSolvent1, nSolvent2, nSolvent3, nSample ):
                    self.ASSetMethodPostInjWashes((int)(cfg[self.method]['PostRinse1']),(int)(cfg[self.method]['PostRinse2']),0)    #ASSetMethodPostInjWashes(self, nSolvent1, nSolvent2, nSolvent3):
                else:   #don't do rinses in this case
                    self.ASSetMethodPreInjWashes(0,0,0,0)
                    self.ASSetMethodPostInjWashes(0,0,0)
                self.ASSetMethodSpeed((float)(cfg[self.method]['FillSpdRinse1']),(float)(cfg[self.method]['FillSpeed']),(float)(cfg[self.method]['InjSpd']),(float)(cfg[self.method]['WasteEject']),(float)(cfg[self.method]['WasteEject']),1)  #ASSetMethodSpeed(self, dSolventDraw, dSampleDraw, dInj, WasteDispenseSpeed20, dSampleDisp, nSyrInsert):
                self.ASSetMethodDelay((float)(cfg[self.method]['PreInjDly']),(float)(cfg[self.method]['PostInjDly']),(int)((float)(cfg[self.method]['ViscosityDly'])),(int)((float)(cfg[self.method]['SolventViscosityDelay'])))          #ASSetMethodDelay(self, dPreInjDelay, dPostInjDelay, nViscDelay, nSolvDelay):
                self.ASSetMethodInjDepth(float(cfg[self.method]['InjectionPointOffset']))
                self.numInjDone=0
                self.assertInj = False
                self.errCode = 0
                self.ASRunMethod(self.tray,self.v,1)
                self.PauseBtn.Enable(True)
                self.lastVial = self.v
            elif self.paused:
                    return
            elif self.injectionComplete and len(self.jobQueue)<=0 and todo<=0:
                self.Log("Done!\r\n")
                self.RunBtn.Enable(True)
                self.EndBtn.Enable(False)
                self.PauseBtn.Enable(False)
                self.ChgSyringeBtn.Enable(True)
                self.LoadQueueBtn.Enable(True)
                self.SaveQueueBtn.Enable(True)                 
                self.running=False
                self.paused=False
                self.PauseBtn.Label = 'Pause'
                running=False
                self.EnableQueueUIElements(True)
            elif self.injectionComplete and todo>=1:
                pass
                #self.injectionComplete=False
            else:
                if(todo<=0):
                    if len(self.jobQueue) > 0:
                        j = self.jobQueue[0]
                        self.jobNum+=1
                        self.tray = int(j["Tray"])
                        self.method=(j["JobName"])
                        self.Log("Starting job number %s with method %s\r\n"%(self.jobNum,self.method))
                        self.nInj=int(j["numInj"])
                        self.startVial=int(j["startVial"])
                        self.endVial=int(j["endVial"])
                        self.v=self.startVial    #endVial+1:
                        self.running=True
                        self.numInjDone=0
                        try:
                            self.jobQueue.pop(0)
                        except:
                            pass

    def OnTeachWasteBtn(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnTeachWasteBtn'"

    def OnEndBtn(self, event): # wxGlade: MyFrame.<event_handler>
        self.abortInProgress = True
        self.running=False
        self.Log("End\r\n")
        self.RunBtn.Enable(True)
        self.EndBtn.Enable(False)
        self.PauseBtn.Enable(False)
        self.ChgSyringeBtn.Enable(True)
        self.LoadQueueBtn.Enable(True)
        self.SaveQueueBtn.Enable(True)         
        self.EnableQueueUIElements(True)
        self.paused=False
        self.ASRunAbort()
        time.sleep(4)
        self.ASStepGoToSyrExchange(2)        
        self.ASStepGoToSyrExchange(3)        
        self.abortInProgress = False
        self.injectionComplete= True        

    def OnStopBtn(self, event):
        if self.exchangePosition:
            return
        self.assertInj=False
        self.injectionComplete=False
        self.stop=True
        self.getStatus()
        self.ChgSyringeBtn.Enable(True)
        self.EnableQueueUIElements(True)
        self.LoadQueueBtn.Enable(True)
        self.SaveQueueBtn.Enable(True)         

    def OnRinseBetweenVialsCBChanged(self, event):
        print "In Event handler `OnRinseBetweenVialsCBChanged'"

    def OnSlot1CBChanged(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot1CBChanged'"

    def OnSlot2CBChanged(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot2CBChanged'"

    def OnSlot3CBChanged(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot3CBChanged'"

    def OnSlot4CBChanged(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot4CBChanged'"

    def OnSlot5CBChanged(self, event):
        print "In Event handler `OnSlot5CBChanged'"

    def OnSlot5StartVialNumEdit(self, event):
        print "In Event handler `OnSlot5StartVialNumEdit'"

    def OnSlot5EndVialNumEdit(self, event):
        print "In Event handler `OnSlot5EndVialNumEdit'"

    def OnSlot6CBChanged(self, event):
        print "In Event handler `OnSlot6CBChanged'"

    def OnSlot6StartVialNumEdit(self, event):
        print "In Event handler `OnSlot6StartVialNumEdit'"

    def OnSlot6EndVialNumEdit(self, event):
        print "In Event handler `OnSlot6EndVialNumEdit'"

    def OnSlot7CBChanged(self, event):
        print "In Event handler `OnSlot7CBChanged'"

    def OnSlot7StartVialNumEdit(self, event):
        print "In Event handler `OnSlot7StartVialNumEdit'"

    def OnSlot7EndVialNumEdit(self, event):
        print "In Event handler `OnSlot7EndVialNumEdit'"

    def OnSlot8CBChanged(self, event):
        print "In Event handler `OnSlot8CBChanged'"

    def OnSlot8StartVialNumEdit(self, event):
        print "In Event handler `OnSlot8StartVialNumEdit'"

    def OnSlot8EndVialNumEdit(self, event):
        print "In Event handler `OnSlot8EndVialNumEdit'"
    
    def OnInjPerVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnInjPerVialNumEdit'"

    def OnSlot1StartVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot1StartVialNumEdit'"

    def OnSlot1EndVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot1EndVialNumEdit'"

    def OnSlot2StartVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot2StartVialNumEdit'"

    def OnSlot2EndVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot2EndVialNumEdit'"

    def OnSlot3StartVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot3StartVialNumEdit'"

    def OnSlot3EndVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot3EndVialNumEdit'"

    def OnSlot4StartVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot4StartVialNumEdit'"

    def OnSlot4EndVialNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSlot4EndVialNumEdit'"

    def OnPreRinse1NumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPreRinse1NumEdit'"

    def OnPreSampleRinseNumEdit(self, event):
        print "In Event handler `OnPreSampleRinseNumEdit'"

    def OnSampleVolNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSampleVolNumEdit'"

    def OnPostRinse1NumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPostRinse1NumEdit'"

    def OnFillSpeedNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnFillSpeedNumEdit'"

    def OnFillSpdRinse1NumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnFillSpdRinse1NumEdit'"

    def OnInjSpdNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnInjSpdNumEdit'"

    def OnSampleWashVolNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnSampleWashVolNumEdit'"

    def OnFillStrokesNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnFillStrokesNumEdit'"

    def OnPreRinse2NumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPreRinse2NumEdit'"

    def OnPullupDlyNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPullupDlyNumEdit'"

    def OnPostRinse2NumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPostRinse2NumEdit'"

    def OnPreInjDlyNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPreInjDlyNumEdit'"

    def OnPostInjDlyNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnPostInjDlyNumEdit'"

    def OnViscosityDelayNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnViscosityDelayNumEdit'"

    def OnWasteEjectNumEdit(self, event): # wxGlade: MyFrame.<event_handler>
        print "In Event handler `OnWasteEjectNumEdit'"

    def OnRinseVolNumEdit(self, event):
        print "In Event handler `OnRinseVolNumEdit"

    def OnSlot1InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot1InjPerVialNumEdit'"

    def OnSlot2InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot2InjPerVialNumEdit'"

    def OnSlot3InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot3InjPerVialNumEdit'"

    def OnSlot4InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot4InjPerVialNumEdit'"

    def OnSlot5InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot5InjPerVialNumEdit'"

    def OnSlot6InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot6InjPerVialNumEdit'"

    def OnSlot7InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot7InjPerVialNumEdit'"

    def OnSlot8InjPerVialNumEdit(self, event):
        print "In Event handler `OnSlot8InjPerVialNumEdit'"

    def setInkwell1_UIState(self):
        if self.slot1Inkwell:
            self.Slot1TrayNumEdit.Hide()            
            self.Slot1StartVialNumEdit.Hide()
            self.Slot1EndVialNumEdit.Hide()
        else: 
            self.Slot1TrayNumEdit.Show()            
            self.Slot1StartVialNumEdit.Show()
            self.Slot1EndVialNumEdit.Show()
        self.Slot1Choice.InvalidateBestSize()
        self.Slot1Choice.Update()
        self.Slot1TrayNumEdit.Update()
        self.Slot1StartVialNumEdit.Update()
        self.Slot1EndVialNumEdit.Update()      

    def setInkwell2_UIState(self):
        if self.slot2Inkwell:
            self.Slot2TrayNumEdit.Hide()            
            self.Slot2StartVialNumEdit.Hide()
            self.Slot2EndVialNumEdit.Hide()
        else: 
            self.Slot2TrayNumEdit.Show()            
            self.Slot2StartVialNumEdit.Show()
            self.Slot2EndVialNumEdit.Show()
        self.Slot2Choice.InvalidateBestSize()
        self.Slot2Choice.Update()
        self.Slot2TrayNumEdit.Update()
        self.Slot2StartVialNumEdit.Update()
        self.Slot2EndVialNumEdit.Update()      

    def setInkwell3_UIState(self):
        if self.slot3Inkwell:
            self.Slot3TrayNumEdit.Hide()            
            self.Slot3StartVialNumEdit.Hide()
            self.Slot3EndVialNumEdit.Hide()
        else: 
            self.Slot3TrayNumEdit.Show()            
            self.Slot3StartVialNumEdit.Show()
            self.Slot3EndVialNumEdit.Show()
        self.Slot3Choice.InvalidateBestSize()
        self.Slot3Choice.Update()
        self.Slot3TrayNumEdit.Update()
        self.Slot3StartVialNumEdit.Update()
        self.Slot3EndVialNumEdit.Update()      

    def setInkwell4_UIState(self):
        if self.slot4Inkwell:
            self.Slot4TrayNumEdit.Hide()            
            self.Slot4StartVialNumEdit.Hide()
            self.Slot4EndVialNumEdit.Hide()
        else: 
            self.Slot4TrayNumEdit.Show()            
            self.Slot4StartVialNumEdit.Show()
            self.Slot4EndVialNumEdit.Show()
        self.Slot4Choice.InvalidateBestSize()
        self.Slot4Choice.Update()
        self.Slot4TrayNumEdit.Update()
        self.Slot4StartVialNumEdit.Update()
        self.Slot4EndVialNumEdit.Update()      

    def setInkwell5_UIState(self):
        if self.slot5Inkwell:
            self.Slot5TrayNumEdit.Hide()            
            self.Slot5StartVialNumEdit.Hide()
            self.Slot5EndVialNumEdit.Hide()
        else: 
            self.Slot5TrayNumEdit.Show()            
            self.Slot5StartVialNumEdit.Show()
            self.Slot5EndVialNumEdit.Show()
        self.Slot5Choice.InvalidateBestSize()
        self.Slot5Choice.Update()
        self.Slot5TrayNumEdit.Update()
        self.Slot5StartVialNumEdit.Update()
        self.Slot5EndVialNumEdit.Update()      

    def setInkwell6_UIState(self):
        if self.slot6Inkwell:
            self.Slot6TrayNumEdit.Hide()            
            self.Slot6StartVialNumEdit.Hide()
            self.Slot6EndVialNumEdit.Hide()
        else: 
            self.Slot6TrayNumEdit.Show()            
            self.Slot6StartVialNumEdit.Show()
            self.Slot6EndVialNumEdit.Show()
        self.Slot6Choice.InvalidateBestSize()
        self.Slot6Choice.Update()
        self.Slot6TrayNumEdit.Update()
        self.Slot6StartVialNumEdit.Update()
        self.Slot6EndVialNumEdit.Update()      

    def setInkwell7_UIState(self):
        if self.slot7Inkwell:
            self.Slot7TrayNumEdit.Hide()            
            self.Slot7StartVialNumEdit.Hide()
            self.Slot7EndVialNumEdit.Hide()
        else: 
            self.Slot7TrayNumEdit.Show()            
            self.Slot7StartVialNumEdit.Show()
            self.Slot7EndVialNumEdit.Show()
        self.Slot7Choice.InvalidateBestSize()
        self.Slot7Choice.Update()
        self.Slot7TrayNumEdit.Update()
        self.Slot7StartVialNumEdit.Update()
        self.Slot7EndVialNumEdit.Update()      

    def setInkwell8_UIState(self):
        if self.slot8Inkwell:
            self.Slot8TrayNumEdit.Hide()            
            self.Slot8StartVialNumEdit.Hide()
            self.Slot8EndVialNumEdit.Hide()
        else: 
            self.Slot8TrayNumEdit.Show()            
            self.Slot8StartVialNumEdit.Show()
            self.Slot8EndVialNumEdit.Show()
        self.Slot8Choice.InvalidateBestSize()
        self.Slot8Choice.Update()
        self.Slot8TrayNumEdit.Update()
        self.Slot8StartVialNumEdit.Update()
        self.Slot8EndVialNumEdit.Update()      

    def setInkwell9_UIState(self):
        if self.slot9Inkwell:
            self.Slot9TrayNumEdit.Hide()            
            self.Slot9StartVialNumEdit.Hide()
            self.Slot9EndVialNumEdit.Hide()
        else: 
            self.Slot9TrayNumEdit.Show()            
            self.Slot9StartVialNumEdit.Show()
            self.Slot9EndVialNumEdit.Show()
        self.Slot9Choice.InvalidateBestSize()
        self.Slot9Choice.Update()
        self.Slot9TrayNumEdit.Update()
        self.Slot9StartVialNumEdit.Update()
        self.Slot9EndVialNumEdit.Update()      

    def setInkwell10_UIState(self):
        if self.slot10Inkwell:
            self.Slot10TrayNumEdit.Hide()            
            self.Slot10StartVialNumEdit.Hide()
            self.Slot10EndVialNumEdit.Hide()
        else: 
            self.Slot10TrayNumEdit.Show()            
            self.Slot10StartVialNumEdit.Show()
            self.Slot10EndVialNumEdit.Show()
        self.Slot10Choice.InvalidateBestSize()
        self.Slot10Choice.Update()
        self.Slot10TrayNumEdit.Update()
        self.Slot10StartVialNumEdit.Update()
        self.Slot10EndVialNumEdit.Update()      

    def OnSlot1ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot1"
            if not self.slot1Inkwell:
                self.slot1Inkwell = True
            else: 
                self.slot1Inkwell = False
            self.setInkwell1_UIState()
            self.Slot1InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key, Nothing to do"
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved1=self.Slot1Choice.GetStringSelection()
            saved2=self.Slot2Choice.GetStringSelection()
            savedList=self.Slot1Choice.GetStrings()
            self.Slot1Choice.Clear()
            self.Slot2Choice.Clear()
            self.Slot1Choice.AppendItems(savedList)
            self.Slot2Choice.AppendItems(savedList)
            self.Slot1Choice.SetStringSelection(saved2)
            self.Slot2Choice.SetStringSelection(saved1)

            saved1 = self.Slot1EndVialNumEdit.Value
            saved2 = self.Slot2EndVialNumEdit.Value
            self.Slot2EndVialNumEdit.SetValue(saved1)
            self.Slot1EndVialNumEdit.SetValue(saved2)

            saved1 = self.Slot1InjPerVialNumEdit.Value
            saved2 = self.Slot2InjPerVialNumEdit.Value
            self.Slot2InjPerVialNumEdit.SetValue(saved1)
            self.Slot1InjPerVialNumEdit.SetValue(saved2)

            saved1 = self.Slot1TrayNumEdit.Value
            saved2 = self.Slot2TrayNumEdit.Value
            self.Slot1TrayNumEdit.SetValue(saved2)
            self.Slot2TrayNumEdit.SetValue(saved1)

            saved1 = self.Slot1StartVialNumEdit.Value
            saved2 = self.Slot2StartVialNumEdit.Value
            self.Slot2StartVialNumEdit.SetValue(saved1)
            self.Slot1StartVialNumEdit.SetValue(saved2)
            
            saved1 = self.slot1Inkwell
            saved2 = self.slot2Inkwell
            self.slot1Inkwell = saved2
            self.slot2Inkwell = saved1
            self.setInkwell1_UIState()
            self.setInkwell2_UIState()

            saved1 = self.slot1CB.Value
            saved2 = self.slot2CB.Value
            self.slot2CB.SetValue(saved1)
            self.slot1CB.SetValue(saved2)
            self.Slot2StartVialNumEdit.SetFocus()

    def OnSlot2ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot2"
            if not self.slot2Inkwell:
                self.slot2Inkwell = True
            else: 
                self.slot2Inkwell = False
            self.setInkwell2_UIState()
            self.Slot2InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved2=self.Slot2Choice.GetStringSelection()
            saved1=self.Slot1Choice.GetStringSelection()
            savedList=self.Slot2Choice.GetStrings()
            self.Slot1Choice.Clear()
            self.Slot2Choice.Clear()
            self.Slot1Choice.AppendItems(savedList)
            self.Slot2Choice.AppendItems(savedList)
            self.Slot2Choice.SetStringSelection(saved1)
            self.Slot1Choice.SetStringSelection(saved2)

            saved2 = self.Slot2EndVialNumEdit.Value
            saved1 = self.Slot1EndVialNumEdit.Value
            self.Slot2EndVialNumEdit.SetValue(saved1)
            self.Slot1EndVialNumEdit.SetValue(saved2)

            saved2 = self.Slot2InjPerVialNumEdit.Value
            saved1 = self.Slot1InjPerVialNumEdit.Value
            self.Slot1InjPerVialNumEdit.SetValue(saved2)
            self.Slot2InjPerVialNumEdit.SetValue(saved1)

            saved2 = self.Slot2StartVialNumEdit.Value
            saved1 = self.Slot1StartVialNumEdit.Value
            self.Slot1StartVialNumEdit.SetValue(saved2)
            self.Slot2StartVialNumEdit.SetValue(saved1)

            saved1 = self.Slot1TrayNumEdit.Value
            saved2 = self.Slot2TrayNumEdit.Value
            self.Slot1TrayNumEdit.SetValue(saved2)
            self.Slot2TrayNumEdit.SetValue(saved1)

            saved1 = self.slot1Inkwell
            saved2 = self.slot2Inkwell
            self.slot1Inkwell = saved2
            self.slot2Inkwell = saved1
            self.setInkwell1_UIState()
            self.setInkwell2_UIState()

            saved2 = self.slot2CB.Value
            saved1 = self.slot1CB.Value
            self.slot1CB.SetValue(saved2)
            self.slot2CB.SetValue(saved1)
            self.Slot1StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved2=self.Slot2Choice.GetStringSelection()
            saved3=self.Slot3Choice.GetStringSelection()
            savedList=self.Slot2Choice.GetStrings()
            self.Slot2Choice.Clear()
            self.Slot3Choice.Clear()
            self.Slot2Choice.AppendItems(savedList)
            self.Slot3Choice.AppendItems(savedList)
            self.Slot2Choice.SetStringSelection(saved3)
            self.Slot3Choice.SetStringSelection(saved2)

            saved2 = self.Slot2EndVialNumEdit.Value
            saved3 = self.Slot3EndVialNumEdit.Value
            self.Slot2EndVialNumEdit.SetValue(saved3)
            self.Slot3EndVialNumEdit.SetValue(saved2)

            saved2 = self.Slot2InjPerVialNumEdit.Value
            saved3 = self.Slot3InjPerVialNumEdit.Value
            self.Slot3InjPerVialNumEdit.SetValue(saved2)
            self.Slot2InjPerVialNumEdit.SetValue(saved3)

            saved2 = self.Slot2StartVialNumEdit.Value
            saved3 = self.Slot3StartVialNumEdit.Value
            self.Slot3StartVialNumEdit.SetValue(saved2)
            self.Slot2StartVialNumEdit.SetValue(saved3)

            saved2 = self.Slot2TrayNumEdit.Value
            saved3 = self.Slot3TrayNumEdit.Value
            self.Slot2TrayNumEdit.SetValue(saved3)
            self.Slot3TrayNumEdit.SetValue(saved2)

            saved2 = self.slot2Inkwell
            saved3 = self.slot3Inkwell
            self.slot2Inkwell = saved3
            self.slot3Inkwell = saved2
            self.setInkwell2_UIState()
            self.setInkwell3_UIState()

            saved2 = self.slot2CB.Value
            saved3 = self.slot3CB.Value
            self.slot3CB.SetValue(saved2)
            self.slot2CB.SetValue(saved3)
            self.Slot3StartVialNumEdit.SetFocus()

    def OnSlot3ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot3"
            if not self.slot3Inkwell:
                self.slot3Inkwell = True
            else: 
                self.slot3Inkwell = False
            self.setInkwell3_UIState()
            self.Slot3InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved3=self.Slot3Choice.GetStringSelection()
            saved2=self.Slot2Choice.GetStringSelection()
            savedList=self.Slot3Choice.GetStrings()
            self.Slot3Choice.Clear()
            self.Slot2Choice.Clear()
            self.Slot3Choice.AppendItems(savedList)
            self.Slot2Choice.AppendItems(savedList)
            self.Slot3Choice.SetStringSelection(saved2)
            self.Slot2Choice.SetStringSelection(saved3)

            saved3 = self.Slot3EndVialNumEdit.Value
            saved2 = self.Slot2EndVialNumEdit.Value
            self.Slot3EndVialNumEdit.SetValue(saved2)
            self.Slot2EndVialNumEdit.SetValue(saved3)

            saved3 = self.Slot3InjPerVialNumEdit.Value
            saved2 = self.Slot2InjPerVialNumEdit.Value
            self.Slot2InjPerVialNumEdit.SetValue(saved3)
            self.Slot3InjPerVialNumEdit.SetValue(saved2)

            saved3 = self.Slot3StartVialNumEdit.Value
            saved2 = self.Slot2StartVialNumEdit.Value
            self.Slot2StartVialNumEdit.SetValue(saved3)
            self.Slot3StartVialNumEdit.SetValue(saved2)

            saved2 = self.Slot2TrayNumEdit.Value
            saved3 = self.Slot3TrayNumEdit.Value
            self.Slot2TrayNumEdit.SetValue(saved3)
            self.Slot3TrayNumEdit.SetValue(saved2)

            saved2 = self.slot2Inkwell
            saved3 = self.slot3Inkwell
            self.slot2Inkwell = saved3
            self.slot3Inkwell = saved2
            self.setInkwell2_UIState()
            self.setInkwell3_UIState()

            saved3 = self.slot3CB.Value
            saved2 = self.slot2CB.Value
            self.slot2CB.SetValue(saved3)
            self.slot3CB.SetValue(saved2)
            self.Slot2StartVialNumEdit.SetFocus()
            
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved3=self.Slot3Choice.GetStringSelection()
            saved4=self.Slot4Choice.GetStringSelection()
            savedList=self.Slot3Choice.GetStrings()
            self.Slot3Choice.Clear()
            self.Slot4Choice.Clear()
            self.Slot3Choice.AppendItems(savedList)
            self.Slot4Choice.AppendItems(savedList)
            self.Slot3Choice.SetStringSelection(saved4)
            self.Slot4Choice.SetStringSelection(saved3)

            saved3 = self.Slot3EndVialNumEdit.Value
            saved4 = self.Slot4EndVialNumEdit.Value
            self.Slot3EndVialNumEdit.SetValue(saved4)
            self.Slot4EndVialNumEdit.SetValue(saved3)

            saved3 = self.Slot3InjPerVialNumEdit.Value
            saved4 = self.Slot4InjPerVialNumEdit.Value
            self.Slot4InjPerVialNumEdit.SetValue(saved3)
            self.Slot3InjPerVialNumEdit.SetValue(saved4)

            saved3 = self.Slot3StartVialNumEdit.Value
            saved4 = self.Slot4StartVialNumEdit.Value
            self.Slot4StartVialNumEdit.SetValue(saved3)
            self.Slot3StartVialNumEdit.SetValue(saved4)

            saved3 = self.Slot3TrayNumEdit.Value
            saved4 = self.Slot4TrayNumEdit.Value
            self.Slot3TrayNumEdit.SetValue(saved4)
            self.Slot4TrayNumEdit.SetValue(saved3)

            saved3 = self.slot3Inkwell
            saved4 = self.slot4Inkwell
            self.slot3Inkwell = saved4
            self.slot4Inkwell = saved3
            self.setInkwell3_UIState()
            self.setInkwell4_UIState()

            saved3 = self.slot3CB.Value
            saved4 = self.slot4CB.Value
            self.slot4CB.SetValue(saved3)
            self.slot3CB.SetValue(saved4)
            self.Slot4StartVialNumEdit.SetFocus()

    def OnSlot4ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot4"
            if not self.slot4Inkwell:
                self.slot4Inkwell = True
            else: 
                self.slot4Inkwell = False
            self.setInkwell4_UIState()
            self.Slot4InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved4=self.Slot4Choice.GetStringSelection()
            saved3=self.Slot3Choice.GetStringSelection()
            savedList=self.Slot4Choice.GetStrings()
            self.Slot4Choice.Clear()
            self.Slot3Choice.Clear()
            self.Slot4Choice.AppendItems(savedList)
            self.Slot3Choice.AppendItems(savedList)
            self.Slot4Choice.SetStringSelection(saved3)
            self.Slot3Choice.SetStringSelection(saved4)

            saved4 = self.Slot4EndVialNumEdit.Value
            saved3 = self.Slot3EndVialNumEdit.Value
            self.Slot4EndVialNumEdit.SetValue(saved3)
            self.Slot3EndVialNumEdit.SetValue(saved4)

            saved4 = self.Slot4InjPerVialNumEdit.Value
            saved3 = self.Slot3InjPerVialNumEdit.Value
            self.Slot4InjPerVialNumEdit.SetValue(saved3)
            self.Slot3InjPerVialNumEdit.SetValue(saved4)

            saved4 = self.Slot4StartVialNumEdit.Value
            saved3 = self.Slot3StartVialNumEdit.Value
            self.Slot4StartVialNumEdit.SetValue(saved3)
            self.Slot3StartVialNumEdit.SetValue(saved4)

            saved3 = self.Slot3TrayNumEdit.Value
            saved4 = self.Slot4TrayNumEdit.Value
            self.Slot3TrayNumEdit.SetValue(saved4)
            self.Slot4TrayNumEdit.SetValue(saved3)

            saved3 = self.slot3Inkwell
            saved4 = self.slot4Inkwell
            self.slot3Inkwell = saved4
            self.slot4Inkwell = saved3
            self.setInkwell3_UIState()
            self.setInkwell4_UIState()

            saved4 = self.slot4CB.Value
            saved3 = self.slot3CB.Value
            self.slot4CB.SetValue(saved3)
            self.slot3CB.SetValue(saved4)
            self.Slot3StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved4=self.Slot4Choice.GetStringSelection()
            saved5=self.Slot5Choice.GetStringSelection()
            savedList=self.Slot4Choice.GetStrings()
            self.Slot4Choice.Clear()
            self.Slot5Choice.Clear()
            self.Slot4Choice.AppendItems(savedList)
            self.Slot5Choice.AppendItems(savedList)
            self.Slot4Choice.SetStringSelection(saved5)
            self.Slot5Choice.SetStringSelection(saved4)

            saved4 = self.Slot4EndVialNumEdit.Value
            saved5 = self.Slot5EndVialNumEdit.Value
            self.Slot4EndVialNumEdit.SetValue(saved5)
            self.Slot5EndVialNumEdit.SetValue(saved4)

            saved4 = self.Slot4InjPerVialNumEdit.Value
            saved5 = self.Slot5InjPerVialNumEdit.Value
            self.Slot4InjPerVialNumEdit.SetValue(saved5)
            self.Slot5InjPerVialNumEdit.SetValue(saved4)

            saved4 = self.Slot4StartVialNumEdit.Value
            saved5 = self.Slot5StartVialNumEdit.Value
            self.Slot4StartVialNumEdit.SetValue(saved5)
            self.Slot5StartVialNumEdit.SetValue(saved4)

            saved4 = self.Slot4TrayNumEdit.Value
            saved5 = self.Slot5TrayNumEdit.Value
            self.Slot4TrayNumEdit.SetValue(saved5)
            self.Slot5TrayNumEdit.SetValue(saved4)

            saved4 = self.slot4Inkwell
            saved5 = self.slot5Inkwell
            self.slot4Inkwell = saved5
            self.slot5Inkwell = saved4
            self.setInkwell4_UIState()
            self.setInkwell5_UIState()

            saved4 = self.slot4CB.Value
            saved5 = self.slot5CB.Value
            self.slot4CB.SetValue(saved5)
            self.slot5CB.SetValue(saved4)
            self.Slot5StartVialNumEdit.SetFocus()

    def OnSlot5ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot5"
            if not self.slot5Inkwell:
                self.slot5Inkwell = True
            else: 
                self.slot5Inkwell = False
            self.setInkwell5_UIState()
            self.Slot5InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved5=self.Slot5Choice.GetStringSelection()
            saved4=self.Slot4Choice.GetStringSelection()
            savedList=self.Slot5Choice.GetStrings()
            self.Slot5Choice.Clear()
            self.Slot4Choice.Clear()
            self.Slot5Choice.AppendItems(savedList)
            self.Slot4Choice.AppendItems(savedList)
            self.Slot5Choice.SetStringSelection(saved4)
            self.Slot4Choice.SetStringSelection(saved5)

            saved5 = self.Slot5EndVialNumEdit.Value
            saved4 = self.Slot4EndVialNumEdit.Value
            self.Slot5EndVialNumEdit.SetValue(saved4)
            self.Slot4EndVialNumEdit.SetValue(saved5)

            saved5 = self.Slot5InjPerVialNumEdit.Value
            saved4 = self.Slot4InjPerVialNumEdit.Value
            self.Slot5InjPerVialNumEdit.SetValue(saved4)
            self.Slot4InjPerVialNumEdit.SetValue(saved5)

            saved5 = self.Slot5StartVialNumEdit.Value
            saved4 = self.Slot4StartVialNumEdit.Value
            self.Slot5StartVialNumEdit.SetValue(saved4)
            self.Slot4StartVialNumEdit.SetValue(saved5)

            saved4 = self.Slot4TrayNumEdit.Value
            saved5 = self.Slot5TrayNumEdit.Value
            self.Slot4TrayNumEdit.SetValue(saved5)
            self.Slot5TrayNumEdit.SetValue(saved4)

            saved4 = self.slot4Inkwell
            saved5 = self.slot5Inkwell
            self.slot4Inkwell = saved5
            self.slot5Inkwell = saved4
            self.setInkwell4_UIState()
            self.setInkwell5_UIState()

            saved5 = self.slot5CB.Value
            saved4 = self.slot4CB.Value
            self.slot5CB.SetValue(saved4)
            self.slot4CB.SetValue(saved5)
            self.Slot4StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved5=self.Slot5Choice.GetStringSelection()
            saved6=self.Slot6Choice.GetStringSelection()
            savedList=self.Slot5Choice.GetStrings()
            self.Slot5Choice.Clear()
            self.Slot6Choice.Clear()
            self.Slot5Choice.AppendItems(savedList)
            self.Slot6Choice.AppendItems(savedList)
            self.Slot5Choice.SetStringSelection(saved6)
            self.Slot6Choice.SetStringSelection(saved5)

            saved5 = self.Slot5EndVialNumEdit.Value
            saved6 = self.Slot6EndVialNumEdit.Value
            self.Slot5EndVialNumEdit.SetValue(saved6)
            self.Slot6EndVialNumEdit.SetValue(saved5)

            saved5 = self.Slot5InjPerVialNumEdit.Value
            saved6 = self.Slot6InjPerVialNumEdit.Value
            self.Slot5InjPerVialNumEdit.SetValue(saved6)
            self.Slot6InjPerVialNumEdit.SetValue(saved5)

            saved5 = self.Slot5StartVialNumEdit.Value
            saved6 = self.Slot6StartVialNumEdit.Value
            self.Slot5StartVialNumEdit.SetValue(saved6)
            self.Slot6StartVialNumEdit.SetValue(saved5)

            saved5 = self.Slot5TrayNumEdit.Value
            saved6 = self.Slot6TrayNumEdit.Value
            self.Slot5TrayNumEdit.SetValue(saved6)
            self.Slot6TrayNumEdit.SetValue(saved5)

            saved5 = self.slot5Inkwell
            saved6 = self.slot6Inkwell
            self.slot5Inkwell = saved6
            self.slot6Inkwell = saved5
            self.setInkwell5_UIState()
            self.setInkwell6_UIState()

            saved5 = self.slot5CB.Value
            saved6 = self.slot6CB.Value
            self.slot5CB.SetValue(saved6)
            self.slot6CB.SetValue(saved5)
            self.Slot6StartVialNumEdit.SetFocus()

    def OnSlot6ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot6"
            if not self.slot6Inkwell:
                self.slot6Inkwell = True
            else: 
                self.slot6Inkwell = False
            self.setInkwell6_UIState()
            self.Slot6InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved6=self.Slot6Choice.GetStringSelection()
            saved5=self.Slot5Choice.GetStringSelection()
            savedList=self.Slot6Choice.GetStrings()
            self.Slot6Choice.Clear()
            self.Slot5Choice.Clear()
            self.Slot6Choice.AppendItems(savedList)
            self.Slot5Choice.AppendItems(savedList)
            self.Slot6Choice.SetStringSelection(saved5)
            self.Slot5Choice.SetStringSelection(saved6)

            saved6 = self.Slot6EndVialNumEdit.Value
            saved5 = self.Slot5EndVialNumEdit.Value
            self.Slot6EndVialNumEdit.SetValue(saved5)
            self.Slot5EndVialNumEdit.SetValue(saved6)

            saved6 = self.Slot6InjPerVialNumEdit.Value
            saved5 = self.Slot5InjPerVialNumEdit.Value
            self.Slot6InjPerVialNumEdit.SetValue(saved5)
            self.Slot5InjPerVialNumEdit.SetValue(saved6)

            saved6 = self.Slot6StartVialNumEdit.Value
            saved5 = self.Slot5StartVialNumEdit.Value
            self.Slot6StartVialNumEdit.SetValue(saved5)
            self.Slot5StartVialNumEdit.SetValue(saved6)

            saved5 = self.Slot5TrayNumEdit.Value
            saved6 = self.Slot6TrayNumEdit.Value
            self.Slot5TrayNumEdit.SetValue(saved6)
            self.Slot6TrayNumEdit.SetValue(saved5)

            saved5 = self.slot5Inkwell
            saved6 = self.slot6Inkwell
            self.slot5Inkwell = saved6
            self.slot6Inkwell = saved5
            self.setInkwell5_UIState()
            self.setInkwell6_UIState()

            saved6 = self.slot6CB.Value
            saved5 = self.slot5CB.Value
            self.slot6CB.SetValue(saved5)
            self.slot5CB.SetValue(saved6)
            self.Slot5StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved6=self.Slot6Choice.GetStringSelection()
            saved7=self.Slot7Choice.GetStringSelection()
            savedList=self.Slot6Choice.GetStrings()
            self.Slot6Choice.Clear()
            self.Slot7Choice.Clear()
            self.Slot6Choice.AppendItems(savedList)
            self.Slot7Choice.AppendItems(savedList)
            self.Slot6Choice.SetStringSelection(saved7)
            self.Slot7Choice.SetStringSelection(saved6)

            saved6 = self.Slot6EndVialNumEdit.Value
            saved7 = self.Slot7EndVialNumEdit.Value
            self.Slot6EndVialNumEdit.SetValue(saved7)
            self.Slot7EndVialNumEdit.SetValue(saved6)

            saved6 = self.Slot6InjPerVialNumEdit.Value
            saved7 = self.Slot7InjPerVialNumEdit.Value
            self.Slot6InjPerVialNumEdit.SetValue(saved7)
            self.Slot7InjPerVialNumEdit.SetValue(saved6)

            saved6 = self.Slot6StartVialNumEdit.Value
            saved7 = self.Slot7StartVialNumEdit.Value
            self.Slot6StartVialNumEdit.SetValue(saved7)
            self.Slot7StartVialNumEdit.SetValue(saved6)

            saved6 = self.Slot6TrayNumEdit.Value
            saved7 = self.Slot7TrayNumEdit.Value
            self.Slot6TrayNumEdit.SetValue(saved7)
            self.Slot7TrayNumEdit.SetValue(saved6)

            saved6 = self.slot6Inkwell
            saved7 = self.slot7Inkwell
            self.slot6Inkwell = saved7
            self.slot7Inkwell = saved6
            self.setInkwell6_UIState()
            self.setInkwell7_UIState()

            saved6 = self.slot6CB.Value
            saved7 = self.slot7CB.Value
            self.slot6CB.SetValue(saved7)
            self.slot7CB.SetValue(saved6)
            self.Slot7StartVialNumEdit.SetFocus()

    def OnSlot7ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot7"
            if not self.slot7Inkwell:
                self.slot7Inkwell = True
            else: 
                self.slot7Inkwell = False
            self.setInkwell7_UIState()
            self.Slot7InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved7=self.Slot7Choice.GetStringSelection()
            saved6=self.Slot6Choice.GetStringSelection()
            savedList=self.Slot7Choice.GetStrings()
            self.Slot7Choice.Clear()
            self.Slot6Choice.Clear()
            self.Slot7Choice.AppendItems(savedList)
            self.Slot6Choice.AppendItems(savedList)
            self.Slot7Choice.SetStringSelection(saved6)
            self.Slot6Choice.SetStringSelection(saved7)

            saved7 = self.Slot7EndVialNumEdit.Value
            saved6 = self.Slot6EndVialNumEdit.Value
            self.Slot7EndVialNumEdit.SetValue(saved6)
            self.Slot6EndVialNumEdit.SetValue(saved7)

            saved7 = self.Slot7InjPerVialNumEdit.Value
            saved6 = self.Slot6InjPerVialNumEdit.Value
            self.Slot7InjPerVialNumEdit.SetValue(saved6)
            self.Slot6InjPerVialNumEdit.SetValue(saved7)

            saved7 = self.Slot7StartVialNumEdit.Value
            saved6 = self.Slot6StartVialNumEdit.Value
            self.Slot7StartVialNumEdit.SetValue(saved6)
            self.Slot6StartVialNumEdit.SetValue(saved7)

            saved6 = self.Slot6TrayNumEdit.Value
            saved7 = self.Slot7TrayNumEdit.Value
            self.Slot6TrayNumEdit.SetValue(saved7)
            self.Slot7TrayNumEdit.SetValue(saved6)

            saved6 = self.slot6Inkwell
            saved7 = self.slot7Inkwell
            self.slot6Inkwell = saved7
            self.slot7Inkwell = saved6
            self.setInkwell6_UIState()
            self.setInkwell7_UIState()

            saved7 = self.slot7CB.Value
            saved6 = self.slot6CB.Value
            self.slot7CB.SetValue(saved6)
            self.slot6CB.SetValue(saved7)
            self.Slot6StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved7=self.Slot7Choice.GetStringSelection()
            saved8=self.Slot8Choice.GetStringSelection()
            savedList=self.Slot7Choice.GetStrings()
            self.Slot7Choice.Clear()
            self.Slot8Choice.Clear()
            self.Slot7Choice.AppendItems(savedList)
            self.Slot8Choice.AppendItems(savedList)
            self.Slot7Choice.SetStringSelection(saved8)
            self.Slot8Choice.SetStringSelection(saved7)

            saved7 = self.Slot7EndVialNumEdit.Value
            saved8 = self.Slot8EndVialNumEdit.Value
            self.Slot7EndVialNumEdit.SetValue(saved8)
            self.Slot8EndVialNumEdit.SetValue(saved7)

            saved7 = self.Slot7InjPerVialNumEdit.Value
            saved8 = self.Slot8InjPerVialNumEdit.Value
            self.Slot7InjPerVialNumEdit.SetValue(saved8)
            self.Slot8InjPerVialNumEdit.SetValue(saved7)

            saved7 = self.Slot7StartVialNumEdit.Value
            saved8 = self.Slot8StartVialNumEdit.Value
            self.Slot7StartVialNumEdit.SetValue(saved8)
            self.Slot8StartVialNumEdit.SetValue(saved7)

            saved7 = self.Slot7TrayNumEdit.Value
            saved8 = self.Slot8TrayNumEdit.Value
            self.Slot7TrayNumEdit.SetValue(saved8)
            self.Slot8TrayNumEdit.SetValue(saved7)

            saved7 = self.slot7Inkwell
            saved8 = self.slot8Inkwell
            self.slot7Inkwell = saved8
            self.slot8Inkwell = saved7
            self.setInkwell7_UIState()
            self.setInkwell8_UIState()

            saved7 = self.slot7CB.Value
            saved8 = self.slot8CB.Value
            self.slot7CB.SetValue(saved8)
            self.slot8CB.SetValue(saved7)
            self.Slot8StartVialNumEdit.SetFocus()

    def OnSlot8ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot8"
            if not self.slot8Inkwell:
                self.slot8Inkwell = True
            else: 
                self.slot8Inkwell = False
            self.setInkwell8_UIState()
            self.Slot8InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved8=self.Slot8Choice.GetStringSelection()
            saved7=self.Slot7Choice.GetStringSelection()
            savedList=self.Slot8Choice.GetStrings()
            self.Slot8Choice.Clear()
            self.Slot7Choice.Clear()
            self.Slot8Choice.AppendItems(savedList)
            self.Slot7Choice.AppendItems(savedList)
            self.Slot8Choice.SetStringSelection(saved7)
            self.Slot7Choice.SetStringSelection(saved8)

            saved8 = self.Slot8EndVialNumEdit.Value
            saved7 = self.Slot7EndVialNumEdit.Value
            self.Slot8EndVialNumEdit.SetValue(saved7)
            self.Slot7EndVialNumEdit.SetValue(saved8)

            saved8 = self.Slot8InjPerVialNumEdit.Value
            saved7 = self.Slot7InjPerVialNumEdit.Value
            self.Slot8InjPerVialNumEdit.SetValue(saved7)
            self.Slot7InjPerVialNumEdit.SetValue(saved8)

            saved8 = self.Slot8StartVialNumEdit.Value
            saved7 = self.Slot7StartVialNumEdit.Value
            self.Slot8StartVialNumEdit.SetValue(saved7)
            self.Slot7StartVialNumEdit.SetValue(saved8)

            saved7 = self.Slot7TrayNumEdit.Value
            saved8 = self.Slot8TrayNumEdit.Value
            self.Slot7TrayNumEdit.SetValue(saved8)
            self.Slot8TrayNumEdit.SetValue(saved7)

            saved7 = self.slot7Inkwell
            saved8 = self.slot8Inkwell
            self.slot7Inkwell = saved8
            self.slot8Inkwell = saved7
            self.setInkwell7_UIState()
            self.setInkwell8_UIState()

            saved8 = self.slot8CB.Value
            saved7 = self.slot7CB.Value
            self.slot8CB.SetValue(saved7)
            self.slot7CB.SetValue(saved8)
            self.Slot7StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved8=self.Slot8Choice.GetStringSelection()
            saved9=self.Slot9Choice.GetStringSelection()
            savedList=self.Slot8Choice.GetStrings()
            self.Slot8Choice.Clear()
            self.Slot9Choice.Clear()
            self.Slot8Choice.AppendItems(savedList)
            self.Slot9Choice.AppendItems(savedList)
            self.Slot8Choice.SetStringSelection(saved9)
            self.Slot9Choice.SetStringSelection(saved8)

            saved8 = self.Slot8EndVialNumEdit.Value
            saved9 = self.Slot9EndVialNumEdit.Value
            self.Slot8EndVialNumEdit.SetValue(saved9)
            self.Slot9EndVialNumEdit.SetValue(saved8)

            saved8 = self.Slot8InjPerVialNumEdit.Value
            saved9 = self.Slot9InjPerVialNumEdit.Value
            self.Slot8InjPerVialNumEdit.SetValue(saved9)
            self.Slot9InjPerVialNumEdit.SetValue(saved8)

            saved8 = self.Slot8StartVialNumEdit.Value
            saved9 = self.Slot9StartVialNumEdit.Value
            self.Slot8StartVialNumEdit.SetValue(saved9)
            self.Slot9StartVialNumEdit.SetValue(saved8)

            saved8 = self.Slot8TrayNumEdit.Value
            saved9 = self.Slot9TrayNumEdit.Value
            self.Slot8TrayNumEdit.SetValue(saved9)
            self.Slot9TrayNumEdit.SetValue(saved8)

            saved8 = self.slot8Inkwell
            saved9 = self.slot9Inkwell
            self.slot8Inkwell = saved9
            self.slot9Inkwell = saved8
            self.setInkwell8_UIState()
            self.setInkwell9_UIState()

            saved8 = self.slot8CB.Value
            saved9 = self.slot9CB.Value
            self.slot8CB.SetValue(saved9)
            self.slot9CB.SetValue(saved8)
            self.Slot9StartVialNumEdit.SetFocus()

    def OnSlot9ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot9"
            if not self.slot9Inkwell:
                self.slot9Inkwell = True
            else: 
                self.slot9Inkwell = False
            self.setInkwell9_UIState()
            self.Slot9InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved9=self.Slot9Choice.GetStringSelection()
            saved8=self.Slot8Choice.GetStringSelection()
            savedList=self.Slot9Choice.GetStrings()
            self.Slot9Choice.Clear()
            self.Slot8Choice.Clear()
            self.Slot9Choice.AppendItems(savedList)
            self.Slot8Choice.AppendItems(savedList)
            self.Slot9Choice.SetStringSelection(saved8)
            self.Slot8Choice.SetStringSelection(saved9)

            saved9 = self.Slot9EndVialNumEdit.Value
            saved8 = self.Slot8EndVialNumEdit.Value
            self.Slot9EndVialNumEdit.SetValue(saved8)
            self.Slot8EndVialNumEdit.SetValue(saved9)

            saved9 = self.Slot9InjPerVialNumEdit.Value
            saved8 = self.Slot8InjPerVialNumEdit.Value
            self.Slot9InjPerVialNumEdit.SetValue(saved8)
            self.Slot8InjPerVialNumEdit.SetValue(saved9)

            saved9 = self.Slot9StartVialNumEdit.Value
            saved8 = self.Slot8StartVialNumEdit.Value
            self.Slot9StartVialNumEdit.SetValue(saved8)
            self.Slot8StartVialNumEdit.SetValue(saved9)

            saved8 = self.Slot8TrayNumEdit.Value
            saved9 = self.Slot9TrayNumEdit.Value
            self.Slot8TrayNumEdit.SetValue(saved9)
            self.Slot9TrayNumEdit.SetValue(saved8)

            saved8 = self.slot8Inkwell
            saved9 = self.slot9Inkwell
            self.slot8Inkwell = saved9
            self.slot9Inkwell = saved8
            self.setInkwell8_UIState()
            self.setInkwell9_UIState()

            saved9 = self.slot9CB.Value
            saved8 = self.slot8CB.Value
            self.slot9CB.SetValue(saved8)
            self.slot8CB.SetValue(saved9)
            self.Slot8StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key!"
            saved9=self.Slot9Choice.GetStringSelection()
            saved10=self.Slot10Choice.GetStringSelection()
            savedList=self.Slot9Choice.GetStrings()
            self.Slot9Choice.Clear()
            self.Slot10Choice.Clear()
            self.Slot9Choice.AppendItems(savedList)
            self.Slot10Choice.AppendItems(savedList)
            self.Slot9Choice.SetStringSelection(saved10)
            self.Slot10Choice.SetStringSelection(saved9)

            saved9 = self.Slot9EndVialNumEdit.Value
            saved10 = self.Slot10EndVialNumEdit.Value
            self.Slot9EndVialNumEdit.SetValue(saved10)
            self.Slot10EndVialNumEdit.SetValue(saved9)

            saved9 = self.Slot9InjPerVialNumEdit.Value
            saved10 = self.Slot10InjPerVialNumEdit.Value
            self.Slot9InjPerVialNumEdit.SetValue(saved10)
            self.Slot10InjPerVialNumEdit.SetValue(saved9)

            saved9 = self.Slot9StartVialNumEdit.Value
            saved10 = self.Slot10StartVialNumEdit.Value
            self.Slot9StartVialNumEdit.SetValue(saved10)
            self.Slot10StartVialNumEdit.SetValue(saved9)

            saved9 = self.Slot9TrayNumEdit.Value
            saved10 = self.Slot10TrayNumEdit.Value
            self.Slot9TrayNumEdit.SetValue(saved10)
            self.Slot10TrayNumEdit.SetValue(saved9)

            saved9 = self.slot9Inkwell
            saved10 = self.slot10Inkwell
            self.slot9Inkwell = saved10
            self.slot10Inkwell = saved9
            self.setInkwell9_UIState()
            self.setInkwell10_UIState()

            saved9 = self.slot9CB.Value
            saved10 = self.slot10CB.Value
            self.slot9CB.SetValue(saved10)
            self.slot10CB.SetValue(saved9)
            self.Slot10StartVialNumEdit.SetFocus()

    def OnSlot10ChoiceKeyPress(self, event):
        keycode = event.GetKeyCode()
        print keycode
        controlDown = event.CmdDown()
        if controlDown and (keycode == 73):
            print "Toggle Inkwell on Slot10"
            if not self.slot10Inkwell:
                self.slot10Inkwell = True
            else: 
                self.slot10Inkwell = False
            self.setInkwell10_UIState()
            self.Slot10InjPerVialNumEdit.SetFocus()
        if controlDown and (keycode == 390 or keycode == 45):
            print "you pressed the Up Key!"
            saved10=self.Slot10Choice.GetStringSelection()
            saved9=self.Slot9Choice.GetStringSelection()
            savedList=self.Slot10Choice.GetStrings()
            self.Slot10Choice.Clear()
            self.Slot9Choice.Clear()
            self.Slot10Choice.AppendItems(savedList)
            self.Slot9Choice.AppendItems(savedList)
            self.Slot10Choice.SetStringSelection(saved9)
            self.Slot9Choice.SetStringSelection(saved10)

            saved10 = self.Slot10EndVialNumEdit.Value
            saved9 = self.Slot9EndVialNumEdit.Value
            self.Slot10EndVialNumEdit.SetValue(saved9)
            self.Slot9EndVialNumEdit.SetValue(saved10)

            saved10 = self.Slot10InjPerVialNumEdit.Value
            saved9 = self.Slot9InjPerVialNumEdit.Value
            self.Slot10InjPerVialNumEdit.SetValue(saved9)
            self.Slot9InjPerVialNumEdit.SetValue(saved10)

            saved10 = self.Slot10StartVialNumEdit.Value
            saved9 = self.Slot9StartVialNumEdit.Value
            self.Slot10StartVialNumEdit.SetValue(saved9)
            self.Slot9StartVialNumEdit.SetValue(saved10)

            saved9 = self.Slot9TrayNumEdit.Value
            saved10 = self.Slot10TrayNumEdit.Value
            self.Slot9TrayNumEdit.SetValue(saved10)
            self.Slot10TrayNumEdit.SetValue(saved9)

            saved9 = self.slot9Inkwell
            saved10 = self.slot10Inkwell
            self.slot9Inkwell = saved10
            self.slot10Inkwell = saved9
            self.setInkwell9_UIState()
            self.setInkwell10_UIState()

            saved10 = self.slot10CB.Value
            saved9 = self.slot9CB.Value
            self.slot10CB.SetValue(saved9)
            self.slot9CB.SetValue(saved10)
            self.Slot9StartVialNumEdit.SetFocus()
        if controlDown and (keycode == 388 or keycode == 43):
            print "you pressed the Down Key, Nothing to do"

    def run(self):
        pass

HELP_STRING = \
"""
Autosampler.py [-h] [-c <AUTOSAMPLER FILENAME> -s <AUTOSAMPLER STATE FILENAME> -t <TD FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a Autosampler config file.
-s         : Specify a Autosampler State config file.
-t         : Specify a TD file after training the autosampler.
"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:s:t:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME
    stateFile = os.path.dirname(AppPath) + "/" + DEFAULT_STATE_CONFIG_NAME
    tdFile = os.path.dirname(AppPath) + "/" + DEFAULT_TD_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Autosampler config file specified at command line: %s" % configFile
        
    if "-s" in options:
        stateFile = options["-s"]
        print "Autosampler State config file specified at command line: %s" % stateFile
        
    if "-t" in options:
        tdFile = options["-t"]
        print "Autosampler Training file specified at command line: %s" % tdFile
        
    return (configFile, stateFile, tdFile)
    
if __name__ == "__main__":
    (configFile, stateFile, tdFile) = HandleCommandSwitches()
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = AutosamplerFrame(configFile, stateFile, tdFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
