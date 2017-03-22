APP_NAME = "DriverSimulator"

import time
from Host.DriverSimulator.DriverSimulator import DriverSimulator, handleCommandSwitches
from Host.Common.SingleInstance import SingleInstance
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    driverApp = SingleInstance("PicarroDriver")
    if driverApp.alreadyrunning():
        Log("Instance of driver us already running",Level=3)
    else:
        configFile = handleCommandSwitches()
        Log("%s started." % APP_NAME, dict(ConfigFile=configFile), Level=0)
        d = DriverSimulator(configFile)
        d.run()
    Log("Exiting program")
    time.sleep(1)
