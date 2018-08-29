"""
File Name: 4to20Server.py
Purpose: 4-20 mA back end. It takes data obj from data manager, 
map the consentration to the 0-40 mA value and send to COM port 
on the mother board.
module i7024 Hardware info: http://confluence.picarro.int/display/SEM/4-20+mA+Analog+Output+Testing
software implimentation: http://confluence.picarro.int/display/~wtan@picarro.com/Software+Implement+4-20+mA+Output+for+SI2000+Series+Analyzers

File History:
    17-04-03  Wenting   Created file

Copyright 2017 Picarro, Inc. 
"""


import sys,time,os
import serial
import getopt
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import Log, LogExc
from Host.Common import CmdFIFO, SharedTypes, Listener, StringPickler
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR
from Host.Common.AppRequestRestart import RequestRestart
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
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout = self.timeout)
        except:
            print "Can not connect to %s port. Please check the SERIAL_PORT_SETUP configuration. "% self.port
        
        #set the device configuration to 4-20 mA outputs. Send the command '%0101310600'. You should get this reply '!01' saying that your re-configuration of the module was successful.
        try:
            self.ser.write('%0101310600'+ '\r')
            s = ''
            #wait for response. 
            while True:
                c = self.ser.read(1)
                if c == "\r":
                    break
                s += c
            #bytesToRead = self.ser.inWaiting()
            #s = self.ser.read(bytesToRead)
            #check the reply.
            if '!01' not in s:
                print "Can not set the device confidguration, aborting..."
                sys.exit(1)
        except:
            print "Can not set the device configuration to 4-20 mA outputs."
            sys.exit(1)
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
        self.con_max = self.simulation_env['max']
        self.con_min = self.simulation_env['min']
        
        self.simulation_env['Test_mode'] = self.config.getboolean('Simulation', 'TEST_MODE')
        self.simulation_env['Test_num'] = self.config.getint('Simulation', 'TEST_NUM')
        self.simulation_env['channel'] = self.config.getint('Simulation', 'CHANNEL')
        if self.simulation_env['min'] != 'None' and self.simulation_env['max'] != 'None':
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
            #print streamOut["source"]
            if streamOut["source"] == self.analyzer_source:
                raw_data = streamOut["data"]
                ###print raw_data.keys()
                for channel in self.channel_par:
                    channel_num = int(channel[-1])
                    ###print self.channel_par[channel]["SOURCE"], self.channel_par[channel]["SOURCE"] in raw_data.keys()
                    ###print "Channel:", channel, "channel_par:", self.channel_par[channel]
                    if self.channel_par[channel]["SOURCE"] != 'Disabled':
                        self.con_max = float(self.channel_par[channel]["SOURCE_MAX"])
                        self.con_min = float(self.channel_par[channel]["SOURCE_MIN"])
                        try:
                            data = raw_data[self.channel_par[channel]["SOURCE"]]
                        except:
                            continue
                            #sys.exit(1)
                            
                        #compute slope and offset values based in given max/min range
                        if self.con_min <= self.con_max:
                            slope = 16.0/(self.con_max - self.con_min)
                            offset = 4.0 - slope*self.con_min
                        else:
                            print "Configuration Error: Please input valid SOURCE_MIN, SOURCE_MAX values in ini file. Make sure min you put is less than max."
                            sys.exit(1)
                        ###print "Slope and Offset: ", slope, offset
                        self.data_processor(data, slope, offset, channel_num)
                    else:
                        ###print "Dummy Channel: channel", channel_num
                        self.data_processor(0, 0, 0, channel_num)
        except Exception, err:
            print "Error in streamFilter. Wrong values in ini file..."
            print err, "   ****"
            
    def data_processor(self, data, slope, offset, channel_num):
        """
        It takes the concentration (data), map to 4-20 mA, and send the command to the designated COM port.
        Any value lower than 4.0 mA will output 4.0 mA, any value higher than 20.0 mA will output 20.0 mA.
        
        """
        
        cur = float(slope * data + offset)
        
        if cur < 4.0:
            cur_str = '04.000'
        elif cur > 20.0:
            cur_str = '20.000'
        elif cur < 10.0:
            cur_str = '0'+ format(cur, '.3f')
        else:
            cur_str = format(cur, '.3f')


        #If send the command '#010+05.000'. This tells the module at address 01 to set channel 0 to 5.000 mA.
        cmd_str = '#01'+ str(channel_num) + '+' + cur_str
        
        try:
            self.ser.write(cmd_str + '\r')
            self.waitForRet()
            #ser.close()
            ###print "Channel: ", channel_num
            ###print self.channel_par['OUTPUT_CHANNEL'+str(channel_num)]["SOURCE"], " Value: ", data
            ###print "Write current %s mA to serial port %s."%(cur_str,self.port)
            ###print "-------------------"
            
        except:
            "Failed to write to serial port."
        
    def waitForRet(self):
        while True:
            c = self.ser.read(1)
            if c == "\r":
                break    
        
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
                #if self.config[s]["SOURCE"] != 'Disabled': 
                print "here: " #self.config[s]
                self.channel_par[s] = self.config[s]
                        #print "Please check configuration file. Make sure you set the SOURCE_MIN and SOURCE_MAX in", s
                        #sys.exit(1)

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

def main():
    server = Four220Server(*handleCommandSwitches())
    try:
        server.run()
    except Exception, e:
        LogExc("Unhandled exception in %s: %s" % APP_NAME % e, Level=3)
        # Request a restart from Supervisor via RPC call
        restart = RequestRestart(APP_NAME)
        if restart.requestRestart(APP_NAME) is True:
            Log("Restart request to supervisor sent", Level=0)
        else:
            Log("Restart request to supervisor not sent", Level=2)


if __name__ == "__main__":
    main()
