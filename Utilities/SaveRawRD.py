#!/usr/bin/python
#
# FILE:
#   SaveRawRD.py
#
# DESCRIPTION:
#   Listen to the processed RD results queue and write them to an HDF5 file
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   15-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
from tables import *
from ctypes import *
from numpy import *
import os
import Queue
import time
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.timestamp import unixTime
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("SaveRawRD")

ctype2coltype = { c_byte:Int8Col, c_uint:UInt32Col, c_int:Int32Col, 
                  c_short:Int16Col, c_ushort:UInt16Col, c_longlong:Int64Col, 
                  c_float:Float32Col, c_double:Float64Col }

class SaveRawRD(object):
    def __init__(self):
        self.h5f = openFile("test.h5","w")
        self.queue = Queue.Queue()
        # Define a listener for the ringdown data
        self.listener = Listener(self.queue,SharedTypes.BROADCAST_PORT_RDRESULTS,RingdownEntryType,retry=True)
        self.colDict = { "DATE_TIME":Time64Col() }
        for name,cls in RingdownEntryType._fields_:
            self.colDict[name] = (ctype2coltype[cls])()
        TableType = type("TableType",(IsDescription,),self.colDict)
        filters = Filters(complevel=1,fletcher32=True)
        self.table = self.h5f.createTable(self.h5f.root,"results",TableType,filters=filters)
        self.numRec = 0
        
    def run(self):
        try:
            while True:
                entry = self.queue.get()
                row = self.table.row
                for name,cls in RingdownEntryType._fields_:
                    if name == "timestamp":
                        row["DATE_TIME"] = unixTime(entry.timestamp)
                    row[name] = getattr(entry,name)
                    self.numRec += 1
                row.append()
                if self.numRec % 500 == 0: sys.stdout.write(".")
        finally:
            self.table.flush()
            self.h5f.close()
            
if __name__ == "__main__":
    e = SaveRawRD()
    e.run()
