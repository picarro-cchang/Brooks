from Host.Common import CmdFIFO
from Host.Common.EventManagerProxy import Log
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR


class RequestRestart(object):
    def __init__(self, APP_NAME):
        """
        This class will send an RPC call to the Supervisor requesting a restart.
        The main intention of this functionality is to wrap an application's main
        loop in a try/except block. In the except block this class can be used to
        have Supervisor restart any application that encounters an unhandled exception.
        Ideally we wouldn't need this class.. but for now, we do.

        :param APP_NAME: Name of the application you wish to restart. This variable can
            typically be found at the header of any individual application's source.
        """
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME,
                                                     IsDontCareConnection=False)
        self.APP_NAME = APP_NAME
        self.status = None

    def requestRestart(self, APP_NAME):
        """
        This function sends the RPC call to Supervisor requesting it to restart
        the application that made the RPC call.

        :param APP_NAME: Name of the application requesting a restart
        :return: Boolean: Message Sent/Not-Sent
        """
        try:
            Log("%s is requesting a restart from Supervisor" % APP_NAME, Level=0)
            self.supervisor.RestartApplications(APP_NAME, True)
            return True
        except:
            return False
