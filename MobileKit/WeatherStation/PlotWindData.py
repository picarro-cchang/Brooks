import PIL
import cStringIO
from PIL import Image
from PIL import ImageDraw, ImageFont
import httplib
import numpy as np
import csv
import os
import sys
import sets
import threading
import traceback
from Host.Common.namedtuple import namedtuple
from FindPlats import FindPlats
from configobj import ConfigObj
import datetime
from Host.Common import timestamp as ts
import pylab as pl
import time
import scipy.signal as sp

ORIGIN = datetime.datetime(2012,1,1,0,0,0,0)
UNIXORIGIN = datetime.datetime(1970,1,1,0,0,0,0)
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
        
if __name__ == "__main__":
    fnames = [r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120320\site 1 master.csv',
              r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120320\site 2 master.csv',
              #r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120320\site 3 master.csv',
              #r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120320\site 4 master.csv'
             ]
             
    windFile = r'R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120320\GPS_WS\windStats-Composite.txt'
         
    SITE = 0
    DAY = 1
    MINUTE = 2
    SECONDS = 3
    WS = 4
    WD = 5
    
    for fname in fnames:
        site, day, minute, seconds, ws, wd = [], [], [], [], [], []
        cp = open(fname,"rb")
        reader = csv.reader(cp)
        for row in reader:
            site.append(int(row[SITE]))
            day.append(int(row[DAY]))
            minute.append(int(row[MINUTE]))
            seconds.append(int(row[SECONDS]))
            ws.append(float(row[WS]))
            wd.append(float(row[WD]))

        site = np.asarray(site)
        day = np.asarray(day)
        minute = np.asarray(minute)
        hour = minute//100
        minute = minute % 100
        seconds = np.asarray(seconds)
        ws = np.asarray(ws)
        wd = np.asarray(wd)
        tzOffset = 7    # Hours that UTC is ahead of local (PDT)
        dts = [ORIGIN+datetime.timedelta(seconds=float(s)) for s in ((((day-1)*24+hour+tzOffset)*60)+minute)*60+seconds]
        epochTime = np.asarray([ts.unixTime(ts.datetimeToTimestamp(dt)) for dt in dts])
        good = epochTime>time.mktime((2012,3,20,6,0,0,0,1,-1))
        t1 = epochTime[good]
        ws1 = ws[good]
        wd1 = wd[good]
        wind1 = ws1*np.exp(1j*wd1*np.pi/180.0)
        wind2 = sp.lfilter(np.ones(10,dtype=float)/10.0,1,wind1)
        pl.figure(1)
        pl.plot(t1,abs(wind2))
        pl.xlabel('Epoch Time')
        pl.ylabel('Wind Speed')
        pl.grid(True)
        pl.figure(2)
        pl.plot(t1,180/np.pi*np.angle(wind2))
        pl.xlabel('Epoch Time')
        pl.ylabel('Wind Bearing')
        pl.grid(True)
        
    p3wind = aReadDatFile(windFile)
    t3 = p3wind.EPOCH_TIME
    w3 = p3wind.WIND_N + 1j*p3wind.WIND_E
    good = t3>time.mktime((2012,3,20,8,0,0,0,1,-1))
    t3 = t3[good]
    w3[np.isnan(w3)] = 0
    w3 = w3[good]
    wind3 = sp.lfilter(np.ones(20,dtype=float)/20.0,1,w3)    
    pl.figure(1)
    pl.plot(t3,abs(w3))
    pl.figure(2)
    pl.plot(t3,180/np.pi*np.angle(w3))
        
    pl.show()
    