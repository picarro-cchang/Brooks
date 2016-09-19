#
# FILE:
#   CoordinatorStateMachine.py
#
# DESCRIPTION:
#   Finite state machine driver for autosampler, evaporator and CRDS analyzer
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   03-Jun-2008  sze  Initial version.
#   04-Dec-2008  alex Use CustomConfigObj to replace configobj
#   20-Sep-2010  sze  Add spectrum collector to list of RPC servers accessible
#                      from CoordinatorScripts
#   01-Sep-2016  yuan New coordinator that can execute python script files besides legacy ini files.
#
#  Copyright (c) 1999 - 2016 Picarro, Inc. All rights reserved
#
import os
import sys
import time
from traceback import format_exc
from time import sleep, mktime, localtime, strptime, strftime

from Host.Coordinator.CoordinatorScripts import calcInjectDateTime, formatOutput, Comms
from Host.Coordinator.CoordinatorScripts import getValveStep, setValveStep, sendValveSequence
from Host.Coordinator.CoordinatorScripts import dummyGetLog, DummyAutosampler
import Host.Coordinator.CoordinatorScripts as CoordinatorScripts
from Host.Coordinator.Autosampler import Autosampler
from Host.Coordinator.IsotechGC import GC
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_MEAS_SYSTEM, \
                                    RPC_PORT_SAMPLE_MGR, RPC_PORT_DATA_MANAGER, \
                                    RPC_PORT_DATALOGGER, RPC_PORT_QUICK_GUI, \
                                    RPC_PORT_INSTR_MANAGER, RPC_PORT_FREQ_CONVERTER, \
                                    RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_VALVE_SEQUENCER, \
                                    RPC_PORT_AUTOSAMPLER, RPC_PORT_SUPERVISOR
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SerIntrf import SerIntrf
from Host.Utilities.ModbusIntrf.ModbusIntrf import ModbusIntrf

OK = 1
EXCEPTION = 2
TIMEOUT = 3

class State(object):
    """A state consists of a name, and an action which is a block of code which performs some actions
    and then sets the pseudo-variable NEXT to a string containing the name of the next state."""
    def __init__(self,name):
        self.name = name
        self.code = None
        self.actionString = ""
    def setAction(self,action):
        self.actionString = action
        self.code = compile(self.actionString,"<State %s action>" % self.name,"exec")

class GuiProxy(object):
    """This class allows methods belonging to the main frame (gui) to be called from within a thread.
       A method of the proxy object is mapped to the corresponding method of the gui. The arguments
       passed to the function are use to curry the main frame method, so that the resulting function
       object (with no arguments) may be passed to the main frame via the control queue for execution."""

    def __init__(self,gui,controlFunc):
        self.gui = gui
        self.controlFunc = controlFunc
        self.guiMethods = []

    def __getattr__(self,name):
        # A queue of methods is needed here. If only the most recent method is kept, it may be overwritten before it gets a chance
        #  to be curried
        self.guiMethods.append(getattr(self.gui,name))
        return self.getArgsAndEnqueue

    def getArgsAndEnqueue(self,*a,**k):
        def curried():
            return self.guiMethods.pop(0)(*a,**k)
        stat,reply = self.controlFunc(curried)
        if stat == OK:
            return reply
        elif stat == EXCEPTION:
            raise reply
        elif stat == TIMEOUT:
            print reply

class BaseMachine(object):
    """Base class for constructing state machines. All the
        methods may be overridden in subclasses.

       The machine starts in "state_start" and finishes after
       completion of "state_done". If an exception occurs, the
       machine enters "state_error".

       The state methods (excluding state_done) return a string
       which is the name of the next state
    """
    def state_start(self):
        self.logFunc( "In state_start. Override this in subclass" )
        return "state_done"

    def state_done(self):
        self.logFunc( "All done" )

    def state_error(self, state, exc):
        self.logFunc( "Error in %s" % state )
        self.logFunc( format_exc(exc) )
        return "state_done"            
            
