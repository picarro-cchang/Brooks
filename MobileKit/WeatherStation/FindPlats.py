import numpy as np
import os
import sys
import sets
from Host.Common.namedtuple import namedtuple

NOT_A_NUMBER = 1e1000/1e1000
DEFAULT_PLATREFERENCE =  r"S:\Projects\Natural Gas Detection + P3\Files from PGE including TIFF maps\GEMS\georeference.txt"

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
            datAsCols.append(np.asarray([getattr(d,f) for d in datAsList]))
        return datAsList[0]._make(datAsCols)
    
def aReadDatFile(fileName):
    # Read a data file into a collection of numpy arrays
    return list2cols([x for x in xReadDatFile(fileName)])

class FindPlats(object):
    """Given a list of lats and longs and find out in which plats they lie
    """
    def __init__(self, platFile):
        if not os.path.exists(platFile):
            gp = file(DEFAULT_PLATREFERENCE,"r")
            self.names = []
            self.minlng = []
            self.maxlng = []
            self.minlat = []
            self.maxlat = []
            for i,line in enumerate(gp):
                if i > 0:
                    line = line.strip().strip('"')
                    atoms = line.split(',')
                    self.names.append(atoms[1].split("\\")[-1].split(".")[0])
                    a,b,c,d = [float(x) for x in atoms[2:6]]
                    self.minlng.append(a)
                    self.maxlng.append(b)
                    self.minlat.append(c)
                    self.maxlat.append(d)
            op = file(platFile,"wb")
            np.savez(op,names=np.asarray(self.names),minlng=np.asarray(self.minlng),maxlng=np.asarray(self.maxlng),
                        minlat=np.asarray(self.minlat),maxlat=np.asarray(self.maxlat))
        else:
            result = np.load(platFile,"rb")
            for f in result.files:
                exec("self.%s = result['%s']" % (f, f))
        self.argSorted = []
        self.argSorted.append(np.argsort(self.minlng))
        self.argSorted.append(np.argsort(self.maxlng))
        self.argSorted.append(np.argsort(self.minlat))
        self.argSorted.append(np.argsort(self.maxlat))

    def search(self, datFile, decimationFactor):
        platIndices = sets.Set()
        readIdx = 0
        for d in xReadDatFile(datFile):
            if readIdx % decimationFactor == 0:
                lng = d.GPS_ABS_LONG
                lat = d.GPS_ABS_LAT
                i1 = np.searchsorted(self.minlng[self.argSorted[0]],lng)
                i2 = np.searchsorted(self.maxlng[self.argSorted[1]],lng)
                i3 = np.searchsorted(self.minlat[self.argSorted[2]],lat)
                i4 = np.searchsorted(self.maxlat[self.argSorted[3]],lat)
                which = sets.Set(self.argSorted[0][:i1]) & sets.Set(self.argSorted[1][i2:]) & sets.Set(self.argSorted[2][:i3]) & sets.Set(self.argSorted[3][i4:])
                platIndices |= which
            readIdx += 1
        return sorted([self.names[w] for w in platIndices])
    
if __name__ == "__main__":
    app = FindPlats(r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\platBoundaries.npz")
    # print app.search(r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120323\DAT\FCDS2006-20120323-020431Z-DataLog_User_Minimal.dat", 30)
    dirname = r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120407\DAT"
    fname = r"FCDS2006-20120407-102214Z-DataLog_User_Minimal.dat"
    print fname
    print app.search(os.path.join(dirname,fname), 30)
