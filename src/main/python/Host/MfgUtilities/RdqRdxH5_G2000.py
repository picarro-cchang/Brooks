import os
import string
import sys
import numpy
from struct import *
from tables import *
import datetime

ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
UNIXORIGIN = datetime.datetime(1970,1,1,0,0,0,0)

def datetimeToTimestamp(t):
    td = t - ORIGIN
    return (td.days*86400 + td.seconds)*1000 + td.microseconds//1000

def getTimestamp():
    """Returns 64-bit millisecond resolution timestamp for instrument"""
    return datetimeToTimestamp(datetime.datetime.utcnow())

def timestampToUtcDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to UTC datetime"""
    return ORIGIN + datetime.timedelta(microseconds=1000*timestamp)

def timestampToLocalDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to local datetime"""
    offset = datetime.datetime.now() - datetime.datetime.utcnow()
    return timestampToUtcDatetime(timestamp) + offset

def formatTime(dateTime):
    ms = dateTime.microsecond//1000
    return dateTime.strftime("%Y/%m/%d %H:%M:%S") + (".%03d" % ms)

def unixTime(timestamp):
    dt = (ORIGIN-UNIXORIGIN)+datetime.timedelta(microseconds=1000*timestamp)
    return 86400.0*dt.days + dt.seconds + 1.e-6*dt.microseconds

def unixTimeToTimestamp(u):
    dt = UNIXORIGIN + datetime.timedelta(seconds=u)
    return datetimeToTimestamp(dt)

RDQ_TITLE_MAPPING = {
"Time (s)": "time",
"Monitor 1 ratio": "ratio1",
"Monitor 2 ratio": "ratio2",
"Uncorrected loss (ppm/cm)": "uncorrectedAbsorbance",
"Corrected loss (ppm/cm)": "correctedAbsorbance",
"PZT control": "pztValue",
"Wavenumber (1/km)": "waveNumber",
"Fit status": "fitStatus",
"Scheme status": "schemeStatus",
"Scheme identification": "subschemeId",
"Scheme counter": "count",
"Scheme table index": "schemeTable",
"Scheme row": "schemeRow",
"Wavenumber setpoint (1/km)": "waveNumberSetpoint",
"Etalon and laser select": "laserUsed",
"Fine laser current": "fineLaserCurrent"
}

RDX_TITLE_MAPPING = {
"Time (s)": "SensorTime_s",
"Cavity pressure (torr)": "CavityPressure",
"Cavity temperature (degC)": "CavityTemp",
"Laser temperature (degC)": "Laser1Temp",
"Etalon temperature (degC)": "EtalonTemp",
"Warm box temperature (degC)": "WarmBoxTemp",
"Laser TEC current monitor": "Laser1Tec",
"Warm Box TEC current monitor": "WarmBoxTec",
"Hot Box TEC current monitor": "HotBoxTec",
"Heater current monitor": "HotBoxHeater",
"Environment temperature (degC)": "DasTemp",
"Inlet proportional valve": "InletValve",
"Outlet proportional valve": "OutletValve",
"Solenoid valves": "ValveMask",
"Ambient pressure (torr)": "AmbientPressure",
"Auxiliary value 1": "SchemeID"
}

class RdqFile(object):
  def __init__(self,fname,decim=1,start=0,stop=None):
    """ Open a .rdq file and read data into an object """
    self.colnames = {}
    self.colindex = {}
    self.coltype = {}
    self.fname = fname
    self.decim = decim
    self.start = start
    self.stop = stop
    fp = file(fname,'rb')
    print "Reading ringdown results file"

    # Read column types
    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdq file")
      if string.find(line,'[Data column types]') >= 0 or string.find(line,'[Data_column_types]') >= 0:
        break
    while True:
      line = fp.readline()
      comps = [comp.strip() for comp in line.split("=",1)]
      if len(comps)<2: break
      self.coltype[int(comps[0])] = comps[1]
    # Make the format string for reading the binary data
    fmt = "="
    self.ncols = len(self.coltype)
    for i in range(self.ncols):
      if self.coltype[i]=="float": fmt += "f"
      else: fmt += "i"
    print "Format string for RDQ file: %s" % fmt

    # Read column names
    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdq file")
      if string.find(line,'[Data column names]') >= 0 or string.find(line,'[Data_column_names]') >= 0:
        break
    while True:
      line = fp.readline()
      comps = [comp.strip() for comp in line.split("=",1)]
      if len(comps)<2: break
      self.colnames[int(comps[0])] = RDQ_TITLE_MAPPING[comps[1]]
      self.colindex[comps[1]] = int(comps[0])

    # Read data
    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdq file")
      if string.find(line,'[Data]') >= 0:
        break
    # Find the zero byte which indicates the end of the header
    while True:
      ch = fp.read(1)
      if ch == '\0':
        break
    # Calculate number of records in the file
    nbytes = calcsize(fmt)
    startPos = fp.tell()
    fp.seek(0,2)
    endPos = fp.tell()
    numRec = (endPos - startPos)/nbytes
    print "Number of records in file: %d" % numRec
    if self.stop is None:
        self.stop = numRec
    # Read in the data
    self.data = []
    for i in range(self.ncols):
      self.data.append(list())
    recNum = self.start
    while recNum < self.stop:
      try:
        fp.seek(startPos + recNum*nbytes)
        rec = fp.read(nbytes)
        if len(rec)<nbytes: break
        vals = unpack(fmt,rec)
        for i in range(self.ncols):
          self.data[i].append(vals[i])
        recNum += self.decim
      except IOError:
        break
    fp.close()

