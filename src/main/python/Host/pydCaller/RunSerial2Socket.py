from Host.PeriphIntrf.RunSerial2Socket import RunSerial2Socket, HandleCommandSwitches
from Host.Common.SingleInstance import SingleInstance

if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    app = SingleInstance("RunSerial2Socket")
    if not app.alreadyrunning():
        RunSerial2Socket(configFile)
    else:
        print "Serial to socket already running"
    print "RunSerial2Socket terminating"