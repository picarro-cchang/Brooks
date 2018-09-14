from Host.ElectricalInterface.ElectricalInterface import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "ElectricalInterface"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()
