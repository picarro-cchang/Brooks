# Test Suite for CmdFIFO

import CmdFIFO_Pyro3 as CmdFIFO
import pytest
import threading
import time

RPC_PORT_TEST_CMDFIFO = 8000
RPC_PORT_TEST_CMDFIFO_CALLBACK = 8001

# Functions to make available for remote calls

class RpcProvider(object):
    def __init__(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_TEST_CMDFIFO),
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

@pytest.fixture(scope="function")
def CBServer(request):
    CBServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_TEST_CMDFIFO_CALLBACK),
                                    ServerName="TestCmdFIFO_Callback",
                                    ServerDescription="Callback server",
                                    threaded=True)
    cbThread = threading.Thread(target=CBServer.serve_forever)
    cbThread.setDaemon(True)
    cbThread.start()
    def fin():
        CBServer.Stop()
        cbThread.join()
    request.addfinalizer(fin)
    return CBServer

@pytest.fixture(scope="class")
def RPC(request):
    RPC = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_TEST_CMDFIFO, "Test_CmdFIFO",
                                                CallbackURI = "http://localhost:%d" % RPC_PORT_TEST_CMDFIFO_CALLBACK,
                                                IsDontCareConnection = False) 
    
    server = RpcProvider().rpcServer
    server.Launch()
    def fin():
        RPC.CmdFIFO.StopServer()
        server.Stop()
    request.addfinalizer(fin)
    return RPC

class TestKill(object):
    def test_killServer(self):
        def connectAndDelay(x):
            cp = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_TEST_CMDFIFO,
                                           "Test_CmdFIFO", IsDontCareConnection = False)
            cp.CmdFIFO.DebugDelay(x)
        RPC = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_TEST_CMDFIFO, "Test_CmdFIFO",
                                          IsDontCareConnection = False) 
        
        server = RpcProvider().rpcServer
        server.Launch()
        assert RPC.remoteProduct(2,5) == 10, "Error in remoteProduct"
        threading.Thread(target=connectAndDelay,args=(10,))
        RPC.CmdFIFO.KillServer("please")
        server.Stop()
    
