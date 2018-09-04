from Host.EventManager.EventManager import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "EventManager"
EventManagerProxy_Init(APP_NAME)

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


def main():
    main()


if __name__ == "__main__":
    main()