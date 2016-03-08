APP_NAME = "Driver"

import time
from Host.Driver.Driver import Driver, handleCommandSwitches
from Host.Common.SingleInstance import SingleInstance
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    driverApp = SingleInstance("PicarroDriver")
    if driverApp.alreadyrunning():
        Log("Instance of driver us already running",Level=3)
    else:
        sim, configFile = handleCommandSwitches()
        Log("%s started." % APP_NAME, dict(Sim = sim, ConfigFile = configFile), Level = 0)
        d = Driver(sim,configFile)
        d.run()
    Log("Exiting program")
    time.sleep(1)
