APP_NAME = "RDFrequencyConverter"

import traceback
from Host.RDFrequencyConverter.RDFrequencyConverter import RDFrequencyConverter, handleCommandSwitches
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    configFilename, virtualMode, options = handleCommandSwitches()
    rdFreqConvertApp = RDFrequencyConverter(configFilename, virtualMode)
    Log("%s started." % APP_NAME, dict(ConfigFile = configFilename), Level = 0)
    rdFreqConvertApp.run()
    Log("Exiting program")
