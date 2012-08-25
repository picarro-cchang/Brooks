#!/usr/bin/python
#
"""
File Name: SwathMaker.py
Purpose: Calculates the field of view associated with the data in a minimal data log file
which contains wind information 

File History:
    17-Apr-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
from collections import deque
import fnmatch
import itertools
from numpy import *
import os
import sys
import time
import traceback
from Host.Common.namedtuple import namedtuple
import ServerUtilities as su
import findFovWidth as fw

import urllib2
import urllib
import socket
try:
    import simplejson as json
except:
    import json
    
EARTH_RADIUS = 6378100
DTR = pi/180.0
RTD = 180.0/pi

class SwathMaker(object):
    def __init__(self,*args,**kwargs):
        if 'analyzerId' in kwargs:
            self.analyzerId = kwargs['analyzerId']
        else:
            self.analyzerId = "ZZZ"
        
        if 'appDir' in kwargs:
            self.appDir = kwargs['appDir']
        else:
            if hasattr(sys, "frozen"): #we're running compiled with py2exe
                AppPath = sys.executable
            else:
                AppPath = sys.argv[0]
            self.AppDir = os.path.split(AppPath)[0]

        if 'userlogfiles' in kwargs:
            self.userlogfiles = kwargs['userlogfiles']
        else:
            self.userlogfiles = '/data/mdudata/datalogAdd/*.dat'
            
        #if 'url' in kwargs:
        #    self.url = kwargs['url']
        #else:
        #    self.url = 'https://dev.picarro.com/node/rest/gdu/abcdefg/1.0/AnzLog'

        if 'timeout' in kwargs:
            self.timeout = int(kwargs['timeout'])
        else:
            self.timeout = 5

        if 'sleep_seconds' in kwargs:
            self.sleep_seconds = float(kwargs['sleep_seconds'])
        else:
            self.sleep_seconds = 30.0

        #if 'usedb' in kwargs:
        #    self.usedb = kwargs['usedb']
        #else:
        #    self.usedb = None
            
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
        
        if 'maxWidth' in kwargs:
            self.maxWidth = kwargs['maxWidth']
        else:
            self.maxWidth = 75  # Meters, determined by stability class
        
        self.noWait = 'nowait' in kwargs

    def makeCore(self,source):
        # We need to convert the latitudes and longitudes to Cartesians and
        #  extract just the epoch time, latitude, longitude, wind statistics and car speed
        latRef = None
        lngRef = None
        coreFields = ["EPOCH_TIME","GPS_FIT","GPS_ABS_LAT","GPS_ABS_LONG",
                      "ValveMask","WIND_N","WIND_E","WIND_DIR_SDEV","CAR_SPEED"]
        CoreTuple = namedtuple("CoreTuple",coreFields+["x","y"])
        for s in source:
            if s.GPS_FIT>=1 and (latRef is None):
                latRef = s.GPS_ABS_LAT
                lngRef = s.GPS_ABS_LONG
            if (latRef is not None) and (lngRef is not None):
                x,y = su.toXY(s.GPS_ABS_LAT,s.GPS_ABS_LONG,latRef,lngRef)
            else:
                x,y = 0.0,0.0
            yield CoreTuple(*([getattr(s,c) for c in coreFields]+[x,y]))
    
    def astd(self,wind,vcar):
        a = 0.15*pi
        b = 0.25
        c = 0.0
        return min(pi,a*(b+c*vcar)/(wind+0.01))
    
    def process(self,source):
        OutTuple = namedtuple("OutTuple",["EPOCH_TIME","GPS_ABS_LAT","GPS_ABS_LONG","DELTA_LAT","DELTA_LONG"])
        fovBuff = deque()
        N = 10              # Use 2*N+1 samples for calculating FOV
        for newdat in source:
            while len(fovBuff) >= 2*N+1: fovBuff.popleft()
            fovBuff.append(newdat)
            if len(fovBuff) == 2*N+1:
                d = fovBuff[N]
                lng = d.GPS_ABS_LONG
                lat = d.GPS_ABS_LAT
                cosLat = cos(lat*DTR)
                t = d.EPOCH_TIME
                fit = d.GPS_FIT
                windN = d.WIND_N
                windE = d.WIND_E
                vcar = d.CAR_SPEED
                dstd = DTR*d.WIND_DIR_SDEV
                mask = d.ValveMask
                if (fit>0) and (mask<1.0e-3):
                    bearing = arctan2(windE,windN)
                    wind = sqrt(windE*windE + windN*windN)
                    dmax = self.maxWidth
                    xx = asarray([fovBuff[i].GPS_ABS_LONG for i in range(2*N+1)])
                    yy = asarray([fovBuff[i].GPS_ABS_LAT for i in range(2*N+1)])
                    xx = DTR*(xx-lng)*EARTH_RADIUS*cosLat
                    yy = DTR*(yy-lat)*EARTH_RADIUS
                    dstd = sqrt(dstd**2 + self.astd(wind,vcar)**2)
                    width = fw.maxDist(xx,yy,N,windE,windN,dstd,dmax,thresh=0.7,tol=1.0)
                    deltaLat = RTD*width*cos(bearing)/EARTH_RADIUS
                    deltaLng = RTD*width*sin(bearing)/(EARTH_RADIUS*cosLat)
                else:
                    deltaLat = 0.0
                    deltaLng = 0.0
                if isnan(deltaLat) or isnan(deltaLng):
                    deltaLat = 0.0
                    deltaLng = 0.0
                yield OutTuple(t,lat,lng,deltaLat,deltaLng)            
        
    def run(self):
        while True:
            # Getting source by monitoring latest file matching name
            try:
                fname = su.genLatestFiles(*os.path.split(self.userlogfiles)).next()
            except:
                fname = None
                time.sleep(self.sleep_seconds)
                print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                headerWritten = False
                # Make a generator which yields lines as a dictionary
                if self.noWait:
                    source = su.sourceFromFile(fname)
                else:
                    source = su.followLastUserFile(fname)
                for s in self.process(su.textAsTuple(source)): 
                    if not headerWritten:
                        swathFile = os.path.splitext(fname)[0] + '.swath'
                        op = open(swathFile,'wb+',0)
                        op.write((len(s._fields)*"%-14s"+"\r\n") % tuple(s._fields))
                        headerWritten = True
                    op.write(("%-14.2f%-14.6f%-14.6f%-14.6f%-14.6f\r\n") % tuple([getattr(s,h) for h in s._fields]))
                op.close()        
            if self.noWait: break
