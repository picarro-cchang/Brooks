from Host.Common import CmdFIFO
from Host.Common.EventManagerProxy import Log
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR


class RequestRestart(object):
    def __init__(self, APP_NAME):
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        self.APP_NAME = APP_NAME

    def requestRestart(self, APP_NAME):
        Log("%s is requesting a restart from Supervisor" % APP_NAME)
        self.supervisor.RestartApplications(APP_NAME, True)