class RdxFile(object):
  def __init__(self,fname):
    """ Open a .rdx file and read data into an object """
    self.colnames = {}
    self.colindex = {}
    self.coltype = {}
    self.header = {}
    self.fname = fname
    fp = file(fname,'rb')
    print "Reading ringdown extension file"
    # Read header info
    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdx file")
      if string.find(line,'[CRDS Header]') >= 0 or string.find(line,'[CRDS_Header]') >= 0:
        break
    while True:
      line = fp.readline()
      comps = [comp.strip() for comp in line.split("=",1)]
      if len(comps)<2: break
      self.header[comps[0]] = comps[1]
   # Read column types
    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdx file")
      if string.find(line,'[Data column types]') >= 0 or string.find(line,'[Data_column_types]') >= 0:
        break
    while True:
      line = fp.readline()
      comps = [comp.strip() for comp in line.split("=",1)]
      if len(comps)<2: break
      self.coltype[int(comps[0])] = comps[1]
    # Make the format string for reading the binary data
    fmt = "="
    self.ncols = len(self.coltype)
    for i in range(self.ncols):
      if self.coltype[i]=="float": fmt += "f"
      else: fmt += "i"
    print "Format string for RDX file: %s" % fmt

    # Read column names
    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdx file")
      if string.find(line,'[Data column names]') or string.find(line,'[Data_column_names]') >= 0:
        break
    while True:
      line = fp.readline()
      comps = [comp.strip() for comp in line.split("=",1)]
      if len(comps)<2: break
      self.colnames[int(comps[0])] = RDX_TITLE_MAPPING[comps[1]]
      self.colindex[comps[1]] = int(comps[0])

    while True:
      line = fp.readline()
      if line == "":
        raise Exception("Unexpected end of .rdx file")
      if string.find(line,'[Data]') >= 0:
        break
    # Find the zero byte which indicates the end of the header
    while True:
      ch = fp.read(1)
      if ch == '\0':
        break
    # Read in the data
    nbytes = calcsize(fmt)
    self.data = []
    for i in range(self.ncols):
      self.data.append(list())
    while True:
      try:
        rec = fp.read(nbytes)
        if len(rec)<nbytes: break
        vals = unpack(fmt,rec)
        for i in range(self.ncols):
          self.data[i].append(vals[i])
      except IOError:
        break

if __name__ == "__main__":
    H5Filters = Filters(complevel=1,fletcher32=True)
    try:
        fname = sys.argv[1]
    except:
        fname = raw_input("Name of RDQ/RDX file? ")
    #fname = raw_input("Name of RDQ/RDX file? ")
    rdqname = fname+".rdq"
    rdxname = fname+".rdx"
    oname = fname+".h5"
    ofile = openFile(oname, "w")
    rdqData = RdqFile(rdqname)

    nRdqRows = len(rdqData.data[0])
    rdqDict = {}
    for i in range(rdqData.ncols):
        rdqDict[rdqData.colnames[i]] = [rdqData.data[i][j] for j in range(nRdqRows)]

    rdxData = RdxFile(rdxname)
    # Take average of each sensor data column
    for i in range(len(rdxData.data)):
        rdxData.data[i] = numpy.mean(rdxData.data[i])
    rdxDict = {}
    for i in range(rdxData.ncols):
        rdxDict[rdxData.colnames[i]] = rdxData.data[i]

    offset = float(rdxData.header['syncTimeSinceEpoch'])-float(rdxData.header['syncDasTime'])
    cavityPressure = rdxDict['CavityPressure']
    # Create HDF5 table file
    if len(rdqDict) > 0:
        rdqDict["waveNumber"] = 1e-5*numpy.array(rdqDict["waveNumber"])
        rdqDict["waveNumberSetpoint"] = 1e-5*numpy.array(rdqDict["waveNumberSetpoint"])
        sortedKeys = sorted(rdqDict.keys())
        # Convert list or tuple to array
        sortedValues = [numpy.array(rdqDict.values()[i]) for i in numpy.argsort(rdqDict.keys())]
        sortedKeys.append("timestamp")
        sortedKeys.append("cavityPressure")
        sortedValues.append(numpy.array([unixTimeToTimestamp(t+offset) for t in rdqDict["time"]]))
        sortedValues.append(cavityPressure*numpy.ones(len(sortedValues[0])))
        dataRec = numpy.rec.fromarrays(sortedValues, names=sortedKeys)
        ofile.createTable("/", "rdData", dataRec, "rdData", filters=H5Filters)

        # Look at count to split the file into spectra
        rowCounts = []
        rows = 0
        current = rdqDict["count"][0]
        for c in rdqDict["count"]:
            if c != current:
                rowCounts.append(rows)
                rows = 0
                current = c
            rows += 1
        rowCounts.append(rows)

    nSpec = len(rowCounts)
    if len(rdxDict) > 0:
        sortedKeys = sorted(rdxDict.keys())
        # Convert list or tuple to array
        sortedValues = [rdxDict.values()[i]*numpy.ones(nSpec) for i in numpy.argsort(rdxDict.keys())]
        dataRec = numpy.rec.fromarrays(sortedValues, names=sortedKeys)
        ofile.createTable("/", "sensorData", dataRec, "sensorData", filters=H5Filters)

    dataRec = numpy.rec.fromarrays([numpy.array(rowCounts),numpy.zeros(nSpec)], names=["RDDataSize","SpectrumQueueSize"])
    ofile.createTable("/", "controlData", dataRec, "controlData", filters=H5Filters)

    ofile.close()