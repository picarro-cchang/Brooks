import numpy as np
import os
import sys
import sets
from Host.Common.namedtuple import namedtuple

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
            datAsCols.append(np.asarray([getattr(d,f) for d in datAsList]))
        return datAsList[0]._make(datAsCols)
    
def aReadDatFile(fileName):
    # Read a data file into a collection of numpy arrays
    return list2cols([x for x in xReadDatFile(fileName)])

# Given a list of lats and longs for leak positions, find out in which plats they lie
fname = "platBoundaries.npz"
if not os.path.exists(fname):
    grname = r"S:\Projects\Natural Gas Detection + P3\Files from PGE including TIFF maps\GEMS\georeference.txt";
    gp = file(grname,"r")
    names = []
    minlng = []
    maxlng = []
    minlat = []
    maxlat = []

    for i,line in enumerate(gp):
        if i>0:
            line = line.strip().strip('"')
            atoms = line.split(',')
            names.append(atoms[1].split("\\")[-1].split(".")[0])
            a,b,c,d = [float(x) for x in atoms[2:6]]
            minlng.append(a)
            maxlng.append(b)
            minlat.append(c)
            maxlat.append(d)
    op = file(fname,"wb")
    np.savez(op,names=np.asarray(names),minlng=np.asarray(minlng),maxlng=np.asarray(maxlng),
                minlat=np.asarray(minlat),maxlat=np.asarray(maxlat))
else:
    result = np.load(fname,"rb")
    resultAsDict = {}
    for f in result.files:
        resultAsDict[f] = result[f]
    locals().update(resultAsDict)

p1 = np.argsort(minlng)
p2 = np.argsort(maxlng)
p3 = np.argsort(minlat)
p4 = np.argsort(maxlat)

print p1

pkName = raw_input("Filename with coordinates to find? ");
platIndices = sets.Set()
for d in xReadDatFile(pkName):
    lng = d.GPS_ABS_LONG
    lat = d.GPS_ABS_LAT
    i1 = np.searchsorted(minlng[p1],lng)
    i2 = np.searchsorted(maxlng[p2],lng)
    i3 = np.searchsorted(minlat[p3],lat)
    i4 = np.searchsorted(maxlat[p4],lat)
    which = sets.Set(p1[:i1]) & sets.Set(p2[i2:]) & sets.Set(p3[:i3]) & sets.Set(p4[i4:])
    platIndices |= which
print sorted([names[w] for w in platIndices])
    
#platNames = ["45B09", "45B10", "45B11", "45C09", "45C10", "45C11", "45C12", "45C13", 
#             "45C14", "45C15", "45C16", "45E08", "45F08", "45F09", "45F10", "45F11"];
             