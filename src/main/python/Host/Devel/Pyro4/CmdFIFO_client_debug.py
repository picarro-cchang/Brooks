import CmdFIFO

RPC_PORT_TEST_CMDFIFO = 8000
RPC_PORT_TEST_CMDFIFO_CALLBACK = 8001

RPC = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_TEST_CMDFIFO, "Test_CmdFIFO",
                                 CallbackURI="http://localhost:%d" % RPC_PORT_TEST_CMDFIFO_CALLBACK,
                                 IsDontCareConnection=False)

print RPC.remoteProduct(45, 32)
