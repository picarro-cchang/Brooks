"""
File Name: GlobalHawk.py
Purpose: This is responsible for network communications with the NASA Global Hawk Aircraft
         It supports several external commands via TCP or UDP. 
         N.B. These MUST be terminated using a "\n" before they are obeyed.
         
         STANDBY  - Shut down but keep driver operating
         STOP     - Shut down and stop driver
         RESTART  - Restart analyzer
         REBOOT   - Hard reset analyzer by cycling power followed by restart
         SHUTDOWN - Shut down analyzer and computer

File History:
    11-09-05 sze   Initial release
    
Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

APP_NAME = "Global Hawk"
APP_DESCRIPTION = "Communication with Global Hawk Aircraft Network"
__version__ = 1.0

import asynchat
import asyncore
import datetime
import getopt
import os
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
from Host.Common.SharedTypes import Singleton, BROADCAST_PORT_DATA_MANAGER, BROADCAST_PORT_SENSORSTREAM, RPC_PORT_SUPERVISOR
from Host.Common.StringPickler import ArbitraryObject
from Host.Common.timestamp import getTimestamp, timestampToUtcDatetime

EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]


class AnalyzerControl(Singleton):
    initialized = False
    def __init__(self,config=None):
        if not self.initialized:
            self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
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

    def standby(self):
        self.killUncontrolled()
        self.supervisor.TerminateApplications(False, False)
        
    def stop(self):
        self.killUncontrolled()
        self.supervisor.TerminateApplications(False, True)

    def shutdown(self):
        self.killUncontrolled()
        self.supervisor.TerminateApplications(True, True)

    def reboot(self):
        self.killUncontrolled()
        # TODO: Run reboot procedure
        # os.system(r'taskkill.exe /IM Controller.exe /F')

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
                
        os.chdir(self.supervisorHostDir)
        info = subprocess.STARTUPINFO()
        print "ConsoleMode = ", self.consoleMode
        if self.consoleMode != 1:
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
        dwCreationFlags = win32process.CREATE_NEW_CONSOLE
            
        if self.launchType == "exe":
            subprocess.Popen(["supervisor.exe","-c",self.supervisorIni], startupinfo=info, creationflags=dwCreationFlags)
        else:
            subprocess.Popen(["python.exe", "Supervisor.py","-c",self.supervisorIni], startupinfo=info, creationflags=dwCreationFlags)

        # Launch HostStartup
        if self.launchType == "exe":
            info = subprocess.STARTUPINFO()
            subprocess.Popen(["HostStartup.exe","-c",self.supervisorIni], startupinfo=info)

                                        
class TcpServer(asyncore.dispatcher):
    """Receives connections and establishes handlers for each client.
    """
    def __init__(self, address,target):
        asyncore.dispatcher.__init__(self)
        self.handler = None
        self.target = target
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(1)
        return
    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        if self.handler is None or self.handler.closed:
            self.handler = TcpHandler(client_info[0],self.target)
        else:
            GoAwayHandler(sock=client_info[0])
    def handle_close(self):
        self.close()
        return
        
class UdpServer(asynchat.async_chat):
    def __init__(self,address,target):
        asynchat.async_chat.__init__(self)
        self.target = target
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(address)
        self.set_terminator('\n')
        self.buffer = []
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        print "UDP: %s" % "".join(self.buffer)
        self.buffer = []
    def handle_connect(self):
        pass
                
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
    
class TcpHandler(asynchat.async_chat):
    """Handles processing data from a single client.
    """
    def __init__(self,sock,target):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        self.push("Connected to Picarro TCP server\r\n")
        self.closed = False
        self.buffer = []
        self.actions = dict(STANDBY  = target.standby, 
                            STOP     = target.stop,
                            RESTART  = target.restart,
                            REBOOT   = target.reboot,
                            SHUTDOWN = target.shutdown)
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        cmd = "".join(self.buffer).strip().upper()
        print "TCP: %s" % cmd
        # Carry out the action
        try:
            self.actions[cmd]()
            self.push("OK %s\r\n" % cmd)
        except KeyError:
            self.push("Unknown command: %s\r\n" % cmd)
        except:
            self.push(traceback.format_exc().replace("\n","\r\n"))
        self.buffer = []
        
    def handle_close(self):
        self.closed = True
        self.close()        

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
    
class GlobalHawk(Singleton):
    initialized = False
    def __init__(self, configPath=None):        
        if not self.initialized:
            if configPath != None:
                # Read from .ini file
                self.config = ConfigObj(configPath)
                basePath = os.path.split(configPath)[0]
                self.statusHost, self.statusPort = self.config['Addresses']['Status'].split(':')
                self.statusPort = int(self.statusPort)
                self.statusSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                self.id = self.config['InstrumentName']['Id']
                self.sensorQueue = Queue(512)
                self.sensorListener = Listener.Listener(self.sensorQueue,
                                                        BROADCAST_PORT_SENSORSTREAM,
                                                        interface.SensorEntryType,
                                                        retry = True,
                                                        name = "GlobalHawk listener")
                self.dmQueue = Queue(512)
                self.dmListener = Listener.Listener(self.dmQueue,
                                                    BROADCAST_PORT_DATA_MANAGER,
                                                    ArbitraryObject,
                                                    retry = True,
                                                    name = "GlobalHawk listener")
                self.tcpHost, self.tcpPort = self.config['Addresses']['TCPcontrol'].split(':')
                self.tcpPort = int(self.tcpPort)
                self.udpHost, self.udpPort = self.config['Addresses']['UDPcontrol'].split(':')
                self.udpPort = int(self.udpPort)
                self.sensorPeriod = int(self.config['SensorReport']['Period'])
                # Read list of sensor streams
                self.streamIndices = MAX_SENSORS*[None]
                nmax = 0
                for k in self.config['SensorReport']:
                    if k.lower().startswith('sensor'):
                        num = int(k[6:])
                        if num>MAX_SENSORS or num<=0:
                            print "Invalid SENSOR number:", num
                        else:
                            nmax = max(nmax,num)
                            self.streamIndices[num-1] = getattr(interface,"STREAM_%s" % self.config['SensorReport'][k])
                self.streamIndices = self.streamIndices[:nmax]
                self.currentSensors = len(self.streamIndices)*[None]
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
                raise ValueError("Configuration file must be specified to initialize GlobalHawk network interface")
            self.initialized = True
        Log('GlobalHawk initialized',Data=dict(statusIP='%s:%d'%(self.statusHost,self.statusPort)))
        
    def sendStatus(self,data):
        self.statusSocket.sendto(data,(self.statusHost,self.statusPort))
        
    # Get data from sensor queue until some timestamp (from any stream) exceeds reportTime. 
    # If the queue becomes empty before this happens, return None
    # Otherwise, report latest values of sensor streams specified in streamIndices as a 
    #  list of the same length as streamIndices. This is a COPY of currentSensors so we can
    #  safely update currentSensors
    
    def setSensorStreams(self,streamIndices):
        # Specify list of stream indices that we wish to have reported
        self.streamIndices = streamIndices
        self.currentSensors = len(streamIndices)*[None]
        
    def getSensorData(self,reportTime):
        # Get all the data in the sensor queue up to reportTime and return all the current sensor
        #  values at that time. If the data in the sensor queue are all before reportTime, return None
        d = None
        try:
            while not self.sensorQueue.empty():
                d = self.sensorQueue.get()
                if d.timestamp>reportTime:
                    return self.currentSensors[:]   # Make a copy, since currentSensors is dynamically updated
                if d.streamNum in self.streamIndices:
                    self.currentSensors[self.streamIndices.index(d.streamNum)] = d.value
            return None
        finally:
            if d is not None:
                if d.streamNum in self.streamIndices:
                    self.currentSensors[self.streamIndices.index(d.streamNum)] = d.value
        
    def run(self):
        self.analyzerControl = AnalyzerControl(self.config)
        TcpServer((self.tcpHost,self.tcpPort),self.analyzerControl)
        UdpServer((self.udpHost,self.udpPort),self.analyzerControl)
        count = 0
        # TODO: For actual code, set up startTs from actual time, rather than from timestamp in the file
        startTs = getTimestamp()
        #d = self.sensorQueue.get()
        #startTs = d.timestamp
        nextReport = self.sensorPeriod*((startTs + self.sensorPeriod)//self.sensorPeriod)
        formatList = [(int,'%d'),(float,'%.5f'),(types.NoneType,'')]
        
        while True:
            asyncore.loop(timeout=0.1,count=1)
            # Get data available on the data manager queue
            if not self.dmQueue.empty():
                status_fields = [self.id]
                d = self.dmQueue.get()
                ts, mode, source = d['data']['timestamp'], d['mode'], d['source']
                if source == self.dataSource: 
                    tsAsString = timestampToUtcDatetime(ts).strftime('%Y%m%dT%H%M%S') + '.%03d' % (ts % 1000,)
                    status_fields.append(tsAsString)
                    status_fields.append('DATA')
                    dd = d['data']
                    status_fields += [format(formatList,dd.get(v,None)) for v in self.dataNames]
                    data = ','.join(status_fields)
                    self.sendStatus('%s\r\n' % data)
                    continue
            sensors = self.getSensorData(nextReport)
            if sensors is not None:
                # We have sensor data that was current as of nextReport
                status_fields = [self.id]
                tsAsString = timestampToUtcDatetime(nextReport).strftime('%Y%m%dT%H%M%S') + '.%03d' % (nextReport % 1000,)
                status_fields.append(tsAsString)
                status_fields.append('SENSORS')
                status_fields += [format(formatList,v) for v in sensors]
                data = ','.join(status_fields)
                self.sendStatus('%s\r\n' % data)
                nextReport += self.sensorPeriod
        
HELP_STRING = """GlobalHawk.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify a config file:  default = "./GlobalHawk.ini"
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
    configFile, options = handleCommandSwitches()
    app = GlobalHawk(configFile)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    app.run()
    Log("Exiting program")
