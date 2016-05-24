APP_NAME = "Supervisor"
import traceback
from Host.Supervisor.Supervisor import main, GetConfigFileAndIniLog
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if __name__ == "__main__":
    configFile, printIniLog = GetConfigFileAndIniLog()
    try:
        main()
    except SystemExit:
        pass
    except:
        # tbMsg = BetterTraceback.get_advanced_traceback()
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
        print tbMsg
        Log("Exiting program")
