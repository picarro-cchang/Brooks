APP_NAME = "SpectrumCollector"

import multiprocessing
from Host.SpectrumCollector.SpectrumCollector import SpectrumCollector, handleCommandSwitches
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        configFile, options = handleCommandSwitches()
        spCollectorApp = SpectrumCollector(configFile)
        Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
        spCollectorApp.run()
        # cProfile.run('spCollectorApp.run()','c:/spectrumCollectorProfile')
        Log("Exiting program")
    except Exception:
        LogExc("Unhandled exception in SpectrumCollector", Level=3)