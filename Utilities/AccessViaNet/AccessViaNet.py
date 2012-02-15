"""
File Name: AccessViaNet.py
Purpose: This is responsible for network communications to an analyzer
         It supports several external commands via TCP or UDP. 
         N.B. These MUST be terminated using a "\n" before they are obeyed.
         
         DRIVER   - Send command to driver
         SYNC     - Resynchronize clock
         STANDBY  - Shut down but keep driver operating
         STOP     - Shut down and stop driver
         RESTART  - Restart analyzer
         REBOOT   - Hard reset analyzer by cycling power followed by restart
         SHUTDOWN - Shut down analyzer and computer

File History:
    11-09-05 sze   Initial release
    
Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

APP_NAME = "AccessViaNet"
APP_DESCRIPTION = "Communication with an Analyzer via Network"
__version__ = 1.0

import asynchat
import asyncore
import datetime
import getopt
import os
import Pyro.errors

from Queue import Queue
import socket
import subprocess
import sys
import time
import traceback
import types
import win32process

from Host.autogen import interface
from Host.Common import Listener, CmdFIFO
from Host.Common.configobj import ConfigObj
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import Singleton, BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_SENSORSTREAM
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_SUPERVISOR
from Host.Common.SingleInstance import SingleInstance
from Host.Common.StringPickler import ArbitraryObject
from Host.Common.timestamp import getTimestamp, timestampToUtcDatetime, unixTime

EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

_TIME1970 = 2208988800L      # Thanks to F.Lundh
_data = '\x1b' + 47*'\0'

#typedef struct _SYSTEMTIME {  // st
#    WORD wYear;
#    WORD wMonth;
#    WORD wDayOfWeek;
#    WORD wDay;
#    WORD wHour;
#    WORD wMinute;
#    WORD wSecond;
#    WORD wMilliseconds;
#} SYSTEMTIME;
#VOID GetSystemTime(
#  LPSYSTEMTIME lpSystemTime   // address of system time structure
#);
#SYSTEMTIME st;
#GetSystemTime(&st);
#SetSystemTime(&st);

from struct import pack, unpack
from ctypes import windll, Structure, c_ushort, byref, c_ulong, c_long
kernel32_GetSystemTime = windll.kernel32.GetSystemTime
kernel32_SetSystemTime = windll.kernel32.SetSystemTime
kernel32_SystemTimeToFileTime=windll.kernel32.SystemTimeToFileTime
kernel32_FileTimeToSystemTime=windll.kernel32.FileTimeToSystemTime

class SYSTEMTIME(Structure):
    _fields_ =  (
                ('wYear', c_ushort),
                ('wMonth', c_ushort),
                ('wDayOfWeek', c_ushort),
                ('wDay', c_ushort),
                ('wHour', c_ushort),

                ('wMinute', c_ushort),
                ('wSecond', c_ushort),
                ('wMilliseconds', c_ushort),
                )
    def __str__(self):
        return '%4d%02d%02d%02d%02d%02d.%03d' % (self.wYear,self.wMonth,self.wDay,self.wHour,self.wMinute,self.wSecond,self.wMilliseconds)

class LONG_INTEGER(Structure):
    _fields_ =  (
            ('low', c_ulong),
            ('high', c_long),
            )

def GetSystemTime():
    st = SYSTEMTIME(0,0,0,0,0,0,0,0)
    kernel32_GetSystemTime(byref(st))
    return st

def SetSystemTime(st):
    return kernel32_SetSystemTime(byref(st))

def GetSystemFileTime():
    ft = LONG_INTEGER(0,0)
    st = GetSystemTime()
    if kernel32_SystemTimeToFileTime(byref(st),byref(ft)):
        return (long(ft.high)<<32)|ft.low
    return None

def SetSystemFileTime(ft):
    st = SYSTEMTIME(0,0,0,0,0,0,0,0)
    ft = LONG_INTEGER(ft&0xFFFFFFFFL,ft>>32)
    r = kernel32_FileTimeToSystemTime(byref(ft),byref(st))
    if r: SetSystemTime(st)
    return r

def _L2U32(L):
    return unpack('l',pack('L',L))[0]

_UTIME1970 = _L2U32(_TIME1970)
def _time2ntp(t):
    s = int(t)
    return pack('!II',s+_UTIME1970,_L2U32((t-s)*0x100000000L))

def _ntp2time((s,f)):
    return s-_TIME1970+float((f>>4)&0xfffffff)/0x10000000

def sntp_time(server):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        #originate timestamp 6:8
        #receive timestamp   8:10
        #transmit timestamp 10:12
        t1 = time.time()
        s.sendto(_data, (server,123))
        data, address = s.recvfrom(1024)
        data = unpack('!12I', data)
        t4 = time.time()
        t2 = _ntp2time(data[8:10])
        t3 = _ntp2time(data[10:12])
        delay = (t4 - t1) - (t2 - t3)
        offset = ((t2 - t1) + (t3 - t4)) / 2.
        return address[0], delay, offset
    except:
        # 
        return 3*(None,)

def inRange(value,optimal,tolerance):
    return abs(value - optimal) <= tolerance
    
class AnalyzerStatus(object):
    # Determine the analyzer status based upon which subsystems are reporting. At the lowest
    #  level, only the host computer is operational. When the driver is operating, sensor data
    #  are reported, and when concentrations are being determined, the data manager is active.
    HOST_ONLY = 1
    SENSORS_ACTIVE = 2
    DATA_ACTIVE = 3
    #
    READY  = 1
    SENSOR = 2
    DATA   = 4
    #
    def __init__(self):
        self.level = AnalyzerStatus.HOST_ONLY
        self.sensorsWithoutData = 0
        self.heartBeatWithoutSensors = 0
        self.status = self.READY
    def receivedData(self,data):
        self.sensorsWithoutData = 0
        self.heartBeatWithoutSensors = 0
        self.level = AnalyzerStatus.DATA_ACTIVE
        state = {
            AnalyzerStatus.DATA     : True,
            AnalyzerStatus.SENSOR   : False,
            }
        mask = sum(state.keys())
        value = sum([k for k in state if state[k]])
        self.status = (self.status & ~mask) | value
    def receivedSensors(self,sensors):
        self.sensorsWithoutData += 1
        self.heartBeatWithoutSensors = 0
        if (self.level>AnalyzerStatus.SENSORS_ACTIVE) and (self.sensorsWithoutData<2): 
            return
        self.level = AnalyzerStatus.SENSORS_ACTIVE
        state = {
            AnalyzerStatus.DATA     : False,
            AnalyzerStatus.SENSOR   : True,
            }
        mask = sum(state.keys())
        value = sum([k for k in state if state[k]])
        self.status = (self.status & ~mask) | value
    def receivedHeartbeat(self):
        self.heartBeatWithoutSensors += 1
        if (self.level>AnalyzerStatus.HOST_ONLY) and (self.heartBeatWithoutSensors<6): 
            return
        self.level = AnalyzerStatus.HOST_ONLY
        self.status = self.READY
    def getLevel(self):
        return self.level
    def getStatus(self):
        return self.status

class AnalyzerControl(Singleton):
    initialized = False
    def __init__(self,config=None):
        if not self.initialized:
            self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                                        APP_NAME,
                                                        IsDontCareConnection = False)
            self.driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                                        APP_NAME,
                                                        IsDontCareConnection = False)
            if config is not None:
                # Set up directory paths
                try:
                    self.launchType = config["Main"]["Type"].strip().lower()
                except:
                    self.launchType = "exe"
                try:
                    self.consoleMode = int(config["Main"]["ConsoleMode"])
                except:
                    self.consoleMode = 2
                apacheDir = config["Main"]["APACHEDir"].strip()
                self.supervisorIniDir = os.path.join(apacheDir, "AppConfig\Config\Supervisor")
                try:
                    hostDir = config["Main"]["HostDir"].strip()
                except:
                    hostDir = "Host"
                self.supervisorHostDir = os.path.join(apacheDir, hostDir)
                self.startupSupervisorIni = os.path.join(self.supervisorIniDir,
                                            config["Main"]["StartupSupervisorIni"].strip())
                self.supervisorIni = self.startupSupervisorIni
                self.syncClock = "NTP" in config
                updateClock = False
                self.ntpServers = []
                if self.syncClock:
                    # Compile list of servers
                    for option in config['NTP']:
                        if option[:6].upper() == "SERVER":
                            try:
                                index = int(option[6:])
                                self.ntpServers.append(config['NTP'][option])
                            except ValueError:
                                print "Unrecognized option %s ignored" % (option,)
                        elif option.upper() == "UPDATECLOCK":
                            updateClock = bool(int(config['NTP'][option]))
                    print "NTP servers", self.ntpServers
                    print "Update clock", updateClock
                    try:
                        print self.syncTime(updateClock)
                    except:
                        print traceback.format_exc()
            else:
                raise ValueError("Missing configuration file when initializing AnalyzerControl")
            self.initialized = True

    def killUncontrolled(self):
        # Kill the startup splash screen as well (if it exists)
        os.system(r'taskkill.exe /IM HostStartup.exe /F')
        # Kill QuickGui if it isn't under Supervisor's supervision
        os.system(r'taskkill.exe /IM QuickGui.exe /F')
        # Kill Controller if it isn't under Supervisor's supervision
        os.system(r'taskkill.exe /IM Controller.exe /F')

    def doDriverRpc(self,args):
        expr = "self.driver." + args
        return "%s" % (eval(expr),)
    
    def syncTime(self,updateClock=True):
        response = []
        if not self.syncClock: return "\n".join(response)
        t0 = time.time()
        mu = 0
        ss = 0
        n = 0
        data = []
        for server in self.ntpServers:
            address, delay, offset = sntp_time(server)
            if address:
                n += 1
                data.append((server, address, delay, offset))
        # Find statistics of offsets
        for (server, address, delay, offset) in data:
            response.append('%s: delay = %.3f offset = %.3f' % (server,delay,offset))
            mu += offset
            ss += offset*offset
        if n:
            mu = mu/n
            ss = (ss/n - mu*mu)**0.5
            # Find median
            med = sorted([offset for (server, address, delay, offset) in data])
            if n & 1:
                med = med[(n-1)//2]
            else:
                med = 0.5*(med[n//2-1] + med[n//2])
            response.append("Median clock offset = %.3f s (Mean = %.3f s, Sdev = %.3f s)" % (med,mu,ss))
            if updateClock:
                r = SetSystemFileTime(GetSystemFileTime()+long(med*10000000L))   #100 nanosecond units (since 16010101)
                response.append("Clock adjustment %s" % (r and 'carried out' or 'failed'))
            else:
                response.append("Clock adjustment has been disabled")
        else:
            response.append("No timeservers available")
        return "\n".join(response)
    
    def help(self):
        usage = []
        usage.append("Available commands:")
        usage.append("DRIVER   - Execute remote procedure call on driver")
        usage.append("REBOOT   - Shuts down, power cycles and reboots analyzer")
        usage.append("RESTART  - Restarts analyzer (when in STANDBY or STOP)")
        usage.append("SHUTDOWN - Turns off analyzer computer (CANNOT BE RESTARTED)")
        usage.append("STANDBY  - Closes valves, stops measurement, but leaves analyzer driver running")
        usage.append("STOP     - Stops measurement and analyzer control loops")
        return "\n".join(usage)
        
    def standby(self):
        self.killUncontrolled()
        self.supervisor.TerminateApplications(False, False)
        # Kill supervisor by PID if it does not stop within 20 seconds
        try:
            for k in range(10):
                p = CRDS_Supervisor.CmdFIFO.GetProcessID()
                if p == pid: time.sleep(2.0)
            os.system(r'taskkill /F /PID %d' % pid)
        except:
            time.sleep(2.0)
        # Close down sample handling
        self.driver.wrDasReg("VALVE_CNTRL_STATE_REGISTER","VALVE_CNTRL_DisabledState")
        return "OK"
        
    def stop(self):
        self.killUncontrolled()
        try:
            self.supervisor.TerminateApplications(False, True)
            status = 'OK'
        except Pyro.errors.ProtocolError:
            status = "Supervisor not active. Stopping driver only."
            self.driver.CmdFIFO.StopServer()
        return status
        
    def shutdown(self):
        self.killUncontrolled()
        try:
            self.supervisor.TerminateApplications(True, True)
            status = 'OK'
        except Pyro.errors.ProtocolError:
            status = "Supervisor not active. Shutting down windows."
            os.system("shutdown -s -t 20")
        return status
        
    def reboot(self):
        self.killUncontrolled()
        os.chdir(self.supervisorHostDir)
        os.system("ResetAnalyzer.exe")
        return "OK"

    def restart(self):
        try:
            if self.supervisor.CmdFIFO.PingDispatcher() == "Ping OK":
                pid = self.supervisor.CmdFIFO.GetProcessID()
                self.killUncontrolled()
                self.supervisor.TerminateApplications(False, False)
                # Kill supervisor by PID if it does not stop within 20 seconds
                try:
                    for k in range(10):
                        p = CRDS_Supervisor.CmdFIFO.GetProcessID()
                        if p == pid: time.sleep(2.0)
                    os.system(r'taskkill /F /PID %d' % pid)
                except:
                    time.sleep(2.0)
        except:
            pass
        time.sleep(5.0)        
        
        os.chdir(self.supervisorHostDir)
        info = subprocess.STARTUPINFO()
        if self.consoleMode != 1:
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
        dwCreationFlags = win32process.CREATE_NEW_CONSOLE
        print ["SupervisorLauncher.exe","-a","-c",AccessViaNet().launcherConfigFile]
        
        subprocess.Popen(["SupervisorLauncher.exe","-a","-c",AccessViaNet().launcherConfigFile], startupinfo=info, creationflags=dwCreationFlags)

        #if self.launchType == "exe":
        #    subprocess.Popen(["supervisor.exe","-c",self.supervisorIni], startupinfo=info, creationflags=dwCreationFlags)
        #else:
        #    subprocess.Popen(["python.exe", "Supervisor.py","-c",self.supervisorIni], startupinfo=info, creationflags=dwCreationFlags)

        # Launch HostStartup
        #if self.launchType == "exe":
        #    info = subprocess.STARTUPINFO()
        #    subprocess.Popen(["HostStartup.exe","-c",self.supervisorIni], startupinfo=info)
        return 'OK'
                                        
class TcpServer(asyncore.dispatcher):
    """Receives connections and establishes handlers for each client.
    """
    def __init__(self, address,target,welcome=''):
        asyncore.dispatcher.__init__(self)
        self.handlers = []
        self.target = target
        self.welcome = welcome
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(1)
        return
    def handle_accept(self):
        # Called when a client connects to our socket
        self.handlers[:] = [h for h in self.handlers if not h.closed]
        client_info = self.accept()
        if not self.handlers:
            self.handlers.append(TcpCmdHandler(client_info[0],self.target,self.welcome))
        else:
            GoAwayHandler(sock=client_info[0])
    def handle_close(self):
        self.close()
        return

class TcpMultiServer(asyncore.dispatcher):
    """Receives connections and establishes handlers for each client.
    """
    def __init__(self, address,target,welcome=''):
        asyncore.dispatcher.__init__(self)
        self.handlers = []
        self.target = target
        self.welcome = welcome
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(1)
        return
    def handle_accept(self):
        # Called when a client connects to our socket
        self.handlers[:] = [h for h in self.handlers if not h.closed]
        client_info = self.accept()
        self.handlers.append(TcpDataHandler(client_info[0],self.target,self.welcome))
    def handle_close(self):
        self.close()
        return
        
class UdpServer(asyncore.dispatcher):
    def __init__(self,address,target):
        asyncore.dispatcher.__init__(self)
        self.handler = CommandHandler(target)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind(address)
        self.closed = False
        self.peerAddress = None
        self.buffer = ""
        self.data_to_write = []
    def handle_read(self):
        """Read an incoming message from the client and put it into our outgoing queue."""
        data,self.peerAddress = self.recvfrom(2048)
        self.buffer += data
        while "\n" in self.buffer:
            where = self.buffer.find("\n")
            cmd = self.buffer[:where]
            self.buffer = self.buffer[where+1:]
            response = self.handler.doCommand(cmd)
            self.data_to_write.insert(0,response)
    def handle_close(self):
        self.closed = True
        self.close()
    def handle_connect(self):
        print "UDP connect", self.addr
    def writable(self):
        return bool(self.data_to_write)
    def handle_write(self):
        """Write as much as possible of the most recent message we have received."""
        data = self.data_to_write.pop()
        sent = self.sendto(data,self.peerAddress)
        if sent < len(data):
            remaining = data[sent:]
            self.data.to_write.append(remaining)
                
class GoAwayHandler(asynchat.async_chat):
    """Tell client to go away and close the connection"""
    def __init__(self,sock):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        self.push("Server busy with existing TCP connection\r\n")
        self.close_when_done()
    def collect_incoming_data(self,data):
        return
    def found_terminator(self):
        return
    def handle_close(self):
        self.close()
        return
    
class TcpCmdHandler(asynchat.async_chat):
    """Handles processing commands from a single client.
    """
    def __init__(self,sock,target,welcome):
        self.handler = CommandHandler(target)
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        if welcome: self.push("%s\r\n" % welcome)
        self.closed = False
        self.buffer = []
    def send_data(self,data):
        self.push(data)
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        cmd = "".join(self.buffer).strip()
        response = self.handler.doCommand(cmd)
        self.push(response)
        self.buffer = []
    def handle_close(self):
        self.closed = True
        self.close()        

class TcpDataHandler(asynchat.async_chat):
    """Handles sending data to a client.
    """
    def __init__(self,sock,target,welcome):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        if welcome: self.push("%s\r\n" % welcome)
        self.closed = False
        self.buffer = []
    def send_data(self,data):
        self.push(data)
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        self.buffer = []
    def handle_close(self):
        self.closed = True
        self.close()        
        
def tidy(line):
    """Handle backspace characters in line"""
    result = []
    for c in line:
        if ord(c) == 8 and result:
            result.pop()
        else:
            result.append(c)
    return "".join(result)
        
class CommandHandler(object):
    def __init__(self,target):
        self.target = target
        self.actions = dict(DRIVER   = self.target.doDriverRpc,
                            HELP     = self.target.help,
                            STANDBY  = self.target.standby, 
                            STOP     = self.target.stop,
                            RESTART  = self.target.restart,
                            REBOOT   = self.target.reboot,
                            SHUTDOWN = self.target.shutdown)
                   
    def doCommand(self,cmd):
        cmd = tidy(cmd.strip()).split(None,1)
        response = ""
        if len(cmd) > 0:
            c = cmd[0].upper()
            args = " ".join(cmd[1:])
            # Carry out the action
            try:
                if args:
                    response = self.actions[c](args=args).replace("\n","\r\n")
                else:
                    response = self.actions[c]().replace("\n","\r\n")
            except KeyError:
                response = "Unknown command: %s\r\n" % c
            except:
                response = traceback.format_exc().replace("\n","\r\n")
        return response + "\r\n> "
            
        
def format(fmtList,v):
    for t,f in fmtList:
        if isinstance(v,t): 
            try:
                return f % (v,)
            except TypeError:
                return f
    return '%s' % (v,)

MAX_SENSORS = 14
MAX_DATA = 14
    
class AccessViaNet(Singleton):
    initialized = False
    def __init__(self, configPath=None):        
        if not self.initialized:
            if configPath != None:
                # Read from .ini file
                self.config = ConfigObj(configPath)
                basePath = os.path.split(configPath)[0]
                self.launcherConfigFile = os.path.join(basePath,self.config['Main']['LauncherConfig'])
                self.statusHost, self.statusPort = self.config['Addresses']['Status'].split(':')
                self.statusPort = int(self.statusPort)
                self.statusSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                self.statusSocket.bind(('', 0))
                self.statusSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                self.id = self.config['InstrumentName']['Id']
                self.sensorQueue = Queue(512)
                self.sensorListener = Listener.Listener(self.sensorQueue,
                                                        BROADCAST_PORT_SENSORSTREAM,
                                                        interface.SensorEntryType,
                                                        retry = True,
                                                        name = "AccessViaNet listener")
                self.dmQueue = Queue(512)
                self.dmListener = Listener.Listener(self.dmQueue,
                                                    BROADCAST_PORT_DATA_MANAGER,
                                                    ArbitraryObject,
                                                    retry = True,
                                                    name = "AccessViaNet listener")
                self.tcpHost, self.tcpPort = self.config['Addresses']['TCPcontrol'].split(':')
                self.tcpPort = int(self.tcpPort)
                self.tcpDataHost, self.tcpDataPort = self.config['Addresses']['TCPdata'].split(':')
                self.tcpDataPort = int(self.tcpDataPort)
                self.udpHost, self.udpPort = self.config['Addresses']['UDPcontrol'].split(':')
                self.udpPort = int(self.udpPort)
                self.sensorPeriod = int(self.config['SensorReport']['Period'])
                self.heartBeatPeriod = 1000
                # Read list of sensor streams
                self.streamNames = MAX_SENSORS*[None]
                nmax = 0
                for k in self.config['SensorReport']:
                    if k.lower().startswith('sensor'):
                        num = int(k[6:])
                        if num>MAX_SENSORS or num<=0:
                            print "Invalid SENSOR number:", num
                        else:
                            nmax = max(nmax,num)
                            self.streamNames[num-1] = self.config['SensorReport'][k]
                self.streamNames = self.streamNames[:nmax]
                self.currentSensors = {}
                # Read list of data streams
                self.dataSource = self.config['DataReport']['Source']
                self.dataNames = MAX_DATA*[None]
                nmax = 0
                for k in self.config['DataReport']:
                    if k.lower().startswith('data'):
                        num = int(k[4:])
                        if num>MAX_DATA or num<=0:
                            print "Invalid DATA number:", num
                        else:
                            nmax = max(nmax,num)
                            self.dataNames[num-1] = self.config['DataReport'][k]
                self.dataNames = self.dataNames[:nmax]
            else:
                raise ValueError("Configuration file must be specified to initialize AccessViaNet network interface")
            self.initialized = True
        Log('AccessViaNet initialized',Data=dict(statusIP='%s:%d'%(self.statusHost,self.statusPort)))
        
    def sendPacket(self,data):
        try:
            self.statusSocket.sendto(data,('<broadcast>',self.statusPort))
        except:
            print traceback.format_exc()
        for h in self.tcpDataServer.handlers:
            if not h.closed:
                h.send_data(data)
        
    # Get data from sensor queue until some timestamp (from any stream) exceeds reportTime. 
    # If the queue becomes empty before this happens, return None
    # Otherwise, report latest values of sensor streams specified in streamNames as a 
    #  list of the same length as streamNames. This is a COPY of currentSensors so we can
    #  safely update currentSensors
    
    def getSensorData(self,reportTime):
        # Get all the data in the sensor queue up to reportTime and return all the current sensor
        #  values at that time. If the data in the sensor queue are all before reportTime, return None
        def getStreamName(streamNum):
            return interface.STREAM_MemberTypeDict[streamNum][7:]        
        d = None
        try:
            while not self.sensorQueue.empty():
                d = self.sensorQueue.get()
                if d.timestamp>reportTime:
                    return self.currentSensors.copy()   # Make a copy, since currentSensors is dynamically updated
                self.currentSensors[getStreamName(d.streamNum)] = d.value
            return None
        finally:
            if d is not None:
                self.currentSensors[getStreamName(d.streamNum)] = d.value

        
    def run(self):
        try:
            self.analyzerControl = AnalyzerControl(self.config)
            self.tcpServer = TcpServer((self.tcpHost,self.tcpPort),self.analyzerControl,"Connected to Picarro Control Server")
            self.tcpDataServer = TcpMultiServer((self.tcpDataHost,self.tcpDataPort),self.analyzerControl)
            self.udpServer = UdpServer((self.udpHost,self.udpPort),self.analyzerControl)
            self.analyzerStatus = AnalyzerStatus()
            count = 0
            # TODO: For actual code, set up startTs from actual time, rather than from timestamp in the file
            startTs = getTimestamp()
            #d = self.sensorQueue.get()
            #startTs = d.timestamp
            nextReport = self.sensorPeriod*((startTs + self.sensorPeriod)//self.sensorPeriod)
            nextHeartbeat = self.heartBeatPeriod*((startTs + self.heartBeatPeriod)//self.heartBeatPeriod)
            formatList = [(int,'%d'),(float,'%.5f'),(types.NoneType,'')]
            
            while True:
                asyncore.loop(timeout=0.1,count=1)
                # Get available data manager queue data
                nGet = 10
                while nGet>0 and not self.dmQueue.empty():
                    d = self.dmQueue.get()
                    nGet -= 1
                    ts, mode, source = d['data']['timestamp'], d['mode'], d['source']
                    if source == self.dataSource:
                        self.analyzerStatus.receivedData(d['data'])
                        uTime = unixTime(ts)
                        tsAsString = timestampToUtcDatetime(ts).strftime('%Y%m%dT%H%M%S') + '.%03d' % (ts % 1000,)
                        now = datetime.datetime.utcnow()
                        # tsAsString = now.strftime('%Y%m%dT%H%M%S') + '.%03d' % (now.microsecond/1000)
                        fields = [self.id]
                        fields.append(tsAsString)
                        fields.append('%d' % (self.analyzerStatus.getStatus(),))
                        fields += [format(formatList,d['data'].get(v,None)) for v in self.dataNames]
                        data = ','.join(fields)
                        self.sendPacket('%s\r\n' % data)
                # Get available sensor data
                sensors = self.getSensorData(nextReport)
                if sensors is not None:
                    self.analyzerStatus.receivedSensors(sensors)
                    selected = len(self.streamNames)*[None]
                    for name in self.streamNames:
                        if name in sensors:
                            selected[self.streamNames.index(name)] = sensors[name]
                    # We have sensor data that was current as of nextReport
                    fields = [self.id]
                    uTime = unixTime(nextReport)
                    tsAsString = timestampToUtcDatetime(nextReport).strftime('%Y%m%dT%H%M%S') + '.%03d' % (nextReport % 1000,)
                    now = datetime.datetime.utcnow()
                    # tsAsString = now.strftime('%Y%m%dT%H%M%S') + '.%03d' % (now.microsecond/1000)
                    fields.append(tsAsString)
                    fields.append('%d' % (self.analyzerStatus.getStatus(),))
                    fields += [format(formatList,v) for v in selected]
                    data = ','.join(fields)
                    if self.analyzerStatus.getLevel() == AnalyzerStatus.SENSORS_ACTIVE:
                        self.sendPacket('%s\r\n' % data)
                    nextReport += self.sensorPeriod
                ts = getTimestamp()
                if ts>nextHeartbeat:
                    self.analyzerStatus.receivedHeartbeat()
                    if self.analyzerStatus.getLevel() == AnalyzerStatus.HOST_ONLY:
                        fields = [self.id]
                        uTime = unixTime(nextHeartbeat)
                        tsAsString = timestampToUtcDatetime(nextHeartbeat).strftime('%Y%m%dT%H%M%S') + '.%03d' % (nextHeartbeat % 1000,)
                        now = datetime.datetime.utcnow()
                        # tsAsString = now.strftime('%Y%m%dT%H%M%S') + '.%03d' % (now.microsecond/1000)
                        fields.append(tsAsString)
                        fields.append('%d' % self.analyzerStatus.getStatus())
                        data = ','.join(fields)
                        self.sendPacket('%s\r\n' % data)
                        nextReport = self.sensorPeriod*(ts//self.sensorPeriod)
                    nextHeartbeat += self.heartBeatPeriod
        except:
            print traceback.format_exc()
        finally:
            self.tcpServer.close()
            self.tcpDataServer.close()
            self.udpServer.close()
                
                
HELP_STRING = """AccessViaNet.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./AccessViaNet.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options

if __name__ == "__main__":
    accessViaNetApp = SingleInstance("AccessViaNet")
    if accessViaNetApp.alreadyrunning():
        Log("Instance of AccessViaNet application is already running",Level=3)
    else:
        configFile, options = handleCommandSwitches()
        app = AccessViaNet(configFile)
        Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
        app.run()
    Log("Exiting program")
