#!/usr/bin/python
"""
FILE:
  testStateDatabase.py

DESCRIPTION:
  Unit tests for the StateDatabase module

SEE ALSO:
  Specify any related information.

HISTORY:
  01-Dec-2013  sze  Initial version

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import ctypes
import os
import time
import threading
import unittest
import Queue
from Host.autogen import interface
from Host.Common.StateDatabase import SensorHistory, StateDatabase

scriptDir = os.path.dirname(os.path.realpath(__file__))

class StateDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.dbFile = os.path.join(scriptDir, "testSqlite.db")
        try:
            os.remove(self.dbFile)
        except WindowsError:
            pass
        time.sleep(0.1)

    def logFunc(self, message):
        self.message = message

    def test_InitializeStateDatabase(self):
        with self.assertRaises(ValueError) as context:
            StateDatabase()
        self.assertIn('Must specify fileName', context.exception.message)
        stateDb = StateDatabase(self.dbFile, self.logFunc)
        try:
            # Check that the database is a singleton
            stateDb2 = StateDatabase()
            self.assertEqual(id(stateDb), id(stateDb2))
        finally:
            # Check that we can close the database and stop the thread
            stateDb.close()
        time.sleep(1.0)
        # Make sure that the database file exists
        self.assertTrue(os.path.exists(self.dbFile))

    def idFetcher(self, threadNum):
        db = StateDatabase()
        for k in range(200):
            self.idQueue.put((threadNum, db.getId()))
            time.sleep(0)

    def test_GetId(self):
        stateDb = StateDatabase(self.dbFile, self.logFunc)
        try:
            # First get a range of IDs from a single thread
            idList = []
            for i in range(10):
                idList.append(stateDb.getId())
            self.assertEqual(idList, range(1,11))
            # Next start a collection of threads all of which are getting IDs
            self.idQueue = Queue.Queue()
            nThreads = 10
            threads = []
            for i in range(nThreads):
                thread = threading.Thread(target=self.idFetcher, args=(i,))
                thread.setDaemon(True)
                threads.append(thread)
            for thread in threads:
                thread.start()
            # Wait for all threads to finish
            for i, thread in enumerate(threads):
                thread.join()
            # Get the results from the queue, sort them and see if we got the correct ids
            idList = []
            while not self.idQueue.empty():
                idList.append(self.idQueue.get())
            idFound = sorted([id for threadNum, id in idList])
            self.assertEqual(len(idFound), nThreads * 200)
            self.assertEqual(idFound, range(11,11+len(idList)))
        finally:
            stateDb.close()

    def getFloatRegNames(self):
        # Get list of all floating point registers
        floatRegNames = []
        for regInfo in interface.registerInfo:
            if regInfo.type == ctypes.c_float:
                floatRegNames.append(regInfo.name)
        return floatRegNames

    def getIntRegNames(self):
        # Get list of all integer registers
        intRegNames = []
        for regInfo in interface.registerInfo:
            if regInfo.type == ctypes.c_uint:
                intRegNames.append(regInfo.name)
        return intRegNames

    def test_FloatReg(self):
        # Save some floating point registers and fetch them back
        print self.getIntRegNames()

if __name__ == "__main__":
    unittest.main()