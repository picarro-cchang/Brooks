# Add wind statistics columns to minimal data log
from scipy.interpolate import interp1d
from Host.Common.namedtuple import namedtuple
from numpy import *
import os
import sys
import traceback
from configobj import ConfigObj
from PeakFinder import PeakFinder

NOT_A_NUMBER = 1e1000/1e1000
def pFloat(x):
    try:
        return float(x)
    except:
        return NOT_A_NUMBER
        
def xReadDatFile(fileName):
            
    # Read a data file with column headings and yield a list of named tuples with the file contents
    fp = open(fileName,'r')
    headerLine = True
    for l in fp:
        if headerLine:
            colHeadings = l.split()
            DataTuple = namedtuple("Bunch",colHeadings)
            headerLine = False
        else:
            yield DataTuple(*[pFloat(v) for v in l.split()])
    fp.close()

def list2cols(datAsList):
    datAsCols = []
    if datAsList:
        for f in datAsList[0]._fields:
            datAsCols.append(asarray([getattr(d,f) for d in datAsList]))
        return datAsList[0]._make(datAsCols)
    
def aReadDatFile(fileName):
    # Read a data file into a collection of numpy arrays
    return list2cols([x for x in xReadDatFile(fileName)])

class AddWindBatch(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        if not self.config:
            raise ValueError("Error opening configuration file %s" % iniFile)
        
    def addGpsWind(self):
        if not os.path.exists(self.outDir): os.makedirs(self.outDir)
        offset = self.analyzerOffset # Time between ringdown measurement and derived wind data 
        windFileName = os.path.join(self.windDir,self.windFile)
        wind = aReadDatFile(windFileName)
            
        datlogName = os.path.join(self.datDir,self.datFile)
        datlog = aReadDatFile(datlogName)
        itimes = datlog.EPOCH_TIME
        print min(itimes), max(itimes)
        print min(wind.EPOCH_TIME), max(wind.EPOCH_TIME)
        newFields = {}
        for n in wind._fields:
            if n == "EPOCH_TIME": continue
            f = interp1d(wind.EPOCH_TIME,getattr(wind,n))
            newFields[n] = f(itimes+offset)
        if self.gpsFile is not None:
            gpsFileName =  os.path.join(self.windDir,self.gpsFile)
            gps = aReadDatFile(gpsFileName)
            for n in gps._fields:
                if n == "EPOCH_TIME": continue
                f = interp1d(gps.EPOCH_TIME,getattr(gps,n))
                newFields[n] = f(itimes+offset)
        # Write out the new file
        self.outFile = os.path.join(self.outDir,os.path.split(self.datFile)[-1])
        op = file(self.outFile,'w')
        allFields = []
        for n in datlog._fields + wind._fields:
            if n not in allFields: allFields.append(n)
            
        for n in allFields:
            op.write("%-26s" % n)
        op.write("\n")
        nRows = len(itimes)
        for i in range(nRows):
            for n in allFields:
                if n in ["EPOCH_TIME"]:
                    op.write("%-26.3f" % getattr(datlog,n)[i])
                elif n in ["ALARM_STATUS","INST_STATUS"]:
                    op.write("%-26d" % getattr(datlog,n)[i])
                elif n in newFields:
                    op.write("%-26.10e" % newFields[n][i])
                else:
                    op.write("%-26.10e" % getattr(datlog,n)[i])
            op.write("\n")
        op.close()

        
    def run(self):
        varList = {'DAT_DIR':'datDir','OUT_DIR':'outDir','GPS_WS_DIR':'windDir','GPS_FILE':'gpsFile',
                   'WIND_FILE':'windFile','DAT_FILE':'datFile','ANALYZER_OFFSET':'analyzerOffset'}
        
        for secName in self.config:
            if secName == 'DEFAULTS': continue
            if 'DEFAULTS' in self.config:
                for v in varList:
                    if v in self.config['DEFAULTS']: 
                        setattr(self,varList[v],self.config['DEFAULTS'][v])
                    else: 
                        setattr(self,varList[v],None)
            for v in varList:
                if v in self.config[secName]: 
                    setattr(self,varList[v],self.config[secName][v])
            self.analyzerOffset = float(self.analyzerOffset)
            
            try:
                print "Processing",os.path.join(self.datDir,self.datFile)
                self.addGpsWind()
                pf = PeakFinder()
                pf.userlogfiles = self.outFile
                pf.debug = False
                pf.noWait = True
                pf.minAmpl = 0.01
                pf.run()
                
            except Exception:
                print traceback.format_exc()


    
if __name__ == "__main__":
    app = AddWindBatch(sys.argv[1])
    app.run()
