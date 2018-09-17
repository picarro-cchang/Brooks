from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log


def restart_app_via_rpc(app_name):
    # Set up and EventManagerProxy
    EventManagerProxy_Init(app_name)
    # Request a restart from Supervisor via RPC call
    restart = RequestRestart(app_name)
    if restart.requestRestart(app_name) is True:
        Log("Restart request to supervisor sent", Level=0)
    else:
        Log("Restart request to supervisor not sent", Level=2)


if __name__ == "__main__":
    restart_app_via_rpc(app_name="SpectrumCollector")