class TestClass(object):
    def test_success1(self,RPC):
        assert RPC.remoteProduct(2,5) == 10, "Error in remoteProduct"
    def test_success2(self,RPC):
        assert RPC.remoteQuotient(5,2) == 2, "Error in remoteQuotient integer division"
    def test_success3(self,RPC):
        assert RPC.remoteQuotient(5.0,2) == 2.5, "Error in remoteQuotient floating point division"
    def test_success4(self,RPC):
        assert RPC.remoteQuotient(y=2, x=10) == 5, "Error in remoteQuotient named argument handling"
    def test_success5(self,RPC):
        assert RPC.remoteQuotient(**dict(y=2, x=10)) == 5, "Error in remoteQuotient keyword handling"
    def test_success6(self,RPC):
        assert RPC.remoteVarSum(1,2,3,4) == 10, "Error in remoteVarSum"
    
    def test_raise1(self,RPC):
        with pytest.raises(ZeroDivisionError) as excinfo:
            q = RPC.remoteQuotient(5,0)
    def test_raise2(self,RPC):
        with pytest.raises(TypeError) as excinfo:
            RPC.remoteProduct(1,2,3,4)
        assert 'remoteProduct' in excinfo.value.message
        assert 'takes exactly 3 arguments' in excinfo.value.message
    def test_raise3(self,RPC):
        with pytest.raises(CmdFIFO.CmdFIFOError) as excinfo:
            RPC.nonexistent()
        assert 'nonexistent' in excinfo.value.message
        assert 'not supported' in excinfo.value.message
        
    def test_system_methods1(self,RPC):
        methodList = RPC.system.listMethods()
        assert 'remoteProduct' in methodList
        assert 'remoteQuotient' in methodList
    def test_system_methods2(self,RPC):
        assert 'method not found' in RPC.system.methodHelp('nonExistent')
        assert 'method not found' in RPC.system.methodSignature('nonExistent')
    def test_system_methods3(self,RPC):
        assert '(self, x, y)' == RPC.system.methodSignature('remoteProduct')
    def test_system_methods4(self,RPC):
        assert 'Computes quotient of x and y' == RPC.system.methodHelp('remoteQuotient')
        
    def test_queueing1(self,RPC):
        def connectAndDelay(x):
            cp = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_TEST_CMDFIFO,
                                           "Test_CmdFIFO", IsDontCareConnection = False)
            cp.CmdFIFO.DebugDelay(x)
            
        start = time.time()
        RPC.CmdFIFO.DebugDelay(0.1)
        assert abs(time.time() - start - 0.1) < 0.05, "Incorrect delay for single call"
        # Start two other delay calls in threads, then make a third call in the main thread
        #  This should not complete until all the delays are done. Note that we are using different
        #  proxies for the calls so that the call made using the RPC object does not have to wait
        #  for the delays to complete
        start = time.time()
        threading.Thread(target=connectAndDelay, args=(0.2,)).start()
        threading.Thread(target=connectAndDelay, args=(0.3,)).start()
        threading.Thread(target=connectAndDelay, args=(0.2,)).start()
        time.sleep(0.1)
        assert RPC.CmdFIFO.GetQueueLength() == 3, "Incorrect number of pending requests"
        assert abs(time.time() - start - 0.1) < 0.05, "Priority call to GetQueueLength not at expected time"
        RPC.CmdFIFO.DebugDelay(0.3)
        assert abs(time.time() - start - 1.0) < 0.05, "Incorrect delay for sequence of calls"

    def test_queueing2(self,RPC):
        def connectAndDelay(x):
            cp = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_TEST_CMDFIFO,
                                           "Test_CmdFIFO", IsDontCareConnection = False)
            cp.CmdFIFO.DebugDelay(x)
            
        start = time.time()
        RPC.CmdFIFO.DebugDelay(0.1)
        assert abs(time.time() - start - 0.1) < 0.05, "Incorrect delay for single call"
        # Start two other delay calls in threads, then make a third call in the main thread
        #  This should not complete until all the delays are done. Note that we are using the same
        #  proxy for the calls unlike in the previous test
        start = time.time()
        threading.Thread(target=lambda x: RPC.CmdFIFO.DebugDelay(x), args=(0.2,)).start()
        threading.Thread(target=lambda x: RPC.CmdFIFO.DebugDelay(x), args=(0.3,)).start()
        threading.Thread(target=lambda x: RPC.CmdFIFO.DebugDelay(x), args=(0.2,)).start()
        time.sleep(0.1)
        # Since we use the SAME proxy (RPC), the calls are handled in sequence and the queue length is zero
        assert RPC.CmdFIFO.GetQueueLength() == 0, "Incorrect number of pending requests"
        assert abs(time.time() - start - 0.7) < 0.05, "Call to GetQueueLength not at expected time"
        RPC.CmdFIFO.DebugDelay(0.3)
        assert abs(time.time() - start - 1.0) < 0.05, "Incorrect delay for sequence of calls"

    def test_callback_server(self,RPC,CBServer):
        callbackResult = {}
        def myCallback(retVals, fault):
            callbackResult['retVals'] = retVals
            callbackResult['fault'] = fault
        CBServer.register_callback_function(myCallback)
        RPC.SetFunctionMode("remoteDelay", FuncMode = CmdFIFO.CMD_TYPE_Callback, Callback = myCallback)
        start = time.time()
        assert RPC.remoteDelay(0.5) == "CB"
        assert abs(time.time() - start) < 0.05 # Should return quickly
        time.sleep(1.0)
        assert abs(callbackResult['retVals'] - start - 0.5) < 0.05 # Correct delay

    def test_simple_callback(self,RPC):
        callbackResult = {}
        def myCallback(retVals, fault):
            callbackResult['retVals'] = retVals
            callbackResult['fault'] = fault
            
        callbackServer = CmdFIFO.CmdFIFOSimpleCallbackServer(("localhost",RPC_PORT_TEST_CMDFIFO_CALLBACK),
                                                              CallbackList=(myCallback,))
        RPC.SetFunctionMode("remoteDelay", FuncMode = CmdFIFO.CMD_TYPE_Callback, Callback = myCallback)
        callbackServer.Launch()
        start = time.time()
        assert RPC.remoteDelay(0.5) == "CB"
        assert abs(time.time() - start) < 0.05 # Should return quickly
        time.sleep(1.0)
        assert abs(callbackResult['retVals'] - start - 0.5) < 0.05 # Correct delay
        callbackServer.Server._CmdFIFO_StopServer()
        