#!/usr/bin/python
"""
FILE:
  testLocking.py

DESCRIPTION:
  Unit tests for locking

SEE ALSO:
  Specify any related information.

HISTORY:
  01-Dec-2013  sze  Initial version

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import os
import time
import threading
import unittest
import Queue

class LockExample(object):
    def __init__(self):
        self.idLock = threading.Lock()
        self.txId = 0
        
    def getId(self):
        self.idLock.acquire()
        self.txId += 1
        result = self.txId
        self.idLock.release()
        return result
    
    def close(self):
        pass

class LockExampleTestCase(unittest.TestCase):
    def setUp(self):
        self.obj = LockExample()
    
    def idFetcher(self, threadNum):
        for k in range(200):
            self.idQueue.put((threadNum, self.obj.getId()))
            time.sleep(0)
    
    def test_GetId(self):
        self.obj = LockExample()
        try:
            # First get a range of IDs from a single thread
            idList = []
            for i in range(10):
                idList.append(self.obj.getId())
            self.assertEqual(idList, range(1,11))
            # Next start a collection of threads all of which are 
            #  getting IDs
            self.idQueue = Queue.Queue()
            nThreads = 10
            threads = []
            for i in range(nThreads):
                thread = threading.Thread(target=self.idFetcher, args=(i,))
                thread.setDaemon(True)
                threads.append(thread)
            for thread in threads:
                thread.start()
            print "All threads started"
            # Wait for all threads to finish
            for i,thread in enumerate(threads):
                thread.join()
                print i,
            print
            # Get the results from the queue
            idList = [] 
            while not self.idQueue.empty():
                idList.append(self.idQueue.get())
            idFound = sorted([id for threadNum, id in idList])
            print max(idFound)
            print "Number of ids %d" % len(idFound)
            self.assertEqual(len(idFound), nThreads * 200)
            self.assertEqual(idFound, range(11,11+len(idList)))           
        finally:
            self.obj.close()

if __name__ == "__main__":
    unittest.main()
    