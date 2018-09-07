from Host.RDFrequencyConverter.RDFrequencyConverter import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "RDFrequencyConverter"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()
