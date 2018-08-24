from Host.Common import CmdFIFO
from Host.Common.EventManagerProxy import Log
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR


class RequestRestart(object):
    def __init__(self, APP_NAME):
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        self.APP_NAME = APP_NAME
        self.status = None

    def requestRestart(self, APP_NAME):
        try:
            Log("%s is requesting a restart from Supervisor" % APP_NAME)
            self.supervisor.RestartApplications(APP_NAME, True)
            self.status = True
        except:
            self.status = False
        return self.status

