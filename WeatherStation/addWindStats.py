# Add wind statistics columns to minimal data log
from scipy.interpolate import interp1d
from namedtuple import namedtuple
from numpy import *
import os

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
            yield DataTuple(*[float(v) for v in l.split()])
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
        
if __name__ == "__main__":
    datlogName = r'ConcordData\FCDS2003-20120203-224635Z-DataLog_User_Minimal.dat';
    fwind = 'windStats20120203.txt';
    
    wind = aReadDatFile(fwind)
    datlog = aReadDatFile(datlogName)
    itimes = datlog.EPOCH_TIME

    newFields = []
    for n in wind._fields:
        if n == "EPOCH_TIME": continue
        f = interp1d(wind.EPOCH_TIME,getattr(wind,n))
        newFields.append(f(itimes))
    # Write out the new file
    op = file('withWind.dat','w')
    for n in datlog._fields:
        op.write("%-26s" % n)
    for n in wind._fields:
        if n == "EPOCH_TIME": continue
        op.write("%-26s" % n)
    op.write("\n")
    nRows = len(itimes)
    for i in range(nRows):
        for n in datlog._fields:
            if n in ["EPOCH_TIME"]:
                op.write("%-26.3f" % getattr(datlog,n)[i])
            elif n in ["ALARM_STATUS","INST_STATUS"]:
                op.write("%-26d" % getattr(datlog,n)[i])
            else:
                op.write("%-26.10e" % getattr(datlog,n)[i])
        j = 0
        for n in wind._fields:
            if n == "EPOCH_TIME": continue
            op.write("%-26.10e" % newFields[j][i])
            j += 1
        op.write("\n")
    op.close()
    