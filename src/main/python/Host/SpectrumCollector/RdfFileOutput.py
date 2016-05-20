#!/usr/bin/python
"""
File Name: RdfFileOutput.py
Purpose: Writes out ringdown files in HDF5 format in a separate process to avoid memory growth issues with PyTables

File History:
    06-Feb-2014  sze   Initial version.

Copyright (c) 2014 Picarro, Inc. All rights reserved
"""
import multiprocessing
import threading
import numpy
import os
import Queue

from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR
from Host.Common import CmdFIFO

APP_NAME = "RdfFileOutput"

SpectrumCollector = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
                                     APP_NAME, IsDontCareConnection = False)

def work(parentPid, queue):
    """Function run within a separate process to save spectrum files and submit them for archiving

    Args:
        parentPid: Process ID of parent. This process terminates if the parent dies.
        queue: Queue holding commands and data to process. Each entry consists of a dictionary
            with a 'cmd' key that specifies the command type.
    """
    from tables import openFile, Filters
    from tables import Float32Col, Float64Col, Int16Col, Int32Col, Int64Col
    from tables import UInt16Col, UInt32Col, UInt64Col
    import psutil

    def fillRdfTables(fileName, spectraInScheme, attrs=None):
        """Transfer data from spectraInScheme to tables in an HDF5 output file.

        Args:
            fileName: Name of HDF5 file to receive spectra
            spectraInScheme: This is a list of dictionaries, one for each spectrum. Each spectrum consists
                of a dictionary with keys "rdData", "sensorData", "tagalongData" and "controlData". The
                values are tables of data (stored as a dictionary whose keys are the column names and whose
                values are lists of the column data) which are to be written to the output file.
            attrs: Dictionary of attributes to be written to HDF5 file
        """
        hdf5Filters = Filters(complevel=1, fletcher32=True)
        try:
            hdf5Handle = openFile(fileName, "w")
            if attrs is not None:
                for a in attrs:
                    setattr(hdf5Handle.root._v_attrs, a, attrs[a])
            # Lookup table giving pyTables column generation function keyed
            # by the numpy dtype.name
            colByName = dict(float32=Float32Col, float64=Float64Col,
                             int16=Int16Col, int32=Int32Col, int64=Int64Col,
                             uint16=UInt16Col, uint32=UInt32Col, uint64=UInt64Col)
            # We make HDF5 tables and define the columns needed in these tables
            tableDict = {}
            for spectrum in spectraInScheme:
                # Iterate over rdData, sensorData, tagalongData and controlData tables
                for tableName in spectrum:
                    spectTableData = spectrum[tableName]
                    if len(spectTableData) > 0:
                        keys, values = zip(*sorted(spectTableData.items()))
                        if tableName not in tableDict:
                            # We are encountering this table for the first time, so we
                            #  need to build up colDict whose keys are the column names and
                            #  whose values are the subclasses of Col used by pytables to
                            #  define the HDF5 column. These are retrieved from colByName.
                            colDict = {}
                            # Use numpy to get the dtype names for the various data
                            values = [numpy.asarray(v) for v in values]
                            for key, value in zip(keys, values):
                                colDict[key] = colByName[value.dtype.name]()
                            tableDict[tableName] = hdf5Handle.createTable(hdf5Handle.root, tableName, colDict, filters=hdf5Filters)
                        table = tableDict[tableName]
                        # Go through the arrays in values and fill up each row of the table
                        #  one element at a time
                        row = table.row
                        for j in range(len(values[0])):
                            for i, key in enumerate(keys):
                                row[key] = values[i][j]
                            row.append()
                        table.flush()
        finally:
            hdf5Handle.close()

    # Here follows the main loop of the process where commands are dispatched
    while True:
        try:
            req = queue.get(timeout=1)
            if req['cmd'] == 'stop':
                break
            elif req['cmd'] == 'writeFile':
                fileName = req['fileName']
                spectraInScheme = req['spectraInScheme']
                attrs = req['attrs']
                auxSpectrumFile = req['auxSpectrumFile']
                fillRdfTables(fileName, spectraInScheme, attrs)
                SpectrumCollector.archiveSpectrumFile(fileName, auxSpectrumFile)
        except Queue.Empty:
            if not psutil.pid_exists(parentPid): break   # To ensure process terminates if parent dies

class WriterProcess(object):
    """Encapsulates a writer process
    """
    def __init__(self):
        self.cmdQueue = multiprocessing.Queue()
        self.processHandle = multiprocessing.Process(target=work, args=(os.getpid(), self.cmdQueue,))
        self.numberSubmitted = 0

    def start(self):
        """Delegated to handle method to start process
        """
        self.processHandle.start()

    def submit(self, fileName, spectraInScheme, attrs, auxSpectrumFile):
        """Submit a set of spectra for writing out to a file and archiving

        Args:
            fileName: Name of HDF5 file to write the spectrum
            spectraInScheme: List of spectra, each of which is a dictionary containing numpy arrays
            attrs: Attributes to be written as metadata in the HDF5 file
            auxSpectrumFile: If not None, the spectrum file is also copied to this location
        """
        req = dict(cmd='writeFile', fileName=fileName, spectraInScheme=spectraInScheme,
                   attrs=attrs, auxSpectrumFile=auxSpectrumFile)
        self.numberSubmitted += 1
        self.cmdQueue.put(req)

    def requestTermination(self):
        """Request that the process terminates by enqueueing stop command
        """
        self.cmdQueue.put(dict(cmd='stop'))

class WriterManager(object):
    """Manages a collection of writer processes, killing each after it has done maxJobs jobs"""
    def __init__(self, maxJobs=10):
        self.writers = []
        self.lock = threading.Lock()
        self.maxJobs = maxJobs
        self.newWriterNeeded = True

    def submit(self, *args, **kwargs):
        """Submit a request to write out spectra, delegated to underlying WriterProcess.

        This also keeps track of the active writers and starts up new ones as needed.
        """
        self.lock.acquire()
        try:
            self.writers = [w for w in self.writers if w.processHandle.is_alive()]
            if self.newWriterNeeded:
                self.writers.append(WriterProcess())
                self.writers[-1].start()
                self.newWriterNeeded = False
            assert len(self.writers) >= 1, "List of writers should not be empty"
            writer = self.writers[-1]
            writer.submit(*args, **kwargs)
            if writer.numberSubmitted >= self.maxJobs:
                writer.requestTermination()
                self.newWriterNeeded = True
        finally:
            self.lock.release()

writerManager = WriterManager()

def writeSpectrumFile(fileName, spectraInScheme, attrs, auxSpectrumFile):
    """Externally visible entry point for this module"""
    writerManager.submit(fileName, spectraInScheme, attrs, auxSpectrumFile)