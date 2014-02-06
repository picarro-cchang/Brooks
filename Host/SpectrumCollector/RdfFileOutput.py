#!/usr/bin/python
"""
File Name: RdfFileOutput.py
Purpose: Writes out ringdown files in HDF5 format, possibly in a separate process

File History:
    06-Feb-2014  sze   Initial version.

Copyright (c) 2014 Picarro, Inc. All rights reserved
"""
import numpy

from tables import openFile, Filters
from tables import Float32Col, Float64Col, Int16Col, Int32Col, Int64Col
from tables import UInt16Col, UInt32Col, UInt64Col

from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR
from Host.Common import CmdFIFO

APP_NAME = "RdfFileOutput"

SpectrumCollector = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
                                     APP_NAME, IsDontCareConnection = False)
    
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

def writeSpectrumFile(fileName, spectraInScheme, attrs, auxSpectrumFile):
    fillRdfTables(fileName, spectraInScheme, attrs)
    SpectrumCollector.archiveSpectrumFile(fileName, auxSpectrumFile)
