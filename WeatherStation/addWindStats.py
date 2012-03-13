# Add wind statistics columns to minimal data log
from scipy.interpolate import interp1d
from namedtuple import namedtuple
from numpy import *
import os

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
        
if __name__ == "__main__":
    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\MountainViewDrivearound_20120208\DAT\FCDS2003-20120208-223124Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\MountainViewDrivearound_20120208\GPSWS\windStats.txt';
    
    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\DAT\FCDS2003-20120213-223639Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\GPSWS\windStats.txt';
    
    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\20120213b\DAT\FCDS2003-20120213-223639Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\20120213b\GPSWS\windStats.txt';

    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120215\DAT\FCDS2003-20120215-235259Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120215\GPSWS\windStats.txt';

    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120216\DAT20120216-145816Z\FCDS2003-20120216-145816Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120216\GPSWS20120216-121652Z\windStats.txt';
    
    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120221\DAT\FCDS2003-20120221-195904Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120221\GPSWS\windStats.txt';
    
    #datlogName = r'R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\WindTests20120222\DAT\FCDS2006-20120222-221309Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\WindTests20120222\GPSWS\windStats-FCDS2006-20120222-203647Z.txt';

    #datlogName = r'R:\crd_G2000\FCDS\1135-FCDS2008\WeatherStationInstantaneousMode\Drive20120227\AnalyzerServer\FCDS2008-20120228-021939Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1135-FCDS2008\WeatherStationInstantaneousMode\Drive20120227\GPSWS\windStats.txt';

    #datlogName = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120220\DAT\FCDS2003-20120220-214652Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120220\GPSWS\windStats.txt'
    
    #datlogName = r'R:\crd_G2000\FCDS\1185-FCDS2010\Survey20120303\DAT\FCDS2010-20120303-200106Z-DataLog_User_Minimal.dat';
    #fwind = r'R:\crd_G2000\FCDS\1185-FCDS2010\Survey20120303\GPSWS_Inst\YYYwindStats-FCDS2010-20120303-181853Z.txt'

    datlogName = r'R:\crd_G2000\FCDS\1185-FCDS2010\DataFromAnalyzer\AnalyzerServer\FCDS2010-20120306-130727Z-DataLog_User_Minimal.dat';
    fwind = r'R:\crd_G2000\FCDS\1185-FCDS2010\Survey20120306\GPSWSInst\windStats-Composite-DataLog_GPS_Raw.dat.txt';
    
    wind = aReadDatFile(fwind)
    datlog = aReadDatFile(datlogName)
    itimes = datlog.EPOCH_TIME
    print min(itimes), max(itimes)
    print min(wind.EPOCH_TIME), max(wind.EPOCH_TIME)
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
    