# Unit tests for the G2000 sample manager application

from unittest import main, TestCase
from mocker import MockerTestCase, Mocker, ANY, ARGS, KWARGS, MATCH
from Host.SampleManager.SampleManager import SampleManager
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.autogen import interface
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_SAMPLE_MGR, BROADCAST_PORT_SENSORSTREAM, STATUS_PORT_SAMPLE_MGR
import sys
#

class test_Config(MockerTestCase):
    def setUp(self):
        self.mock_Log = self.mocker.replace('Host.Common.EventManagerProxy.Log')
        self.mock_CustomConfigObj = self.mocker.replace('Host.Common.CustomConfigObj.CustomConfigObj')
        self.mock_SampleManager = self.mocker.mock()
    def test_LoadConfig(self):
        """The purpose of LoadConfig is to assign a ConfigObj specified by a file to the config attribute"""
        sampleConfig = CustomConfigObj(["[OK]"])
        self.mock_CustomConfigObj("test.ini")
        self.mocker.result(sampleConfig)
        self.mock_SampleManager.config = sampleConfig
        self.mocker.replay()
        # Success is indicated by return value
        self.assertTrue(SampleManager.LoadConfig.im_func(self.mock_SampleManager,"test.ini"))
    def test_IOError(self):
        """Test LoadConfig returns False if file cannot be opened"""
        self.mock_CustomConfigObj("test.ini")
        self.mocker.throw(IOError("File not found"))
        self.mock_Log("Unable to open config. <type 'exceptions.IOError'> File not found")
        self.mocker.replay()
        # Failure is indicated by return value
        self.assertFalse(SampleManager.LoadConfig.im_func(self.mock_SampleManager,"test.ini"))
    def test_otherError(self):
        """Test LoadConfig throws exception if some other error occurs"""
        self.mock_CustomConfigObj("test.ini")
        self.mocker.throw(ValueError("Some other error"))
        self.mocker.replay()
        # Failure is indicated by return value
        self.assertRaises(ValueError,SampleManager.LoadConfig.im_func,self.mock_SampleManager,"test.ini")

class test_RPCs(MockerTestCase):
    def test_RegisterRPCs(self):
        """Test of RPC function registration. Only class functions starting with RPC_ should be registered"""
        self.mock_SampleManager = self.mocker.mock()
        class MyClass(object):
            def RPC_func1(self):
                pass
            def foo(self):
                pass
            def RPC_func2(self):
                pass
            class RPC_notThis(object):
                pass
        obj = MyClass()
        self.mock_SampleManager.RpcServer.register_function(MATCH(lambda f:f.__name__ == 'RPC_func1'),'RPC_func1',NameSlice = 4)
        self.mock_SampleManager.RpcServer.register_function(MATCH(lambda f:f.__name__ == 'RPC_func2'),'RPC_func2',NameSlice = 4)
        self.mock_SampleManager.RpcServer.register_function(ARGS,KWARGS)
        self.mocker.call(lambda *a,**k: sys.stdout.write('REGISTER_FUNCTION:: %s, %s\n' % (a,k)))
        self.mocker.count(0)
        self.mocker.replay()
        SampleManager.RegisterRPCs.im_func(self.mock_SampleManager,obj)

        
        
class test_initSampleManager(MockerTestCase):
    def setUp(self):
        self.mock_Log = self.mocker.replace('Host.Common.EventManagerProxy.Log')
        self.mock_CustomConfigObj = self.mocker.replace('Host.Common.CustomConfigObj.CustomConfigObj')
        self.mock_SampleManager = self.mocker.mock()
        self.mock_Listener = self.mocker.replace('Host.Common.Listener.Listener')
        self.mock_Queue = self.mocker.replace('Queue.Queue')
        self.mock_Thread = self.mocker.replace('threading.Thread')
        
        # We do not expect any Log messages, so fail if they turn up
        self.mock_Log(ANY)
        self.mocker.call(lambda s: sys.stdout.write('LOG:: %s\n' % s))
        self.mocker.count(0,None)
        #
        self.mock_Listener(None,BROADCAST_PORT_SENSORSTREAM,interface.SensorEntryType,ARGS,KWARGS)        
        self.mock_Listener(ARGS,KWARGS)
        self.mocker.call(lambda *a,**k: sys.stdout.write('LISTENER:: %s, %s\n' % (a,k)))
        self.mocker.count(0,None)
        #
        self.mock_Thread(ARGS,KWARGS)
        self.mocker.call(lambda *a,**k: sys.stdout.write('THREAD:: %s, %s\n' % (a,k)))
        self.mocker.count(0,None)
    
        
    def test_StartThreads(self):
        """Test to see if sample manager starts up all threads"""
        sampleConfig = CustomConfigObj(["[DEFAULT_CONFIGS]","[MAIN]","Mode=ProportionalMode","[ProportionalMode]","script_filename=ProportionalMode"])
        self.mock_CustomConfigObj("test.ini")
        self.mocker.result(sampleConfig)
        self.mock_Thread(target=MATCH(lambda t:t.__name__ == "CmdHandler"))
        self.mocker.result(self.mock_Thread)
        self.mock_Thread(target=MATCH(lambda t:t.__name__ == "SolenoidHandler"))
        self.mocker.result(self.mock_Thread)
        self.mock_Thread(target=MATCH(lambda t:t.__name__ == "Monitor"))
        self.mocker.result(self.mock_Thread)
        self.mock_Thread.setDaemon(True)
        self.mocker.count(3)
        
        self.mocker.replay()
        s = SampleManager("test.ini")
    
if __name__ == "__main__":
    main()