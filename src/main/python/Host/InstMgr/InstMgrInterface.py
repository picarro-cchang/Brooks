from Host.Common import CmdFIFO
from Host.Common.SharedTypes import  RPC_PORT_INSTR_MANAGER

class InstMgrInterface(object):
    """Interface to the instrument manager RPC"""
    def __init__(self,config, clientName = "No client defined"):
        self.config = config
        self.loadConfig()
        self.instMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, ClientName = clientName)
        self.result = None
        self.exception = None
        self.rpcInProgress = False

    def loadConfig(self):
        pass