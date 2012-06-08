#!/usr/bin/python
#
"""
File Name: ReportGenSupport.py
Purpose: Support for Surveyor report generation 

File History:
    26-Apr-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
import calendar
from collections import namedtuple
import copy
import cStringIO
import getFromP3 as gp3
import hashlib
try:
    import json
except:
    import simplejson as json
import math
import numpy as np
import os
import PIL.Image
import PIL.ImageDraw
import PIL.ImageMath
import SwathProcessor as sp
import sys
import threading
import time
import traceback
import urllib
import urllib2

RTD = 180.0/math.pi
DTR = math.pi/180.0
EARTH_RADIUS = 6378100

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]
PLAT_TIF_ROOT = r"S:\Projects\Picarro Surveyor\Files from PGE including TIFF maps\GEMS\CompTif\Gas\Distribution"
PLAT_PNG_ROOT = os.path.join(appDir,'static/plats')
if not os.path.exists(PLAT_PNG_ROOT): os.makedirs(PLAT_PNG_ROOT)

MapParams = namedtuple("MapParams",["minLng","minLat","maxLng","maxLat","nx","ny","padX","padY"])

fname = "platBoundaries.json"
fp = open(fname,"rb")
platBoundaries = json.loads(fp.read())
fp.close()

def overBackground(a,b,box):
    # Overlay the RGBA image a on top of an RGBA background image b, 
    #  where the color channels in b are multiplied by the alpha.
    #  Returns a reference to the modified image b, which can
    #  be used as the background in further operations.
    
    # Alternatively, b can be an RGB background image which is assumed
    #  to be opaque. The result is then an RGB image again with an 
    #  opaque background
    b.paste(a.convert('RGB'),box,a)
    return b

def backgroundToOverlay(im):
    r,g,b,a = im.split()
    r = PIL.ImageMath.eval("int(256*n/(d+1))",n=r,d=a).convert('L')
    g = PIL.ImageMath.eval("int(256*n/(d+1))",n=g,d=a).convert('L')
    b = PIL.ImageMath.eval("int(256*n/(d+1))",n=b,d=a).convert('L')
    return PIL.Image.merge("RGBA",(r,g,b,a))

def merge_dictionary(dst, src):
    stack = [(dst, src)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict) :
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst

def getStatus(fname):
    stDict = {}
    if os.path.exists(fname):
        sp = open(fname,"rb")
        try:
            stDict = json.load(sp)
        except:
            stDict = {}
        sp.close()
    return stDict
    
def updateStatus(fname,statusDict,init=False):
    dst = {}
    if not init:
        sp = open(fname,"rb")
        dst = json.load(sp)
        sp.close()
    sp = open(fname,"wb")
    json.dump(merge_dictionary(dst,statusDict),sp)
    sp.close()

def asPNG(image):
    output = cStringIO.StringIO()
    image.save(output,format="PNG")                
    try:
        return output.getvalue()
    finally:
        output.close()
        
def strToEtm(s):
    return calendar.timegm(time.strptime(s,"%Y-%m-%d  %H:%M"))

class CompositeMapMaker(object):
    def __init__(self,reportDir,ticket,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.region = region
        self.compositeMapFname = os.path.join(self.reportDir,"%s.compositeMap.%d.png" % (self.ticket,self.region))
        self.statusFname  = os.path.join(self.reportDir,"%s.compositeMap.%d.status" % (self.ticket,self.region))
        
    def getStatus(self):
        return getStatus(self.statusFname)
        
    def run(self):
        if "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.statusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
            try:
                files = {}
                imageFnames = {}
                statusFnames = {}
                for dirPath, dirNames, fileNames in os.walk(self.reportDir):
                    for name in fileNames:
                        atoms = name.split('.')
                        if atoms[0] == self.ticket and atoms[-2] == ("%d" % self.region) and atoms[-1] == 'png':
                            key = '.'.join(atoms[1:-2])
                            base = '.'.join(atoms[:-1])
                            # Having found a png file, look for the associated .status file
                            #  to see if the png file is valid
                            statusName = os.path.join(dirPath,base+'.status')
                            pngName = os.path.join(dirPath,name)
                            if "done" in getStatus(statusName):
                                try:
                                    files[key] = file(pngName,"rb").read()
                                    imageFnames[key] = pngName
                                    statusFnames[key] = statusName
                                except:
                                    pass
                layers = ['baseMap','pathMap','swathMap','wedgesMap','peaksMap']
                compositeImage = None
                for layer in layers:
                    if layer in files:
                        image = PIL.Image.open(cStringIO.StringIO(files[layer]))
                        if compositeImage is None:
                            compositeImage = PIL.Image.new('RGBA',image.size,(0,0,0,0))
                        compositeImage = overBackground(image,compositeImage,None)
                        # Remove the component status and image files
                        os.remove(statusFnames[layer])
                        os.remove(imageFnames[layer])
                op = open(self.compositeMapFname,"wb")
                op.write(asPNG(compositeImage))
                op.close()
                updateStatus(self.statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})
    
class LayerFilenamesGetter(object):
    def __init__(self,reportDir,ticket):
        self.reportDir = reportDir
        self.ticket = ticket
    def run(self):
        files = {}
        for dirPath, dirNames, fileNames in os.walk(self.reportDir):
            for name in fileNames:
                atoms = name.split('.')
                if atoms[0] == self.ticket and atoms[-1] == 'png':
                    key = '.'.join(atoms[1:-1])
                    files[key] = name
        return files
    
class ReportStatus(object):
    def __init__(self,reportDir,ticket):
        self.reportDir = reportDir
        self.ticket = ticket
    def run(self):
        files = {}
        for dirPath, dirNames, fileNames in os.walk(self.reportDir):
            for name in fileNames:
                atoms = name.split('.')
                if atoms[0] == self.ticket and atoms[-2] == 'json' and atoms[-1] == 'status':
                    key = '.'.join(atoms[1:-1])
                    try:
                        files[key] = json.load(file(os.path.join(dirPath,name),"rb"))
                    except:
                        files[key] = {}
        return dict(files=files)

class ReportGen(object):
    def __init__(self,reportDir,contents):
        self.reportDir = reportDir
        self.contents = contents
        self.instructions = None
        self.ticket = None
        
    def run(self):
        self.ticket = hashlib.md5(self.contents).hexdigest()
        instrFname  = os.path.join(self.reportDir,"%s.json" % self.ticket)
        statusFname = os.path.join(self.reportDir,"%s.json.status" % self.ticket)
        ip = open(instrFname,"wb")
        ip.write(self.contents)
        ip.close()
        #
        updateStatus(statusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
        # Read the instructions as a JSON object
        try:
            self.instructions = json.loads(self.contents)
            o = Supervisor(self.reportDir,self.ticket,self.instructions)
            th = threading.Thread(target = o.run)
            th.setDaemon(True)
            th.start()
        except:
            msg = traceback.format_exc()
            updateStatus(statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})
        return self.ticket

class Supervisor(object):
    def __init__(self,reportDir,ticket,instr):
        self.instructions = instr
        self.ticket = ticket
        self.reportDir = reportDir
    def run(self):
        statusFname = os.path.join(self.reportDir,"%s.json.status" % self.ticket)
        for i,r in enumerate(self.instructions["regions"]):
            # Check if a composite map already exists for this region
            cm = CompositeMapMaker(self.reportDir,self.ticket,i)
            if "done" not in cm.getStatus():
                components = { "baseMap":{}, "pathMap":{}, "markerMap":{} }
                bm = ReportBaseMap(self.reportDir,self.ticket,self.instructions,i)
                components["baseMap"]["object"] = bm
                bmThread = threading.Thread(target = bm.run)
                bmThread.setDaemon(True)
                bmThread.start()
                mp = bm.getMapParams()
                pm = ReportPathMap(self.reportDir,self.ticket,self.instructions,mp,i)
                components["pathMap"]["object"] = pm
                pmThread = threading.Thread(target = pm.run)
                pmThread.setDaemon(True)
                pmThread.start()
                mm = ReportMarkerMap(self.reportDir,self.ticket,self.instructions,mp,i)
                components["markerMap"]["object"] = mm
                mmThread = threading.Thread(target = mm.run)
                mmThread.setDaemon(True)
                mmThread.start()
                while True:
                    errors = False
                    complete = True
                    for c in components:
                        st = components[c]["object"].getStatus()
                        components[c]["status"] = st
                        if isinstance(st,tuple):
                            for s in st:
                                if "end" not in s: complete = False
                                if "error" in s: errors = True
                        else:    
                            if "end" not in st: complete = False
                            if "error" in st: errors = True
                        updateStatus(statusFname,{("%s.%d" % (c,i)):st})
                    if complete: break
                    time.sleep(1.0)
            # All components have been made, it is time to generate the composite map    
            cmThread = threading.Thread(target = cm.run)
            cmThread.setDaemon(True)
            cmThread.start()
            while True:
                errors = False
                complete = True
                st = cm.getStatus()
                if "end" not in st: complete = False
                if "error" in st: errors = True
                updateStatus(statusFname,{("%s.%d" % ("composite",i)):st})
                if complete: break
                time.sleep(1.0)
                
        updateStatus(statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
            
        # try:
            # bm = ReportBaseMap(self.reportDir,self.ticket,self.instructions)
            # bmThread = threading.Thread(target = bm.run)
            # bmThread.setDaemon(True)
            # bmThread.start()
            # # The map parameters are necessary for the additional layers
            # mp = bm.getMapParams()
            # pm = ReportPathMap(self.reportDir,self.ticket,self.instructions,mp)
            # pmThread = threading.Thread(target = pm.run)
            # pmThread.setDaemon(True)
            # pmThread.start()           
            # mm = ReportMarkerMap(self.reportDir,self.ticket,self.instructions,mp)
            # mmThread = threading.Thread(target = mm.run)
            # mmThread.setDaemon(True)
            # mmThread.start()            
        # except:
            # msg = traceback.format_exc()
            # updateStatus(statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})
        # #
        # return self.ticket

class ReportBaseMap(object):
    def __init__(self,reportDir,ticket,instructions,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.baseMapFname = os.path.join(self.reportDir,"%s.baseMap.%d.png" % (self.ticket,self.region))
        self.statusFname  = os.path.join(self.reportDir,"%s.baseMap.%d.status" % (self.ticket,self.region))
        self.name   = self.instructions["regions"][region]["name"]
        self.minLng = float(self.instructions["regions"][region]["minLng"])
        self.maxLng = float(self.instructions["regions"][region]["maxLng"])
        self.minLat = float(self.instructions["regions"][region]["minLat"])
        self.maxLat = float(self.instructions["regions"][region]["maxLat"])
        self.baseImage = self.instructions["regions"][region]["baseImage"]
        
    def getMapParams(self):
        if self.baseImage == "Google map image":
            mp = GoogleMap().getPlatParams(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)
        elif self.baseImage == "Google satellite image": 
            mp = GoogleMap().getPlatParams(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=True)
        elif self.baseImage == "Plat image":
            mp = PlatFetcher().getPlatParams(self.name,self.minLng,self.maxLng,self.minLat,self.maxLat)
            if mp is None:
                mp = GoogleMap().getPlatParams(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)             
        else:
            raise ValueError("Base Image type not yet supported")
        return mp
    
    def getStatus(self):
        return getStatus(self.statusFname)
        
    def run(self):
        if os.path.exists(self.baseMapFname) and "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output file exists
        else:
            updateStatus(self.statusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
            try:
                if self.baseImage == "Google map image":
                    image, mp = GoogleMap().getPlat(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)
                elif self.baseImage == "Google satellite image": 
                    image, mp = GoogleMap().getPlat(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=True)
                elif self.baseImage == "Plat image":
                    image, mp = PlatFetcher().getPlat(self.name,self.minLng,self.maxLng,self.minLat,self.maxLat)
                    if mp is None:
                        image, mp = GoogleMap().getPlat(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)             
                else:
                    raise ValueError("Base Image type not yet supported")
                op = open(self.baseMapFname,"wb")
                op.write(asPNG(image))
                op.close()
                updateStatus(self.statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})

class ReportPathMap(object):
    def __init__(self,reportDir,ticket,instructions,mapParams,region,timeout=300):
        self.reportDir = reportDir
        self.ticket = ticket
        self.region = region
        self.instructions = instructions
        self.pathMapFname = os.path.join(self.reportDir,"%s.pathMap.%d.png" % (self.ticket,self.region))
        self.pathStatusFname  = os.path.join(self.reportDir,"%s.pathMap.%d.status" % (self.ticket,self.region))
        self.swathMapFname = os.path.join(self.reportDir,"%s.swathMap.%d.png" % (self.ticket,self.region))
        self.swathStatusFname  = os.path.join(self.reportDir,"%s.swathMap.%d.status" % (self.ticket,self.region))
        self.mapParams = mapParams
        self.timeout = timeout
        
    def getStatus(self):
        return getStatus(self.pathStatusFname),getStatus(self.swathStatusFname)
        
    def run(self):
        swathColors = dict(No=False,Yes=(64,64,255,64),Red=(255,64,64,64),Green=(64,255,64,64),Blue=(64,64,255,64),
                           Yellow=(255,255,64,64),Magenta=(255,64,255,64),Cyan=(64,255,255,64))
        if "done" in getStatus(self.pathStatusFname) and "done" in getStatus(self.swathStatusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.pathStatusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
            updateStatus(self.swathStatusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
            mp = self.mapParams
            sl = SurveyorLayers(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
            try:
                if "runs" in self.instructions:
                    pathMaps = []
                    swathMaps = []
                    for ir,params in enumerate(self.instructions["runs"]):
                        showPath = (params["path"] == "Yes")
                        showSwath = swathColors[params["swath"]]
                        def report(nPoints):
                            if showPath:  updateStatus(self.pathStatusFname,{"run%d" % (ir,): "%d points" % nPoints})
                            if showSwath: updateStatus(self.swathStatusFname,{"run%d" % (ir,): "%d points" % nPoints})
                        if showPath or showSwath:
                            startEtm = strToEtm(params["startEtm"])
                            endEtm   = strToEtm(params["endEtm"])
                            analyzer = params["analyzer"]
                            if showSwath:
                                minAmpl   = params["minAmpl"]
                                stabClass = params["stabClass"]
                                sl.setSwathParams(minAmpl=minAmpl,stabClass=stabClass)
                            pMap,sMap = sl.makePathAndSwath(analyzer,startEtm,endEtm,showPath,showSwath,report,self.timeout)
                            if showPath: pathMaps.append(pMap)
                            if showSwath: swathMaps.append(sMap)
                    # Now merge the paths on the run maps together to form the composite path
                    if pathMaps:
                        image = sl.makeEmpty()
                        for m in pathMaps:
                            image = overBackground(m,image,None)
                        image = backgroundToOverlay(image)
                        op = open(self.pathMapFname,"wb")
                        op.write(asPNG(image))
                        op.close()
                    if swathMaps:
                        image = sl.makeEmpty()
                        for m in swathMaps:
                            image = overBackground(m,image,None)
                        image = backgroundToOverlay(image)
                        op = open(self.swathMapFname,"wb")
                        op.write(asPNG(image))
                        op.close()
                updateStatus(self.pathStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
                updateStatus(self.swathStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.pathStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})
                updateStatus(self.swathStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})          

MT_NONE, MT_CONC, MT_RANK = 0, 1, 2

class ReportMarkerMap(object):
    def __init__(self,reportDir,ticket,instructions,mapParams,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.peaksHtmlFname = os.path.join(self.reportDir,"%s.peaksMap.%d.html" % (self.ticket,self.region))
        self.peaksMapFname = os.path.join(self.reportDir,"%s.peaksMap.%d.png" % (self.ticket,self.region))
        self.peaksStatusFname  = os.path.join(self.reportDir,"%s.peaksMap.%d.status" % (self.ticket,self.region))
        self.wedgesMapFname = os.path.join(self.reportDir,"%s.wedgesMap.%d.png" % (self.ticket,self.region))
        self.wedgesStatusFname  = os.path.join(self.reportDir,"%s.wedgesMap.%d.status" % (self.ticket,self.region))
        self.mapParams = mapParams
        
    def getStatus(self):
        return getStatus(self.peaksStatusFname),getStatus(self.wedgesStatusFname)
    
    def makePeakReport(self,op,peakDict):
        peakTableString = []
        peakTableString.append('<table class="table table-striped table-condensed">')
        peakTableString.append('<thead><tr>')
        peakTableString.append('<th>%s</th>' % "Rank")
        peakTableString.append('<th>%s</th>' % "Designation")
        peakTableString.append('<th>%s</th>' % "Longitude")
        peakTableString.append('<th>%s</th>' % "Latitude")
        peakTableString.append('<th>%s</th>' % "Conc")
        peakTableString.append('<th>%s</th>' % "Ampl")
        peakTableString.append('</tr></thead>')
        peakTableString.append('<tbody>')
        for i in range(len(peakDict)):
            r = i+1
            peakTableString.append('<tr>')
            peakTableString.append('<td>%d</td>' % r)
            tstr = time.strftime("%Y%m%dT%H%M%S",time.gmtime(peakDict[r].etm))
            anz = peakDict[r].data['ANALYZER']
            peakTableString.append('<td>%s_%s</td>' % (anz,tstr))
            lng = peakDict[r].data['GPS_ABS_LONG']
            peakTableString.append('<td>%.6f</td>' % lng)
            lat = peakDict[r].data['GPS_ABS_LAT']
            peakTableString.append('<td>%.6f</td>' % lat)
            ch4 = peakDict[r].data['CH4']
            peakTableString.append('<td>%.1f</td>' % ch4)
            ampl = peakDict[r].data['AMPLITUDE']
            peakTableString.append('<td>%.2f</td>' % ampl)
            peakTableString.append('</tr>')
        peakTableString.append('</tr></tbody>')
        peakTableString.append('</table>')
        op.write("\n".join(peakTableString))
        
    def run(self):
        markerTypes = {"None":MT_NONE,"Concentration":MT_CONC,"Rank":MT_RANK}
        markerColors = dict(Red=(255,64,64),Green=(64,255,64),Blue=(64,64,255),
                            Yellow=(255,255,64),Magenta=(255,64,255),Cyan=(64,255,255))
        wedgeColors = dict(No=False,Yes=(255,255,64,192),Red=(255,64,64,192),Green=(64,255,64,192),Blue=(64,64,255,192),
                           Yellow=(255,255,64,192),Magenta=(255,64,255,192),Cyan=(64,255,255,192))
        if "done" in getStatus(self.peaksStatusFname) and "done" in getStatus(self.wedgesStatusFname):
            return  # This has already been computed and the output files exist
        else:
            updateStatus(self.peaksStatusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
            updateStatus(self.wedgesStatusFname,{"start":time.strftime("%Y%m%dT%H:%M:%S")},True)
            mp = self.mapParams
            sl = SurveyorLayers(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
            try:
                if "runs" in self.instructions:
                    markerParams = []
                    MarkerParams = namedtuple('MarkerParams',['analyzer','startEtm','endEtm','minAmpl',
                                              'maxAmpl','mType','mColor','showWedges','exclRadius'])
                    for ir,params in enumerate(self.instructions["runs"]):
                        mType  = markerTypes[params["markerType"]]
                        mColor = markerColors[params["markerColor"]]
                        showPeaks = (mType != MT_NONE)
                        showWedges = wedgeColors[params["wedges"]]
                        if showPeaks or showWedges:
                            startEtm = strToEtm(params["startEtm"])
                            endEtm   = strToEtm(params["endEtm"])
                            analyzer = params["analyzer"]
                            minAmpl  = params["minAmpl"]
                            maxAmpl  = params.get("maxAmpl",None)
                            exclRadius = params["exclRadius"]
                            markerParams.append(MarkerParams(analyzer,startEtm,endEtm,minAmpl,maxAmpl,
                                                mType,mColor,showWedges,exclRadius))
                    im1,im2,pkDict = sl.makeMarkers(markerParams)
                    # Now write out the maps
                    if showPeaks:
                        im1 = backgroundToOverlay(im1)
                        op = open(self.peaksMapFname,"wb")
                        op.write(asPNG(im1))
                        op.close()
                        if pkDict:
                            op = open(self.peaksHtmlFname,"wb")
                            self.makePeakReport(op,pkDict)
                            op.close()
                    if showWedges:
                        im2 = backgroundToOverlay(im2)
                        op = open(self.wedgesMapFname,"wb")
                        op.write(asPNG(im2))
                        op.close()
                updateStatus(self.peaksStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
                updateStatus(self.wedgesStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H:%M:%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.peaksStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})
                updateStatus(self.wedgesStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H:%M:%S")})
                
class PlatFetcher(object):
    def getPlatParams(self,platName,minLng,maxLng,minLat,maxLat,padX=50,padY=50):
        return self.getPlat(platName,minLng,maxLng,minLat,maxLat,padX,padY,fetchPlat=False)
        
    def getPlat(self,platName,minLng,maxLng,minLat,maxLat,padX=50,padY=50,fetchPlat=True):
        tifFile = os.path.join(PLAT_TIF_ROOT, platName+".tif")
        pngFile = os.path.join(PLAT_PNG_ROOT, platName+".png")
        if not os.path.exists(tifFile):
            return (None, None) if fetchPlat else None
        if not fetchPlat:
            p = PIL.Image.open(tifFile)
            nx,ny = p.size
            mp = MapParams(minLng,minLat,maxLng,maxLat,nx,ny,padX,padY)
            return mp
        else:
            if not os.path.exists(pngFile):
                # Call ImageMagik to convert the TIF to a PNG
                os.system('convert "%s" "%s"' % ( tifFile, pngFile))
            p = PIL.Image.open(pngFile)
            nx,ny = p.size
            q = PIL.Image.new('RGBA',(nx+2*padX,ny+2*padY),(255,255,255,255))
            q.paste(p,(padX,padY))
            mp = MapParams(minLng,minLat,maxLng,maxLat,nx,ny,padX,padY)
            return q,mp

class GoogleMap(object):
    def getMap(self,latCen,lonCen,zoom,nx,ny,scale=1,satellite=True):
        url = 'http://maps.googleapis.com/maps/api/staticmap'
        params = dict(center="%.6f,%.6f"%(latCen,lonCen),zoom="%d"%zoom,size="%dx%d" % (nx,ny),scale="%d"%scale,sensor="false")
        if satellite: params["maptype"] = "satellite"
        paramStr = urllib.urlencode(params)
        get_url = url+("?%s" % paramStr)
        try:
            resp = urllib2.urlopen(get_url,timeout=5.0)
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
            raise
        else:
            return resp.read()
            
    def getPlatParams(self,minLng,maxLng,minLat,maxLat,satellite=True,padX=50,padY=50):
        return self.getPlat(minLng,maxLng,minLat,maxLat,satellite,padX,padY,fetchPlat=False)
    
    def getPlat(self,minLng,maxLng,minLat,maxLat,satellite=True,padX=50,padY=50,fetchPlat=True):
        meanLat = 0.5*(minLat + maxLat)
        meanLng = 0.5*(minLng + maxLng)
        Xp = maxLng-minLng
        Yp = maxLat-minLat
        # Find the largest zoom consistent with these limits
        cosLat = math.cos(meanLat*DTR)
        zoom = int(math.floor(math.log(min((360.0*640)/(256*Xp),(360.0*640*cosLat)/(256*Yp)))/math.log(2.0)))
        # Find the number of pixels in each direction
        fac = (256.0/360.0)*2**zoom
        mx = int(math.ceil(fac*Xp))
        my = int(math.ceil(fac*Yp/cosLat))
        scale = 2
        mp = MapParams(minLng,minLat,maxLng,maxLat,mx*scale,my*scale,padX,padY)
        if fetchPlat:
            p = PIL.Image.open(cStringIO.StringIO(self.getMap(meanLat,meanLng,zoom,mx,my,scale,satellite)))
            q = PIL.Image.new('RGBA',(scale*mx+2*padX,scale*my+2*padY),(255,255,255,255))
            q.paste(p,(padX,padY))
            return q, mp
        else:
            return mp
            
class GoogleMarkers(object):
    def getMarker(self,size,fontsize,text,color):
        url = 'http://chart.apis.google.com/chart'
        params = dict(chst="d_map_spin",chld="%s|0|%s|%s|b|%s" % (size,color,fontsize,text))
        paramStr = urllib.urlencode(params)
        get_url = url+("?%s" % paramStr)
        try:
            resp = urllib2.urlopen(get_url,timeout=5.0)
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
            raise
        else:
            return resp.read()
            
class SurveyorLayers(object):
    def __init__(self,minLng,minLat,maxLng,maxLat,nx,ny,padX,padY):
        # The map is in the middle, of size nx by ny. It is padded by padX on left and right, and by
        #  padY on top and bottom. This makes the padded image have size nx+2*padX, ny+2*padY
        self.minLng = minLng
        self.minLat = minLat
        self.maxLng = maxLng
        self.maxLat = maxLat
        self.nx = nx
        self.ny = ny
        self.padX = padX
        self.padY = padY
        deltaLat = RTD/EARTH_RADIUS
        deltaLng = RTD/(EARTH_RADIUS*math.cos(0.5*(self.minLat+self.maxLat)*DTR))
        mppx = (self.maxLng-self.minLng)/(deltaLng*self.nx)
        mppy = (self.maxLat-self.minLat)/(deltaLat*self.ny)
        self.mpp = 0.5*(mppx+mppy)
        # Calculate padded lat and lng limits for selection of P3 data
        minPadDist = 200.0   # Extend by at least this distance beyond the map edges
        px = max((maxLng-minLng)*padX/nx,minPadDist*deltaLng)
        py = max((maxLat-minLat)*padY/ny,minPadDist*deltaLat)
        self.padMinLng = minLng - px
        self.padMinLat = minLat - py
        self.padMaxLng = maxLng + px
        self.padMaxLat = maxLat + py
        self.setSwathParams()   # Set up defaults, which may be overridden
        
    def xform(self,lng,lat):
        """Get pixel corresponding to (lng,lat), where pixel (0,0) is
           (minLng,maxLat) and (nx,ny) is (maxLng,minLat)"""
        x = int(self.nx*(lng-self.minLng)/(self.maxLng-self.minLng))
        y = int(self.ny*(lat-self.maxLat)/(self.minLat-self.maxLat))
        return x,y
        
    def makeEmpty(self):
        return PIL.Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
    
    def setSwathParams(self,minAmpl=0.05,minLeak=1.0,stabClass='D',nWindow=10,astdParams=dict(a=0.15*math.pi,b=0.25,c=0.0)):
        self.minAmpl = minAmpl
        self.minLeak = minLeak
        self.stabClass = stabClass
        self.nWindow = nWindow
        self.astdParams = astdParams.copy()
        
    def astd(self,wind,vcar):
        a = self.astdParams["a"]
        b = self.astdParams["b"]
        c = self.astdParams["c"]
        return min(math.pi,a*(b+c*vcar)/(wind+0.01))
        
    def drawSwath(self,source,sv,makeSwath):
        result = sp.process(source,self.nWindow,self.stabClass,self.minLeak,self.minAmpl,self.astdParams)
        lastLng, lastLat, lastDeltaLng, lastDeltaLat = None, None, None, None
        for etm,lng,lat,deltaLng,deltaLat in zip(result["EPOCH_TIME"],result["GPS_ABS_LONG"],result["GPS_ABS_LAT"],result["DELTA_LONG"],result["DELTA_LAT"]):
            if lastLng is not None:
                noLastView = abs(lastDeltaLng)<1.0e-6 and abs(lastDeltaLat)<1.0e-6
                if not noLastView:
                    noView = abs(deltaLng)<1.0e-6 and abs(deltaLat)<1.0e-6
                    if not noView:
                        x1,y1 = self.xform(lastLng+lastDeltaLng, lastLat+lastDeltaLat)
                        x2,y2 = self.xform(lastLng, lastLat)
                        x3,y3 = self.xform(lng,lat)
                        x4,y4 = self.xform(lng+deltaLng, lat+deltaLat)
                        xmin = min(x1,x2,x3,x4)
                        xmax = max(x1,x2,x3,x4)
                        ymin = min(y1,y2,y3,y4)
                        ymax = max(y1,y2,y3,y4)
                        temp = PIL.Image.new('RGBA',(xmax-xmin+1,ymax-ymin+1),(0,0,0,0))
                        tdraw = PIL.ImageDraw.Draw(temp)
                        tdraw.polygon([(x1-xmin,y1-ymin),(x2-xmin,y2-ymin),(x3-xmin,y3-ymin),(x4-xmin,y4-ymin)],
                                        fill=makeSwath,outline=makeSwath[0:3]+(128,))
                        mask = (self.padX+xmin,self.padY+ymin)
                        sv = overBackground(temp,sv,mask)
                        
            lastLng, lastLat, lastDeltaLng, lastDeltaLat = lng, lat, deltaLng, deltaLat
    
    def makePathAndSwath(self,analyzer,startEtm,endEtm,makePath,makeSwath,reportFunc=None,timeout=None):
        """Use analyzer name, start and end epoch times to make a REST call to P3 and draw the path taken 
        by the vehicle onto a layer. Only points lying in the layer rectangle (within the padded region)
        are displayed"""
        startTime = time.clock()
        colors = dict(normal=(0,0,255,255),analyze=(0,0,0,255),inactive=(255,0,0))
        lastColor = [colors["normal"]]
        def getColorFromValveMask(mask):
            # Determine color of path from valve mask
            color = lastColor[0]
            imask = int(round(mask,0))
            if abs(mask-imask) <= 1e-4:
                if   imask & 1:  color = colors["analyze"]
                elif imask & 16: color = colors["inactive"]
                else:            color = colors["normal"]
                lastColor[0] = color
            return color
            
        ov, sv = None, None
        if makePath:
            ov = PIL.Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            odraw = PIL.ImageDraw.Draw(ov)
        if makeSwath:
            sv = PIL.Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            sdraw = PIL.ImageDraw.Draw(sv)
        lastRow = -1
        penDown = False
        path = []               # Path in (x,y) coordinates
        bufferedPath = []       # Path for calculation of swath
        pathColor = colors["normal"]
        newPath = True
        p3 = gp3.P3_Accessor(analyzer)
        gen = p3.genAnzLog("dat")(startEtm=startEtm,endEtm=endEtm,minLng=self.padMinLng,
                                  maxLng=self.padMaxLng,minLat=self.padMinLat,maxLat=self.padMaxLat)
        i = 0
        for i,m in enumerate(gen):
            lat = m.data["GPS_ABS_LAT"]
            lng = m.data["GPS_ABS_LONG"]
            fit = m.data.get("GPS_FIT",1)
            mask = m.data.get("ValveMask",0)
            row = m.data.get("row",0)   # Used to detect contiguous points
            color = getColorFromValveMask(mask)
            isNormal = (color == colors["normal"])
            x,y = self.xform(lng,lat)
            # newPath = True means that there is to be a break in the path. A simple change
            #  of color gives a new path which joins onto the last
            # if fit>=1 and (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY) and (row == lastRow+1):
            if fit>=1 and (row == lastRow+1):
                if newPath or color!=pathColor:
                    if path: # Draw out old path
                        if makePath: odraw.line(path,fill=pathColor,width=2)
                        if makeSwath and pathColor == colors["normal"]: self.drawSwath(bufferedPath,sv,makeSwath)
                        if newPath:
                            path = []
                            bufferedPath = []
                        else:
                            path = [path[-1]]
                            bufferedPath = [bufferedPath[-1]]
                    pathColor = color
                path.append((self.padX+x,self.padY+y))
                bufferedPath.append(m.data)
                newPath = False
            else:
                newPath = True
            lastRow = row
            if i%100 == 0:
                if reportFunc: reportFunc(i)
                if timeout and (time.clock()-startTime)>timeout:
                    raise RuntimeError("makePathAndSwath is taking too long to complete")
        if reportFunc: reportFunc(i)
        if path:        
            if makePath: odraw.line(path,fill=pathColor,width=2)
            if makeSwath and pathColor == colors["normal"]: self.drawSwath(bufferedPath,sv,makeSwath)
        return ov, sv
            
    def makeMarkers(self,markerParams):
        markersByRank = {}
        peaks = []
        anyPeaks = False
        anyWedges = False
        
        for r,(analyzer,startEtm,endEtm,minAmpl,maxAmpl,mType,mColor,makeWedges,exclRadius) in enumerate(markerParams):
            # markerParams specifies parameters for each region in turn, and r is the region number
            anyPeaks = anyPeaks or (mType != MT_NONE)
            anyWedges = anyWedges or makeWedges

            p3 = gp3.P3_Accessor(analyzer)
            gen = p3.genAnzLog("peaks")(startEtm=startEtm,endEtm=endEtm,minLng=self.padMinLng,
                                      maxLng=self.padMaxLng,minLat=self.padMinLat,maxLat=self.padMaxLat)
            pList = [(m.data["AMPLITUDE"],m,r) for m in gen]
            if exclRadius > 0:
                result = []
                ilat, ilng, iampl = [], [], []
                # We need to remove peaks which are closer to each other than the exclusion radius, keeping
                #  only the largest in each group
                for amp,m,region in pList:
                    ilat.append(m.data["GPS_ABS_LAT"])
                    ilng.append(m.data["GPS_ABS_LONG"])
                    iampl.append(m.data["AMPLITUDE"])
                ilat = np.asarray(ilat)
                ilng = np.asarray(ilng)
                iampl = np.asarray(iampl)
                
                # Get median latitude and longitude for estimating distance scale
                medLat = np.median(ilat)
                medLng = np.median(ilng)
                mpdLat = DTR*EARTH_RADIUS           # Meters per degree of latitude
                mpdLng = mpdLat*np.cos(DTR*medLat)  # Meters per degree of longitude

                # Find points which are close to a given location
                # Find permutations that sort by longitude as primary key
                perm = np.argsort(ilng)
                elow = ehigh = 0
                dlng = exclRadius/mpdLng
                for i in perm:
                    while elow<len(perm)  and ilng[perm[elow]]  <  ilng[i]-dlng:  elow += 1
                    while ehigh<len(perm) and ilng[perm[ehigh]] <= ilng[i]+dlng: ehigh += 1
                    for e in range(elow,ehigh):
                        j = perm[e]
                        lng,lat,ampl = ilng[j],ilat[j],iampl[j]
                        assert ilng[i]-dlng <= lng < ilng[i]+dlng
                        dx = mpdLng*(lng-ilng[i])
                        dy = mpdLat*(lat-ilat[i])
                        if 0 < dx*dx+dy*dy <= exclRadius*exclRadius:
                            if iampl[i]<ampl: break
                            elif iampl[i]==ampl and i<j: break
                    else:
                        # This is the largest peak in the exclusion zone
                        result.append(i)
                peaks += [pList[i] for i in result]
            else:
                peaks += pList
            
        ov1, ov2 = None, None
        peaks.sort()
                
        if anyPeaks:
            ov1 = PIL.Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            # Count ranked markers
            nRanked = 0
            for amp,m,region in peaks:
                mType = markerParams[region].mType
                if mType == MT_RANK:
                    lat = m.data["GPS_ABS_LAT"]
                    lng = m.data["GPS_ABS_LONG"]
                    x,y = self.xform(lng,lat)
                    if (0<=x<self.nx) and (0<=y<self.ny) and (amp>minAmpl) and ((maxAmpl is None) or (amp<=maxAmpl)): nRanked += 1
            
            rank = nRanked
            #
            for amp,m,region in peaks:
                analyzer,startEtm,endEtm,minAmpl,maxAmpl,mType,mColor,makeWedges,exclRadius = markerParams[region]
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                amp = m.data["AMPLITUDE"]
                ch4 = m.data["CH4"]
                x,y = self.xform(lng,lat)
                if (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY) and \
                   (amp>minAmpl) and ((maxAmpl is None) or (amp<=maxAmpl)):
                    if mType in [MT_CONC, MT_RANK]:
                        if mType == MT_CONC:
                            size = (self.ny/1500.0)*amp**0.25    # Make these depend on number of pixels in the image
                            fontsize = min(100,int(18.0*size))
                            color = "%02x%02x%02x" % tuple(mColor)
                            msg = "%.1f" % ch4
                        elif mType == MT_RANK:
                            size = (self.ny/1500.0)
                            fontsize = min(100,int(25.0*size))
                            color = "%02x%02x%02x" % tuple(mColor)
                            if (0<=x<self.nx) and (0<=y<self.ny):
                                msg = "%d" % rank
                                markersByRank[rank] = m
                                rank -= 1
                            else:
                                msg = "*"
                        buff = cStringIO.StringIO(GoogleMarkers().getMarker(size,fontsize,msg,color))
                        b = PIL.Image.open(buff)
                        bx,by = b.size
                        box = (self.padX+x-bx//2,self.padY+y-by)
                        ov1 = overBackground(b,ov1,box)
        if anyWedges:
            ov2 = PIL.Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            odraw2 = PIL.ImageDraw.Draw(ov2)
            for amp,m,region in peaks:
                analyzer,startEtm,endEtm,minAmpl,maxAmpl,mType,mColor,makeWedges,exclRadius = markerParams[region]
                if not makeWedges: continue
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                vcar = m.data.get("CAR_SPEED",0.0)
                windN = m.data.get("WIND_N",0.0)
                windE = m.data.get("WIND_E",0.0)
                dstd  = DTR*m.data.get("WIND_DIR_SDEV",0.0)
                x,y = self.xform(lng,lat)
                if (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY) and \
                   (amp>minAmpl) and ((maxAmpl is None) or (amp<=maxAmpl)):
                    wind = math.hypot(windN,windE)
                    radius = 50.0; speedmin = 0.5
                    meanBearing = RTD*math.atan2(windE,windN)
                    dstd = math.hypot(dstd,self.astd(wind,vcar))
                    windSdev = RTD*dstd
                    # Check for NaN
                    if wind == wind and meanBearing == meanBearing:
                        minBearing = meanBearing-min(2*windSdev,180.0)
                        maxBearing = meanBearing+min(2*windSdev,180.0)
                    else:
                        minBearing = 0
                        maxBearing = 360.0
                    radius = int(radius/self.mpp)
                    b = PIL.Image.new('RGBA',(2*radius+1,2*radius+1),(0,0,0,0))
                    bdraw = PIL.ImageDraw.Draw(b)
                    bdraw.pieslice((0,0,2*radius,2*radius),int(minBearing-90.0),int(maxBearing-90.0),fill=makeWedges,outline=(0,0,0,255))
                    ov2 = overBackground(b,ov2,(self.padX+x-radius,self.padY+y-radius))
                   
        return ov1, ov2, markersByRank
        