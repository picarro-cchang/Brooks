APP_NAME = "ElectricalInterface"

from Host.ElectricalInterface.ElectricalInterface import EifMgr, HandleCommandSwitches
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__" :
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        eif = EifMgr(configFile)
        eif.run()
        Log("Exiting program")
    except Exception, E:
        if __debug__: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))
