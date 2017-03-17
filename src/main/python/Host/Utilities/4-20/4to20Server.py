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

class Four220Server(object):
    def __init__(self, configFile, simulation):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            raise Exception("Configuration file not found: %s" % configFile)
        
        self.port = self.config.get('SERIAL_PORT_SETUP', 'PORT')
        self.analyzer_source = self.config.get('MAIN', 'ANALYZER')
        try:
            self.ser = serial.Serial(self.port)
        except:
            print "Can not connect to %s port."% self.port
            
        if simulation:
            self.data_thread = threading.Thread(target=self.simulate_data)
            self.data_thread.daemon = True
            self.data_thread.start()
        else:
            self.get_channel_info()
            print self.channel_par
            self.data_thread = Listener.Listener(None, 
                                        SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                        StringPickler.ArbitraryObject,
                                        self._streamFilter,
                                        retry = True,
                                        name = APP_NAME)
        
    def simulate_data(self):
        self.simulation_env = {}
        self.simulation_env['Slope'] = self.config.getfloat('Simulation', 'SLOPE')
        self.simulation_env['Offset'] = self.config.getfloat('Simulation', 'OFFSET')
        
        for i in range(1,401):
            data = i * 2
            print "simulated concentration: ", i, 'ppb'
            try:
                self.data_processor(data, self.simulation_env['Slope'], self.simulation_env['Offset'], 0)
            except:
                print "Can not send to serial port."
                break 
            time.sleep(5)
    
    def _streamFilter(self, streamOut):
        try:
            if streamOut["source"] == self.analyzer_source:
                raw_data = streamOut["data"]
                for channel in self.channel_par:
                    channel_num = int(channel[-1])
                    data = raw_data[self.channel_par[channel]["SOURCE"]]
                    #get slope and offset from ini
                    if self.channel_par[channel]["SLOPE"] != '' and self.channel_par[channel]["OFFSET"] != '':
                        slope = float(self.channel_par[channel]["SLOPE"])
                        offset = float(self.channel_par[channel]["OFFSET"])
                    elif self.channel_par[channel]["SOURCE_MIN"] != '' and self.channel_par[channel]["SOURCE_MAX"] != '':
                        slope = 16.0/(float(self.channel_par[channel]["SOURCE_MAX"]) + float(self.channel_par[channel]["SOURCE_MIN"]))
                        offset = 4.0 - slope*float(self.channel_par[channel]["SOURCE_MIN"])
                    else:
                        print "Configuration Error: Please input valid SLOPE, OFFSET or SOURCE_MIN, SOURCE_MAX values in ini file."
                    print "Slope and Offset: ", slope, offset
                    
                    self.data_processor(data, slope, offset, channel_num)
        except Exception, err:
            print "Error in streamFilter. Wrong values in ini file..."
            print err, "   ****"
            
    def data_processor(self, data, slope, offset, channel_num):
        
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
            print "Write current %f to serial port %s."%(cur,self.port)
            print "Write cur_str", cmd_str
        except:
            "Failed to write to serial port."
        
        
        
    def run(self):
        while True: 
            time.sleep(10)
    
    def get_channel_info(self):
        self.channel_par = {}
        for s in self.config:
            if s.startswith("OUTPUT_CHANNEL"):
                if self.config[s]["SOURCE"] != '':
                    self.channel_par[s] = self.config[s]
                    
                    
        
        
        
        
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
    configFile = os.path.dirname(AppPath) + "4to20Server.ini"
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