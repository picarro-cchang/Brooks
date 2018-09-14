from Host.Supervisor.Supervisor import start
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "Supervisor"
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if __name__ == "__main__":
    start()
