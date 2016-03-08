from Host.Utilities.RestartSupervisor.RestartSupervisor import RestartSupervisor, handleCommandSwitches
from Host.Common.SingleInstance import SingleInstance

if __name__ == "__main__":
    restartSupervisorApp = SingleInstance("RestartSupervisor")
    if restartSupervisorApp.alreadyrunning():
        print "Instance of RestartSupervisor application is already running"
    else:
        configFile, options = handleCommandSwitches()
        app = RestartSupervisor(configFile)
        app.launch()
    print "Exiting program"
