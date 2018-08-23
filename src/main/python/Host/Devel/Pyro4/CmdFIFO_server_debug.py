# Test Suite for CmdFIFO

import CmdFIFO
import time

RPC_PORT_TEST_CMDFIFO = 8000
RPC_PORT_TEST_CMDFIFO_CALLBACK = 8001

# Functions to make available for remote calls


class RpcProvider(object):
    def __init__(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(
            ("", RPC_PORT_TEST_CMDFIFO),
            ServerName="TestCmdFIFO",
            ServerDescription="Test server for CmdFIFO functionality",
            threaded=True)
        self.rpcServer.register_function(self.remoteProduct)
        self.rpcServer.register_function(self.remoteQuotient)
        self.rpcServer.register_function(self.remoteVarSum)
        self.rpcServer.register_function(self.remoteDelay)

    def remoteProduct(self, x, y):
        "Computes product of x and y"
        return x*y

    def remoteQuotient(self, x, y):
        "Computes quotient of x and y"
        return x/y

    def remoteVarSum(self, *a):
        "Computes sum of any number of arguments"
        return sum([x for x in a])

    def remoteDelay(self, x):
        "Delay by x seconds and return epoch time at completion"
        time.sleep(x)
        return time.time()

if __name__ == "__main__":
    server = RpcProvider().rpcServer
    server.Launch()
    while True:
        time.sleep(1.0)