class StateMachine(object):
    # The scriptFile is compiled and executed when run is called to provide an environment within which
    #  the state machine actions can be executed. If the scriptFile is not specified, the 'script' option
    #  within the 'Setup' section of the iniFile is used.
    # The state machine transitions according to the entries in the iniFile, until it reaches the
    #  final state, whereupon it stops. If the state machine is stopped by calling the stop method,
    #  it will jump to the final state on the next transition, so that there is an opportunity to tidy up.
    # The functions logFunc and fileDataFunc are placed within the environment in which the script
    #  and state machine actions are run, so that they can communicate to the user.
    # A copy of the ConfigObj object made from the ini file is placed in the script environment as "config"
    # The main GUI which is used for user interaction is passed as "gui". A proxy object is passed to the
    #   script file so that the script can call functions of the main GUI even though it is not in the main thread.
    #   These function calls are actually enqueued so that the main GUI thread can execute them when idle.
    #
    def __init__(self,iniFile,gui,scriptFile=None,logFunc=None,fileDataFunc=None,controlFunc=None,editParamDict=None):
        if logFunc==None: logFunc = self.defaultLogger
        if fileDataFunc==None: fileDataFunc = self.defaultLogger
        self.logFunc = logFunc
        self.fileDataFunc = fileDataFunc
        self.controlFunc = controlFunc
        self.editParamDict = editParamDict
        self.guiProxy = GuiProxy(gui,controlFunc)
        self.gui = gui
        self.scriptEnv = {}
        # Parse the configuration file containing the state machine
        self.config = CustomConfigObj(iniFile, list_values = True)
        self.portDict = {}
        self.machine = None
        if "SerialPorts" in self.config:
            try:
                self.portDict = self.config["SerialPorts"].copy()
            except:
                pass
        self.setupSciptEnv()
        self.setup = self.config['Setup']
        if 'script' in self.setup:
            scriptFile = self.setup['script']
            if not os.path.exists(scriptFile):
                raise ValueError("Script file not found: %s" % scriptFile)
            #  Compile the script file within its own environment
            with open(scriptFile, "r") as fp:
                self.script = compile(fp.read().replace("\r\n", "\n"), scriptFile, "exec")
                exec(self.script, self.scriptEnv)
                machine = self.scriptEnv["MACHINE_CLASS"]
                if not issubclass(machine, BaseMachine):
                    raise ValueError("MACHINE_CLASS must be set to a sub-class of StateMachine")
                self.machine = machine()
                self.initialState = "state_start"
                self.finalState = "state_done"
                self.errorState = "state_error"
        else:   # legacy coordinator files
            self.stateNames = [s for s in self.config.sections if s.startswith('State')]
            self.states = {}
            for name in self.stateNames:
                s = State(name)
                self.states[name] = s
                sc = self.config[name]
                s.setAction(sc["action"])
            try:
                stateName = self.setup['initial']
            except:
                raise ValueError("No initial state has been specified")
            if stateName not in self.states:
                raise ValueError("%s is not a valid initial state" % stateName)
            self.initialState = self.states[stateName]
            try:
                stateName = self.setup['final']
            except:
                raise ValueError("No final state has been specified")
            if stateName not in self.states:
                raise ValueError("%s is not a valid final state" % stateName)
            self.finalState = self.states[stateName]
            try:
                stateName = self.setup['error']
            except:
                raise ValueError("No error state has been specified")
            if stateName not in self.states:
                raise ValueError("%s is not a valid error state" % stateName)
            self.errorState = self.states[stateName]
        self.state = ""
        self.running = False

    def setupSciptEnv(self):
        CoordinatorScripts.SUPERVISOR = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, ClientName = "Coordinator")
        CoordinatorScripts.DRIVER = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "Coordinator")
        CoordinatorScripts.MEASSYS = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM, ClientName = "Coordinator")
        CoordinatorScripts.SAMPLEMGR = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SAMPLE_MGR, ClientName = "Coordinator")
        CoordinatorScripts.DATAMGR = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = "Coordinator")
        CoordinatorScripts.DATALOGGER = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER, ClientName = "Coordinator")
        CoordinatorScripts.QUICKGUI = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_QUICK_GUI, ClientName = "Coordinator")
        CoordinatorScripts.INSTMGR = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, ClientName = "Coordinator")
        CoordinatorScripts.FREQCONV = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER, ClientName = "Coordinator")
        CoordinatorScripts.SPECTCOLLECTOR = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR, ClientName = "Coordinator")
        CoordinatorScripts.VALSEQ = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_VALVE_SEQUENCER, ClientName = "Coordinator")
        CoordinatorScripts.LOGFUNC = self.logFunc
        CoordinatorScripts.CONFIG = self.config
        self.newAutosampler = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_AUTOSAMPLER, ClientName = "Coordinator")
        BaseMachine.logFunc = self.logFunc
        scriptSyms = dir(CoordinatorScripts)
        for sym in scriptSyms:
            if sym[:2] != "__":
                self.scriptEnv[sym] = getattr(CoordinatorScripts,sym)
        self.scriptEnv.update({"logFunc":self.logFunc,"fileDataFunc":self.fileDataFunc,\
                          "config":self.config,"Autosampler":Autosampler,"DummyAutosampler":DummyAutosampler,\
                          "GC":GC,"SerIntrf":SerIntrf,"GUI":self.guiProxy,"getDescription":self.getDescription,\
                          "time":time,"editParamDict":self.editParamDict,"runningFlag":True,"pause":self.turnOffRunningFlag,\
                          "resume":self.turnOnRunningFlag, "portDict":self.portDict, "configObj":CustomConfigObj,
                          "NEWAUTOSAMPLER":self.newAutosampler, "ModbusIntrf":ModbusIntrf, "StateMachine": BaseMachine})
        
    def defaultLogger(self,str):
        print str

    def stop(self):
        print "Stopping FSM"
        self.running = False

    def isRunning(self):
        return self.running

    def getDescription(self,key):
        return self.gui.sampleDescriptionDict.get(key,"")

    def turnOffRunningFlag(self):
        self.scriptEnv["runningFlag"] = False

    def turnOnRunningFlag(self):
        self.scriptEnv["runningFlag"] = True

    def run(self):
        self.running = True
        self.state = self.initialState     

        while True:
            if not self.running: # Always leave via the final state
                    self.state = self.finalState
            if self.machine is None: # legacy coordinator script
                try:
                    self.scriptEnv["NEXT"] = self.state.name
                    if self.state.code != None:
                        exec self.state.code in self.scriptEnv
                except Exception,e:  # Transition to error state on an exception
                    self.scriptEnv["ERROR_STATE"] = self.state.name
                    self.scriptEnv["ERROR_MSG"] = "%s" % e
                    if self.state.name != self.finalState.name:
                        self.state = self.errorState
                        continue
                    else:
                        self.logFunc("Exception %s occured in final state\n" % e)
                        break

                if self.state.name == self.finalState.name:
                    break
                try:
                    self.state = self.states[self.scriptEnv["NEXT"]]
                except:
                    raise ValueError("State %s does not exist\nCurrent state: %s\nCurrent action: %s" %
                        (self.scriptEnv["NEXT"],self.state.name,self.state.actionString))
            else:
                state = self.state
                try:
                    state_func = getattr(self.machine, state)
                    self.state = state_func()
                except Exception, e:
                    self.state = self.machine.state_error(state, e)
                if state == self.finalState:
                    break
        self.running = False
        return self.scriptEnv

if __name__ == "__main__":
    fsm = StateMachine(file("Coordinator.ini"),file("CoordinatorScripts.py"))
    env = fsm.run()
    print "Program termination"