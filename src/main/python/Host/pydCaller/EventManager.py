import threading
import time
from Host.EventManager.EventManager import HandleCommandSwitches, EventLogger

def LaunchViewerGUI(EL):
    import Host.EventManager.EventManagerGUI as EventManagerGUI
    logViewer = EventManagerGUI.LogViewer(EL.EventList, EventSourceCounter = EL.EventSourceCounter, EventSourceList = EL.EventSourceList)
    #Now link the EventLogger to the viewer...
    EL.Viewer = logViewer
    EL.ViewerUpdateFunc = logViewer.UpdateEventData
    #Launch the GUI app...
    logViewer.Launch() #This call blocks until GUI exit
    #Make sure we don't start it up again if we exited the GUI with the X
    EL.ShowViewer = False
    EL.Viewer = None
    EL.ViewerUpdateFunc = None
    #clean up so that we stay clean with this logger...

    del logViewer, EventManagerGUI

def Main():
    showViewer, configFile = HandleCommandSwitches()

    #create and kick off the event logging engine...
    EL = EventLogger(configFile)
    t = threading.Thread(target = EL.Launch)
    t.setDaemon(True)
    t.start()

    if showViewer:
        EL.ShowViewer = True

    #Now just loop and wait for the logger to shut down (while letting the
    #viewer app be on the main thread)...
    while not EL.LoggerStopped:
        if EL.ShowViewer:
            if EL.Viewer == None:
                #Need to start it up. Blocks until GUI exits.
                LaunchViewerGUI(EL)
        else:
            #We shouldn't be showing the viewer.
            assert not EL.Viewer, "Code error!  The viewer app should not be running at this time!"
        time.sleep(1.0)

if __name__ == "__main__":
    Main()