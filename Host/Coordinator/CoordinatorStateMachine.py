#
# FILE:  
#   Coordinator1.py
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
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved 
#
import sys
import time
from traceback import format_exc
from time import sleep, mktime, localtime, strptime, strftime 

from CoordinatorScripts import calcInjectDateTime, formatOutput, Comms
from CoordinatorScripts import getValveStep, setValveStep, sendValveSequence
from CoordinatorScripts import dummyGetLog, DummyAutosampler
import CoordinatorScripts
from Autosampler import Autosampler
from IsotechGC import GC
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_MEAS_SYSTEM, RPC_PORT_SAMPLE_MGR, RPC_PORT_DATA_MANAGER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SerIntrf import SerIntrf

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
        self.guiProxy = GuiProxy(gui,controlFunc)
        self.gui = gui
        self.scriptEnv = {}
        # Parse the configuration file containing the state machine
        self.config = CustomConfigObj(iniFile, list_values = True)
        self.setup = self.config['Setup']
        # We no longer use a user-specified script file
        # if scriptFile == None:
        #     # The script file must be specified in the [Setup] section
        #     scriptFile = file(self.setup['script'],"r")
        #  Compile the script file within its own environment
        # self.scriptName = getattr(scriptFile,'name','<string>')
        # self.script = compile(scriptFile.read().replace("\r\n","\n"),self.scriptName,'exec')
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
        self.editParamDict = editParamDict
        self.running = False
        self.driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "Coordinator")
        self.measSys = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM, ClientName = "Coordinator")
        self.sampleMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SAMPLE_MGR, ClientName = "Coordinator")
        self.dataMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = "Coordinator")
        
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
        scriptSyms = dir(CoordinatorScripts)
        for sym in scriptSyms:
            if sym[:2] != "__":
                self.scriptEnv[sym] = getattr(CoordinatorScripts,sym)
        self.scriptEnv.update({"logFunc":self.logFunc,"fileDataFunc":self.fileDataFunc,\
                          "config":self.config,"Autosampler":Autosampler,"DummyAutosampler":DummyAutosampler,\
                          "GC":GC,"SerIntrf":SerIntrf,"GUI":self.guiProxy,"getDescription":self.getDescription,\
                          "time":time,"editParamDict":self.editParamDict,"runningFlag":True,"pause":self.turnOffRunningFlag,\
                          "resume":self.turnOnRunningFlag})
        CoordinatorScripts.DRIVER = self.driver
        CoordinatorScripts.MEASSYS = self.measSys
        CoordinatorScripts.SAMPLEMGR = self.sampleMgr
        CoordinatorScripts.DATAMGR = self.dataMgr         
        CoordinatorScripts.LOGFUNC = self.logFunc
        CoordinatorScripts.CONFIG = self.config
        #try:
        #    exec self.script in self.scriptEnv
        #except Exception,e:
        #    self.running = False
        #    raise RuntimeError("\n%s\nWhile running %s: %s%s" % (72*"=",self.scriptName,format_exc(),72*"="))

        while True:
            if not self.running: # Always leave via the final state
                self.state = self.finalState
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
        self.running = False
        return self.scriptEnv

if __name__ == "__main__":
    fsm = StateMachine(file("Coordinator.ini"),file("CoordinatorScripts.py"))
    env = fsm.run()
    print "Program termination"
