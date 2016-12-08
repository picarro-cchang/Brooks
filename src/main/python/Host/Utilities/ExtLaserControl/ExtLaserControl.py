import wx

from Host.Utilities.ExtLaserControl.AnalyzerModel import AnalyzerModel
import argparse
from Host.Utilities.ExtLaserControl.ConfigProcessor import ConfigProcessor
from Host.Utilities.ExtLaserControl.LaserCurrentModel import LaserCurrentModels
from Host.Utilities.ExtLaserControl.LaserControlViewModel import LaserControlViewModel
from Host.Utilities.ExtLaserControl.LaserCurrentViewModel import LaserCurrentViewModel
from Host.Utilities.ExtLaserControl.LaserControlFrameGui import LaserControlFrameGui
from Host.Common.SharedTypes import RPC_PORT_EXT_LASER_CONTROLLER
from Host.Common.CmdFIFO import CmdFIFOServer
import gettext
import os
import sys
from threading import Thread

APP_NAME = "Extended Laser Current Controller"
APP_VERSION = "1.0.0"

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    app_path = sys.executable
else:
    app_path = sys.argv[0]

class LaserControlFrame(LaserControlFrameGui):
    def __init__(self, *args, **kwargs):
        super(LaserControlFrame, self).__init__(*args, **kwargs)
        self.laser_current_models = None
        self.laser_current_view_models = None
        self.panel_lookup = {
            "Laser1":self.laser1_control_panel,
            "Laser2":self.laser2_control_panel,
            "Laser3":self.laser3_control_panel,
            "Laser4":self.laser4_control_panel
        }
        self.laser_control_view_model = None
        self.process_rd_timer = wx.Timer(self)

    def process_options(self, options):
        cp = ConfigProcessor()
        cp.process_config(options['config'])
        self.laser_current_models = LaserCurrentModels()
        self.laser_current_models.load_from_config(cp.config)
        self.laser_current_view_models = []

        for model in self.laser_current_models.models:
            if model is not None:
                name = model.name
                view = self.panel_lookup[name]
                view_model = LaserCurrentViewModel(model, view)
                self.laser_current_view_models.append(view_model)
                view.set_view_model(view_model)
            else:
                self.laser_current_view_models.append(None)
        analyzer_model = AnalyzerModel(self.laser_current_models.models)
        self.laser_control_view_model = LaserControlViewModel(analyzer_model, self)
    def set_slope_factor(self, laser_num, slope_factor):
        """Sets slope factor for specified laser (1-origin)"""
        view_model = self.laser_current_view_models[laser_num-1]
        view_model.set_model_parameter("slope_factor", slope_factor)
        
    def set_timeBetweenSteps(self, laser_num, time_steps):
        """Sets time interval between steps for specified laser (1-origin)"""
        view_model = self.laser_current_view_models[laser_num-1]
        view_model.set_model_parameter("time_between_steps", time_steps)
    
    def set_upper_window(self, laser_num, upper_window):
        """Sets laser current upper window for specified laser (1-origin)"""
        view_model = self.laser_current_view_models[laser_num-1]
        view_model.set_model_parameter("upper_window" , upper_window)
    
    def set_lower_window(self, laser_num, lower_window):
        """Sets laser current lower window for specified laser (1-origin)"""
        view_model = self.laser_current_view_models[laser_num-1]
        view_model.set_model_parameter("lower_window" , lower_window)
    
    def set_binning_rd(self, laser_num, binning_rd):
        """Sets binning_rd for specified laser (1-origin)"""
        view_model = self.laser_current_view_models[laser_num-1]
        view_model.set_model_parameter("binning_rd" , binning_rd)\
        
    def registerRpc(self):
        self.rpcServer.register_function(self.multiplier)
        self.rpcServer.register_function(self.set_slope_factor)
        self.rpcServer.register_function(self.set_timeBetweenSteps)
        self.rpcServer.register_function(self.set_upper_window)
        self.rpcServer.register_function(self.set_lower_window)
        self.rpcServer.register_function(self.set_binning_rd)
        
    def start_rpc_server(self):
        self.rpcServer = CmdFIFOServer(("", RPC_PORT_EXT_LASER_CONTROLLER),
                                        ServerName = APP_NAME,
                                        ServerDescription = "Extended laser current controller",
                                        ServerVersion = APP_VERSION,
                                        threaded = True)
        self.registerRpc()
        #start the rpc server on another thread...
        self.rpcThread = Thread(target=self.do_rpc)
        self.rpcThread.setDaemon(True)
        self.rpcThread.start()
        
    def do_rpc(self):
        try:
            while True:
                self.rpcServer.daemon.handleRequests(0.5)
        except:
            print "RPC server stopped"
            wx.CallAfter(self.Close, True)
    
        
# def handle_command_switches():
    # parser = argparse.ArgumentParser(description = "Extended Laser Control Panel")
    # parser.add_argument('-c', '--config', dest='config', help='Name of configuration file', default=os.path.splitext(app_path)[0] + ".ini")
    # args = parser.parse_args()
    # return vars(args)

def handle_command_switches():
    import getopt

    shortOpts = 'c:d:hvo:'
    longOpts = ["help","viewer"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit(0)
    print options
    useViewer = False
    if "-v" in options or "--viewer" in options:
        useViewer = True

    #Start with option defaults...
    configFile = os.path.splitext(app_path)[0] + ".ini"
    print configFile
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    
    parser = argparse.ArgumentParser(description = "Extended Laser Control Panel")
    parser.add_argument('-c', '--config', dest='config', help='Name of configuration file', default=os.path.splitext(app_path)[0] + ".ini")
    args = parser.parse_args()
    return vars(args)
    
    #parser.add_argument
    #return (configFile, useViewer, options)

   
if __name__ == "__main__":
    gettext.install("app") # replace with the appropriate catalog name
    options = handle_command_switches()
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = LaserControlFrame(None, wx.ID_ANY, "")
    frame_1.process_options(options)
    frame_1.start_rpc_server()
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()