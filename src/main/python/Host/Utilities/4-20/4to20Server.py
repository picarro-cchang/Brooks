#!/usr/bin/python
"""
File Name: 4to20Server.py
Purpose: 4-20 mA back end. It takes data obj from data manager, 
map the consentration to the 0-40 mA value and send to COM port 
on the mother board.  

File History:
    17-04-03  Wenting   Created file

Copyright 2017 Picarro, Inc. 
"""


import sys,time,os
import math
import serial
import getopt
from Host.Common.CustomConfigObj import CustomConfigObj

from Host.Common import CmdFIFO, SharedTypes, Listener, StringPickler
import threading

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
APP_NAME = "4to20Server"

class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            if self.ExitFunction is not None:
                self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")


class Four220Server(object):
    def __init__(self, configFile, simulation):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            raise Exception("Configuration file not found: %s" % configFile)
        
        self.port = self.config.get('SERIAL_PORT_SETUP', 'PORT')
        self.baudrate = self.config.getint('SERIAL_PORT_SETUP', 'BAUDRATE')
        self.timeout = self.config.getfloat('SERIAL_PORT_SETUP', 'TIMEOUT')
        
        self.analyzer_source = self.config.get('MAIN', 'ANALYZER')
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout = self.timeout)
        except:
            print "Can not connect to %s port. Please check the SERIAL_PORT_SETUP configuration. "% self.port
        #simulation mode or execution mode    
        if simulation:
            self.data_thread = threading.Thread(target=self.simulate_data)
            self.data_thread.daemon = True
            self.data_thread.start()
        else:
            self.get_channel_info()
            print self.channel_par
            self.startServer()
            self.data_thread = Listener.Listener(None, 
                                        SharedTypes.BROADCAST_PORT_DATA_MANAGER, 
                                        StringPickler.ArbitraryObject,
                                        self._streamFilter,
                                        retry = True,
                                        name = APP_NAME)
        
    def simulate_data(self):
        """
        Simulate the concentration data. Send mapped current value to COM port.
        """
        
        
        self.simulation_env = {}
        self.simulation_env['min'] = self.config.getfloat('Simulation', 'MIN')
        self.simulation_env['max'] = self.config.getfloat('Simulation', 'MAX')
        self.simulation_env['Test_mode'] = self.config.getboolean('Simulation', 'TEST_MODE')
        self.simulation_env['Test_num'] = self.config.getint('Simulation', 'TEST_NUM')
        self.simulation_env['channel'] = self.config.getint('Simulation', 'CHANNEL')
        if self.simulation_env['min'] != '' and self.simulation_env['max'] != '':
            slope = 16.0/(float(self.simulation_env['max']) - float(self.simulation_env['min']))
            offset = 4.0 - slope*float(self.simulation_env['min'])
            print "Simulation: Slope and Offset: ", slope, offset
        else:
            print "Configuration Error: Please input valid SOURCE_MIN, SOURCE_MAX values in Simulation section ini file."

        #Test mode will let you enter a concentration value manually and send the current to COM port.
        if self.simulation_env['Test_mode']:
            for i in range(self.simulation_env['Test_num']):
                print "********\n Enter a concentration value:"
                input = raw_input()
                if not input.isdigit():
                    print "What you entered is not a number. Enter again."
                    continue
                data = float(input.strip())
                try:
                    self.data_processor(data, slope, offset, self.simulation_env['channel'])
                except:
                    print "Can not send to serial port."
                    continue 
                time.sleep(1)
            
        else:
            for i in range(201):
                data = float(i * 4)
                print "simulated concentration: ", data, 'ppb'
                
                try:
                    self.data_processor(data, slope, offset, self.simulation_env['channel'])
                except:
                    print "Can not send to serial port."
                    break 
                time.sleep(5)
    #this fun is called every time when the listener gets data obj from data manager.
    def _streamFilter(self, streamOut):
        try:
            #get the concentration indicated in the ini file as source. 
            if streamOut["source"] == self.analyzer_source:
                raw_data = streamOut["data"]
                for channel in self.channel_par:
                    channel_num = int(channel[-1])
                    try:
                        data = raw_data[self.channel_par[channel]["SOURCE"]]
                    except:
                        print "SOURCE value in configuration file is not valid. " 
                        sys.exit(1)
                    #get slope and offset from ini
                    # if self.channel_par[channel]["SLOPE"] != '' and self.channel_par[channel]["OFFSET"] != '':
                        # slope = float(self.channel_par[channel]["SLOPE"])
                        # offset = float(self.channel_par[channel]["OFFSET"])
                    if float(self.channel_par[channel]["SOURCE_MIN"]) <= float(self.channel_par[channel]["SOURCE_MAX"]):
                        slope = 16.0/(float(self.channel_par[channel]["SOURCE_MAX"]) - float(self.channel_par[channel]["SOURCE_MIN"]))
                        offset = 4.0 - slope*float(self.channel_par[channel]["SOURCE_MIN"])
                    else:
                        print "Configuration Error: Please input valid SOURCE_MIN, SOURCE_MAX values in ini file. Make sure min you put is less than max."
                        sys.exit(1)
                    print "Slope and Offset: ", slope, offset
                    
                    self.data_processor(data, slope, offset, channel_num)
        except Exception, err:
            print "Error in streamFilter. Wrong values in ini file..."
            print err, "   ****"
            
    def data_processor(self, data, slope, offset, channel_num):
        """
        It takes the concentration (data), map to 4-20 mA, and send to command to the designated COM port.  
        
        """
        cur = float(slope * data + offset)
        
        if cur < 0.0 or cur > 20.0:
            print "Cur out of range."
        elif cur < 10.0:
            cur_str = '0'+ format(cur, '.3f')
        else:
            cur_str = format(cur, '.3f')
        cmd_str = '#0'+ str(channel_num + 1) + '0+' + cur_str
        try:
            self.ser.write(cmd_str + '\r')
            #ser.close()
            print "Gas Concentration: ", data
            print "Write current %f mA to serial port %s."%(cur,self.port)
            print "-------------------"
            
        except:
            "Failed to write to serial port."
        
        
        
    def run(self):
        """
        Main loop.
        """
        while True: 
            time.sleep(10)
    
    def get_channel_info(self):
        """
        config parse. get parameters in each channel 
        """
        self.channel_par = {}
        for s in self.config:
            if s.startswith("OUTPUT_CHANNEL"):
                if self.config[s]["SOURCE"] != '': 
                    if self.config[s]["SOURCE_MIN"] != '' and self.config[s]["SOURCE_MAX"] != '':
                        if float(self.config[s]["SOURCE_MIN"]) < 0:
                            self.config[s]["SOURCE_MIN"] = 0
                        if float(self.config[s]["SOURCE_MAX"]) > 2000:
                            self.config[s]["SOURCE_MAX"] = 2000
                        
                        self.channel_par[s] = self.config[s]
                    else:
                        print "Please check configuration file. Make sure you set the SOURCE_MIN and SOURCE_MAX in", s
                        sys.exit(1)

    def startServer(self):
        """
        Start rpc server thread.  
        """
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_4to20_SERVER),
                                            ServerName = APP_NAME,
                                            ServerDescription = "",
                                            ServerVersion = "1.0.0",
                                            threaded = True)
        self.rpcThread = RpcServerThread(self.rpcServer, None)
        self.rpcThread.start()                        
        
        
HELP_STRING = """Four220Server.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./4to20Server.ini"
-s                   simulation mode
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s'
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
    configFile = os.path.join(os.path.dirname(AppPath), "4to20Server.ini")
    simulation = False
    
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options:
        simulation = True

    return (configFile, simulation)

if __name__ == "__main__":
    server = Four220Server(*handleCommandSwitches())
    server.run()