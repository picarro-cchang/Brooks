from Host.ValveSequencer.ValveSequencerSimulator import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "ValveSequencer"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()
