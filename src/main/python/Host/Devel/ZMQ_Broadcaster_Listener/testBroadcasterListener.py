# testBroadcasterListener

from Broadcaster import Broadcaster
from Listener import Listener
from TextListener import TextListener
import pytest
import Queue
import threading
import time

def myLog(msg):
    print msg
    
class BroadcastStream(object):
    def __init__(self, port):
        self.port = port
        self.sending = True
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()
    def run(self):
        self.broadcaster = Broadcaster(self.port, "broadcaster:%d" % self.port,logFunc=myLog,sendHwm=10)
        count = 0
        while self.sending:
            time.sleep(0.1)
            self.broadcaster.send("test message %d\n" % count)
            count += 1
        self.broadcaster.stop()
    def stop(self):
        self.sending = False
        self.thread.join()

@pytest.fixture(scope="function")
def broadcaster(request):
    broadcaster = BroadcastStream(request.cls.port)
    def fin():
        broadcaster.stop()
    request.addfinalizer(fin)
    return broadcaster

class TestBroadcasterListener(object):
    port = 8881
    def testSimple1(self, broadcaster):
        queue = Queue.Queue(0)
        textListener = TextListener(queue, self.port)
        for i in range(10):
            print queue.get()
        textListener.stop()
        textListener.join()
    def testSimple2(self, broadcaster):
        queue = Queue.Queue(0)
        textListener = TextListener(queue, self.port)
        for i in range(10):
            print queue.get()
        textListener.stop()
        textListener.join()
