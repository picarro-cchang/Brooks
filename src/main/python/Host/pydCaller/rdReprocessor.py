from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.rdReprocessor.rdReprocessor import rdReprocessor, HandleCommandSwitches

APP_NAME = "rdReprocessor"
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if __name__ == "__main__":
    configFile, loop = HandleCommandSwitches()
    print  "The name of configFile is %s" % configFile
    app = rdReprocessor(configFile, loop)
    app.run()