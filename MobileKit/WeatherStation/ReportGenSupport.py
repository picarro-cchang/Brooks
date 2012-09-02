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
import csv
try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple
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
import Image
import ImageDraw
import ImageMath
from Host.Common.SwathProcessor import process
import socket
import sys
import threading
import time
import traceback
import urllib
import urllib2
import subprocess
import Host.Common.SurveyorInstStatus as sis
from ExcelXmlReport import ExcelXmlReport
from Host.Common.configobj import ConfigObj

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# Executable for HTML to PDF conversion
configFile = os.path.splitext(appPath)[0] + ".ini"
WKHTMLTOPDF = None
IMGCONVERT  = None
APIKEY = None
PLAT_TIF_ROOT = r"S:\Projects\Picarro Surveyor\Files from PGE including TIFF maps\GEMS\CompTif\Gas\Distribution"
PLAT_PNG_ROOT = r"static\plats"

if os.path.exists(configFile):
    config = ConfigObj(configFile)
    WKHTMLTOPDF = config["HelperApps"]["wkhtml_to_pdf"]
    IMGCONVERT  = config["HelperApps"]["image_convert"]
    APIKEY = config["P3Logs"].get("apikey",None)

    if "Plats" in config:
        PLAT_TIF_ROOT = config["Plats"]["tif_root"]
        PLAT_PNG_ROOT = config["Plats"]["png_root"]

SVCURL = "http://localhost:5200/rest"
RTD = 180.0/math.pi
DTR = math.pi/180.0
EARTH_RADIUS = 6378100

NOT_A_NUMBER = 1e1000/1e1000

PLAT_TIF_ROOT = os.path.join(appDir,PLAT_TIF_ROOT)
PLAT_PNG_ROOT = os.path.join(appDir,PLAT_PNG_ROOT)
if not os.path.exists(PLAT_PNG_ROOT): os.makedirs(PLAT_PNG_ROOT)
MapParams = namedtuple("MapParams",["minLng","minLat","maxLng","maxLat","nx","ny","padX","padY"])

statusLock = threading.Lock()
statusLocks = {}

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
    r = ImageMath.eval("int(256*n/(d+1))",n=r,d=a).convert('L')
    g = ImageMath.eval("int(256*n/(d+1))",n=g,d=a).convert('L')
    b = ImageMath.eval("int(256*n/(d+1))",n=b,d=a).convert('L')
    return Image.merge("RGBA",(r,g,b,a))

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
    statusLock.acquire()
    if fname not in statusLocks:
        statusLocks[fname] = threading.Lock()
    statusLock.release()
    statusLocks[fname].acquire()
    try:
        stDict = {}
        if os.path.exists(fname):
            sp = open(fname,"rb")
            try:
                stDict = json.load(sp)
            except:
                stDict = {}
            sp.close()
        return stDict
    finally:
        statusLocks[fname].release()
        
def updateStatus(fname,statusDict,init=False):
    statusLock.acquire()
    if fname not in statusLocks:
        statusLocks[fname] = threading.Lock()
    statusLock.release()
    statusLocks[fname].acquire()
    try:
        dst = {}
        if not init:
            sp = open(fname,"rb")
            dst = json.load(sp)
            sp.close()
        sp = open(fname,"wb")
        json.dump(merge_dictionary(dst,statusDict),sp)
        sp.close()
    finally:
        statusLocks[fname].release()

def asPNG(image):
    output = cStringIO.StringIO()
    image.save(output,format="PNG")                
    try:
        return output.getvalue()
    finally:
        output.close()
        
def strToEtm(s):
    return calendar.timegm(time.strptime(s,"%Y-%m-%d  %H:%M"))

def pretty_ticket(ticket):
    t = ticket.upper()
    return " ".join([t[s:s+4] for s in range(0,32,4)])

def getPossibleNaN(d,k,default):
    try:
        result = float(d.get(k,default))
    except:
        result = NOT_A_NUMBER
    return result

class ReportCompositeMap(object):
    def __init__(self,reportDir,ticket,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.region = region
        self.compositeMapFname = os.path.join(self.reportDir,"%s/compositeMap.%d.png" % (self.ticket,self.region))
        self.statusFname  = os.path.join(self.reportDir,"%s/compositeMap.%d.status" % (self.ticket,self.region))
        
    def getStatus(self):
        return getStatus(self.statusFname)
        
    def run(self):
        if "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.statusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            try:
                files = {}
                imageFnames = {}
                statusFnames = {}
                targetDir = os.path.join(self.reportDir,"%s" % self.ticket)
                for dirPath, dirNames, fileNames in os.walk(targetDir):
                    for name in fileNames:
                        atoms = name.split('.')
                        if len(atoms)>=2 and atoms[-2] == ("%d" % self.region) and atoms[-1] == 'png':
                            key = '.'.join(atoms[:-2])
                            base = '.'.join(atoms[:-1])
                            # Having found a png file, look for the associated .status file
                            #  to see if the png file is valid
                            statusName = os.path.join(targetDir,base+'.status')
                            pngName = os.path.join(targetDir,name)
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
                        image = Image.open(cStringIO.StringIO(files[layer]))
                        if compositeImage is None:
                            compositeImage = Image.new('RGBA',image.size,(0,0,0,0))
                        compositeImage = overBackground(image,compositeImage,None)
                        # Remove the component status and image files
                        os.remove(statusFnames[layer])
                        os.remove(imageFnames[layer])
                op = open(self.compositeMapFname,"wb")
                op.write(asPNG(compositeImage))
                op.close()
                updateStatus(self.statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})

class ReportPDF(object):
    def __init__(self,reportDir,ticket,instructions,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.PdfFname = os.path.join(self.reportDir,"%s/report.%d.pdf" % (self.ticket,self.region))
        self.statusFname  = os.path.join(self.reportDir,"%s/report.%d.status" % (self.ticket,self.region))
        
    def getStatus(self):
        return getStatus(self.statusFname)
        
    def run(self):
        style = """
        <style>
            table.table-fmt1 td {text-align:center; vertical-align:middle; }
            table.table-fmt1 th {text-align:center; }
        </style>
        """
        name = self.instructions["regions"][self.region]["name"]
        heading = "<h2>Report %s, Region %d (%s)</h2>" % (pretty_ticket(self.ticket),self.region+1,name)
        peaksHeading = "<h3>Methane Peaks Detected</h3>"
        markerHeading = "<h3>Markers</h3>"
        surveyHeading = "<h3>Surveys</h3>"
        if "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.statusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            try:
                # Find the peaks report file and the path report file
                peaksReportFname = os.path.join(self.reportDir,"%s/peaksMap.%d.html" % (self.ticket,self.region))
                markerReportFname = os.path.join(self.reportDir,"%s/markerMap.%d.html" % (self.ticket,self.region))
                pathReportFname = os.path.join(self.reportDir,"%s/pathMap.%d.html" % (self.ticket,self.region))
                compositeMapFname = os.path.join(self.reportDir,"%s/compositeMap.%d.png" % (self.ticket,self.region))
                
                params = {"ticket":self.ticket, "region":self.region}
                compositeMapUrl = "%s/getComposite?%s" % (SVCURL,urllib.urlencode(params))
                # compositeMapUrl = "file:%s" % urllib.pathname2url(compositeMapFname)
                # Read in the peaks report and path report
                peaksReport = peaksHeading
                fp = None
                try:
                    fp = file(peaksReportFname,"rb")
                    peaksReport += fp.read()
                except:
                    peaksReport = ""
                finally:
                    if fp: fp.close()
                    
                markerReport = markerHeading
                fp = None
                try:
                    fp = file(markerReportFname,"rb")
                    markerReport += fp.read()
                except:
                    markerReport = ""
                    print traceback.format_exc()
                finally:
                    if fp: fp.close()
                    
                pathReport = surveyHeading
                fp = None
                try:
                    fp = file(pathReportFname,"rb")
                    pathReport += fp.read()
                except:
                    pathReport = ""
                finally:
                    if fp: fp.close()
                # Generate the composite map as an image
                # pic = '<img id="image" src="%s" alt="" width="95%%" style="-moz-transform:rotate(90deg);-webkit-transform:rotate(90deg);"></img>' % compositeMapUrl
                pic = '<img id="image" src="%s" alt="" width="95%%"></img>' % compositeMapUrl
                s = style + heading + peaksReport + markerReport + pathReport + heading + pic
                proc = subprocess.Popen([WKHTMLTOPDF,"-",self.PdfFname],
                                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                stdout = proc.communicate(s)
                updateStatus(self.statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})
    
class LayerFilenamesGetter(object):
    def __init__(self,reportDir,ticket):
        self.reportDir = reportDir
        self.ticket = ticket
    def run(self):
        files = {}
        targetDir = os.path.join(self.reportDir,"%s" % self.ticket)
        for dirPath, dirNames, fileNames in os.walk(targetDir):
            for name in fileNames:
                atoms = name.split('.')
                if atoms[-1] == 'png':
                    key = '.'.join(atoms[:-1])
                    files[key] = name
        return files
    
class ReportStatus(object):
    def __init__(self,reportDir,ticket):
        self.reportDir = reportDir
        self.ticket = ticket
    def run(self):
        files = {}
        targetDir = os.path.join(self.reportDir,"%s" % self.ticket)
        for dirPath, dirNames, fileNames in os.walk(targetDir):
            for name in fileNames:
                atoms = name.split('.')
                if len(atoms)>=2 and atoms[-2] == 'json' and atoms[-1] == 'status':
                    key = '.'.join(atoms[:-1])
                    try:
                        files[key] = json.load(file(os.path.join(dirPath,name),"rb"))
                    except:
                        files[key] = {}
        return dict(files=files)

def getTicket(contents):
    return hashlib.md5(contents).hexdigest()

class ReportGen(object):
    def __init__(self,reportDir,contents):
        self.reportDir = reportDir
        self.contents = contents
        self.instructions = None
        self.ticket = None
        
    def run(self):
        self.ticket = getTicket(self.contents)
        targetDir = os.path.join(self.reportDir,"%s" % self.ticket)
        if not os.path.exists(targetDir): os.makedirs(targetDir)
        instrFname  = os.path.join(self.reportDir,"%s/json" % self.ticket)
        statusFname = os.path.join(self.reportDir,"%s/json.status" % self.ticket)
        try:
            if os.path.exists(statusFname): # This job has already been done
                status = getStatus(statusFname)
                # If there is an "error" in the status, we delete everything in this directory
                #  so as to get a fresh start
                if "error" in status:
                    for dirPath, dirNames, fileNames in os.walk(targetDir):
                        for name in fileNames:
                            os.remove(os.path.join(targetDir,name))
                else:
                    return self.ticket
            if os.path.exists(instrFname):
                ip = open(instrFname,"rb")
                if ip.read() != self.contents:
                    updateStatus(statusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
                    ip.close()
                    raise ValueError("MD5 hash collision in cached instructions")
            else:
                ip = open(instrFname,"wb")
                ip.write(self.contents)
                ip.close()
                    
            updateStatus(statusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            # Read the instructions as a JSON object
            self.instructions = json.loads(self.contents)
            o = Supervisor(self.reportDir,self.ticket,self.instructions)
            th = threading.Thread(target = o.run)
            th.setDaemon(True)
            th.start()
        except:
            msg = traceback.format_exc()
            updateStatus(statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})
        return self.ticket

class Supervisor(object):
    # Start up various report generation tasks. Processing takes place one region at a time
    #  with the generation of a composite map and a PDF report for each. The composite map
    #  is made only once there are a base map, a marker map and a path map, and the PDF report
    #  is made only once there is a composite map. For each of the base, marker and path maps,
    #  we iterate over the runs sequentially, and test that all three are complete before 
    #  proceeding the next, so as not to start too many concurrent threads.
    def __init__(self,reportDir,ticket,instr):
        self.instructions = instr
        self.ticket = ticket
        self.reportDir = reportDir
    def run(self):
        errors = False
        statusFname = os.path.join(self.reportDir,"%s/json.status" % self.ticket)
        for i,r in enumerate(self.instructions["regions"]):
            # Check if a composite map already exists for this region
            cm = ReportCompositeMap(self.reportDir,self.ticket,i)
            if "done" not in cm.getStatus():
                components = { "baseMap":{}, "pathMap":{}, "markerMap":{} }
                # Start generating the base map
                bm = ReportBaseMap(self.reportDir,self.ticket,self.instructions,i)
                components["baseMap"]["object"] = bm
                bmThread = threading.Thread(target = bm.run)
                bmThread.setDaemon(True)
                bmThread.start()
                # Start generating the path map
                mp = bm.getMapParams()
                pm = ReportPathMap(self.reportDir,self.ticket,self.instructions,mp,i)
                components["pathMap"]["object"] = pm
                pmThread = threading.Thread(target = pm.run)
                pmThread.setDaemon(True)
                pmThread.start()
                # Start generating the marker map
                mm = ReportMarkerMap(self.reportDir,self.ticket,self.instructions,mp,i)
                components["markerMap"]["object"] = mm
                mmThread = threading.Thread(target = mm.run)
                mmThread.setDaemon(True)
                mmThread.start()
                # Wait until completion of all component maps
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
            # Check if a PDF report already exists for this region
            pdf = ReportPDF(self.reportDir,self.ticket,self.instructions,i)
            if "done" not in pdf.getStatus() and not errors:
                # Start PDF report generation in thread and wait until end is in status
                pdfThread = threading.Thread(target=pdf.run)
                pdfThread.setDaemon(True)
                pdfThread.start()
                while True:
                    st = pdf.getStatus()
                    if "error" in st: errors = True
                    updateStatus(statusFname,{("%s.%d" % ("report",i)):st})
                    if "end" in st: break
                    time.sleep(1.0)
        if errors:
            updateStatus(statusFname,{"error":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
        else:
            updateStatus(statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
            

class ReportBaseMap(object):
    def __init__(self,reportDir,ticket,instructions,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.baseMapFname = os.path.join(self.reportDir,"%s/baseMap.%d.png" % (self.ticket,self.region))
        self.statusFname  = os.path.join(self.reportDir,"%s/baseMap.%d.status" % (self.ticket,self.region))
        self.name   = self.instructions["regions"][region]["name"]
        self.minLat, self.minLng = self.instructions["regions"][region]["swCorner"]
        self.maxLat, self.maxLng = self.instructions["regions"][region]["neCorner"]
        self.baseType = self.instructions["regions"][region]["baseType"]
        
    def getMapParams(self):
        if self.baseType == "map":
            mp = GoogleMap().getPlatParams(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)
        elif self.baseType == "satellite": 
            mp = GoogleMap().getPlatParams(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=True)
        elif self.baseType == "plat":
            mp = PlatFetcher().getPlatParams(self.name,self.minLng,self.maxLng,self.minLat,self.maxLat)
            if mp is None:
                mp = GoogleMap().getPlatParams(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)             
        else:
            raise ValueError("Base type %s not yet supported" % self.baseType)
        return mp
    
    def getStatus(self):
        return getStatus(self.statusFname)
        
    def run(self):
        if os.path.exists(self.baseMapFname) and "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output file exists
        else:
            updateStatus(self.statusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            try:
                if self.baseType == "map":
                    image, mp = GoogleMap().getPlat(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)
                elif self.baseType == "satellite": 
                    image, mp = GoogleMap().getPlat(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=True)
                elif self.baseType == "plat":
                    image, mp = PlatFetcher().getPlat(self.name,self.minLng,self.maxLng,self.minLat,self.maxLat)
                    if mp is None:
                        image, mp = GoogleMap().getPlat(self.minLng,self.maxLng,self.minLat,self.maxLat,satellite=False)             
                else:
                    raise ValueError("Base type %s not yet supported" % self.baseType)
                op = open(self.baseMapFname,"wb")
                op.write(asPNG(image))
                op.close()
                updateStatus(self.statusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})

def colorStringToRGB(colorString):
    if colorString == "None": return False
    if colorString[0] != "#": raise ValueError("Invalid color string")
    red = int(colorString[1:3],16)
    green = int(colorString[3:5],16)
    blue = int(colorString[5:7],16)
    return (red,green,blue)

def makeColorPatch(value):
    if value == "None":
        result = "None"
    else:
        result= '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;'
        result += 'background-color:%s;"></div>' % value
    return result

def mostCommon(iterable):
    hist = {}
    for c in iterable:
        if c not in hist: hist[c] = 0
        hist[c] += 1
    sc = [(hist[c],c) for c in iterable]
    sc.sort()
    return sc[-1][1] if sc else None

def getStabClass(alog):
    p3 = gp3.P3_Accessor_ByPos(alog)
    gen = p3.genAnzLog("dat")(startPos=0,endPos=100)
    weatherCodes = [(int(d.data["INST_STATUS"])>>sis.INSTMGR_AUX_STATUS_SHIFT) & sis.INSTMGR_AUX_STATUS_WEATHER_MASK for d in gen]
    stabClasses = [sis.classByWeather.get(c-1,"None") for c in weatherCodes]
    return mostCommon(stabClasses)
    
class ReportPathMap(object):
    """ Generate the path and swath. The parameters for each run (e.g. colors for markers, wedges,
        minimum amplitudes, etc.) are associated with the various drive-arounds which make up
        the run, so these can be included in the path report. """
        
    def __init__(self,reportDir,ticket,instructions,mapParams,region,timeout=1800):
        self.reportDir = reportDir
        self.ticket = ticket
        self.region = region
        self.instructions = instructions
        self.pathHtmlFname = os.path.join(self.reportDir,"%s/pathMap.%d.html" % (self.ticket,self.region))
        self.pathMapFname = os.path.join(self.reportDir,"%s/pathMap.%d.png" % (self.ticket,self.region))
        self.pathStatusFname  = os.path.join(self.reportDir,"%s/pathMap.%d.status" % (self.ticket,self.region))
        self.swathMapFname = os.path.join(self.reportDir,"%s/swathMap.%d.png" % (self.ticket,self.region))
        self.swathStatusFname  = os.path.join(self.reportDir,"%s/swathMap.%d.status" % (self.ticket,self.region))
        self.mapParams = mapParams
        self.timeout = timeout
        self.paramsByLogname = {}
        
    def makePathReport(self,op):
        pathTableString = []
        pathTableString.append('<table style="page-break-after:always;" class="table table-striped table-condensed table-fmt1">')
        pathTableString.append('<thead><tr>')
        pathTableString.append('<th style="width:20%%">%s</th>' % "Analyzer")
        pathTableString.append('<th style="width:20%%">%s</th>' % "Survey Start (GMT)")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Markers")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Wedges")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Swath")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Min Ampl")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Excl Radius")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Stab Class")
        pathTableString.append('</tr></thead>')
        pathTableString.append('<tbody>')
        # Helper to sort surveys by start time
        logHelper = []
        for logname in self.paramsByLogname:
            params = self.paramsByLogname[logname]
            anz,dt,tm = logname.split('-')[:3]
            utime = calendar.timegm(time.strptime(dt+tm, "%Y%m%d%H%M%SZ"))
            logHelper.append((utime,logname))
        logHelper.sort()
        # Iterate through sorted surveys
        for utime,logname in logHelper:
            if "sensor" in logname.lower(): continue
            params = self.paramsByLogname[logname]
            anz,dt,tm = logname.split('-')[:3]            
            pathTableString.append('<tr>')
            pathTableString.append('<td>%s</td>' % anz)
            tstr = time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(utime))
            pathTableString.append('<td>%s</td>' % tstr)
            pathTableString.append('<td>%s</td>' % makeColorPatch(params['marker']))
            pathTableString.append('<td>%s</td>' % makeColorPatch(params['wedges']))
            pathTableString.append('<td>%s</td>' % makeColorPatch(params['swath']))
            pathTableString.append('<td>%s</td>' % params['minAmpl'])
            pathTableString.append('<td>%s</td>' % params['exclRadius'])
            if params['stabClass'] == '*':
                pathTableString.append('<td>%s*</td>' % getStabClass(logname))
            else:
                pathTableString.append('<td>%s</td>' % params['stabClass'])
            pathTableString.append('</tr>')
        pathTableString.append('</tbody>')
        pathTableString.append('</table>')
        op.write("\n".join(pathTableString))
        
    def getStatus(self):
        return getStatus(self.pathStatusFname),getStatus(self.swathStatusFname)
        
    def run(self):
        if "done" in getStatus(self.pathStatusFname) and "done" in getStatus(self.swathStatusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.pathStatusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            updateStatus(self.swathStatusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            mp = self.mapParams
            sl = SurveyorLayers(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
            try:
                if "runs" in self.instructions:
                    pathMaps = []
                    swathMaps = []
                    for ir,params in enumerate(self.instructions["runs"]):
                        showPath = True
                        showSwath = colorStringToRGB(params["swath"])
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
                            pMap,sMap,lognames = sl.makePathAndSwath(analyzer,startEtm,endEtm,showPath,showSwath,report,self.timeout)
                            for n in lognames:
                                if n in self.paramsByLogname:
                                    raise ValueError("Log %s appears in more than one run" % n)
                                self.paramsByLogname[n] = dict(params).copy()
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
                    op = open(self.pathHtmlFname,"wb")
                    self.makePathReport(op)
                    op.close()
                updateStatus(self.pathStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
                updateStatus(self.swathStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.pathStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})
                updateStatus(self.swathStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})          

MT_NONE, MT_CONC, MT_RANK = 0, 1, 2

class ReportMarkerMap(object):
    def __init__(self,reportDir,ticket,instructions,mapParams,region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.peaksHtmlFname = os.path.join(self.reportDir,"%s/peaksMap.%d.html" % (self.ticket,self.region))
        self.markerHtmlFname = os.path.join(self.reportDir,"%s/markerMap.%d.html" % (self.ticket,self.region))
        self.peaksXmlFname = os.path.join(self.reportDir,"%s/peaksMap.%d.xml" % (self.ticket,self.region))
        self.peaksMapFname = os.path.join(self.reportDir,"%s/peaksMap.%d.png" % (self.ticket,self.region))
        self.peaksStatusFname  = os.path.join(self.reportDir,"%s/peaksMap.%d.status" % (self.ticket,self.region))
        self.wedgesMapFname = os.path.join(self.reportDir,"%s/wedgesMap.%d.png" % (self.ticket,self.region))
        self.wedgesStatusFname  = os.path.join(self.reportDir,"%s/wedgesMap.%d.status" % (self.ticket,self.region))
        self.mapParams = mapParams
        
    def getStatus(self):
        return getStatus(self.peaksStatusFname),getStatus(self.wedgesStatusFname)
    
    def makePeakReport(self,op,peakDict):
        if peakDict:
            peakTableString = []
            zoom = 18
            peakTableString.append('<table class="table table-striped table-condensed table-fmt1 table-datatable">')
            peakTableString.append('<thead><tr>')
            peakTableString.append('<th style="width:10%%">%s</th>' % "Rank")
            peakTableString.append('<th style="width:30%%">%s</th>' % "Designation")
            peakTableString.append('<th style="width:20%%">%s</th>' % "Latitude")
            peakTableString.append('<th style="width:20%%">%s</th>' % "Longitude")
            peakTableString.append('<th style="width:10%%">%s</th>' % "Conc")
            peakTableString.append('<th style="width:10%%">%s</th>' % "Ampl")
            peakTableString.append('</tr></thead>')
            peakTableString.append('<tbody>')
            for i in range(len(peakDict)):
                r = i+1
                tstr = time.strftime("%Y%m%dT%H%M%S",time.gmtime(peakDict[r].etm))
                anz = peakDict[r].data['ANALYZER']
                lat = peakDict[r].data['GPS_ABS_LAT']
                lng = peakDict[r].data['GPS_ABS_LONG']
                ch4 = peakDict[r].data['CH4']
                ampl = peakDict[r].data['AMPLITUDE']
                des = "%s_%s" % (anz,tstr)
                coords = "%s,%s" % (lat,lng)
                peakTableString.append('<tr>')
                peakTableString.append('<td>%d</td>' % r)
                peakTableString.append('<td><a href="http://maps.google.com?q=%s+(%s)&z=%d" target="_blank">%s</a></td>' % (coords,des,zoom,des))
                peakTableString.append('<td>%.6f</td>' % lat)
                peakTableString.append('<td>%.6f</td>' % lng)
                peakTableString.append('<td>%.1f</td>' % ch4)
                peakTableString.append('<td>%.2f</td>' % ampl)
                peakTableString.append('</tr>')
            peakTableString.append('</tbody>')
            peakTableString.append('</table>')
            op.write("\n".join(peakTableString))
            
    def makeMarkerReport(self,op,selMarkers):
        if selMarkers:
            zoom = 18
            markerTableString = []
            markerTableString.append('<table class="table table-striped table-condensed table-fmt1 table-datatable">')
            markerTableString.append('<thead><tr>')
            markerTableString.append('<th style="width:30%%">%s</th>' % "Designation")
            markerTableString.append('<th style="width:20%%">%s</th>' % "Latitude")
            markerTableString.append('<th style="width:20%%">%s</th>' % "Longitude")
            markerTableString.append('</tr></thead>')
            markerTableString.append('<tbody>')
            for m,(x,y) in selMarkers:
                coords = "%s,%s" % (m.lat,m.lng)
                markerTableString.append('<tr>')
                markerTableString.append('<td><a href="http://maps.google.com?q=%s+(%s)&z=%d" target="_blank">%s</a></td>' % (coords,m.label,zoom,m.label))
                markerTableString.append('<td>%s</td>' % m.lat)
                markerTableString.append('<td>%s</td>' % m.lng)
                markerTableString.append('</tr>')
            markerTableString.append('</tbody>')
            markerTableString.append('</table>')
            op.write("\n".join(markerTableString))
        
    def makePeakCsv(self,op,peakDict,selMarkers):
        zoom = 18
        writer = csv.writer(op,dialect='excel')
        if peakDict:
            writer.writerow(('Rank','Designation','Latitude','Longitude','Concentration','Amplitude','URL'))
            for i in range(len(peakDict)):
                r = i+1
                tstr = time.strftime("%Y%m%dT%H%M%S",time.gmtime(peakDict[r].etm))
                anz = peakDict[r].data['ANALYZER']
                lat = peakDict[r].data['GPS_ABS_LAT']
                lng = peakDict[r].data['GPS_ABS_LONG']
                coords = "%s,%s" % (lat,lng)
                ch4 = peakDict[r].data['CH4']
                ampl = peakDict[r].data['AMPLITUDE']
                des = "%s_%s" % (anz,tstr)
                url = "http://maps.google.com?q=%s+(%s)&z=%d" % (coords,des,zoom)
                writer.writerow((r,des,lat,lng,ch4,ampl,url))
            return
        
    def makePeakXml(self,op,peakDict,selMarkers):
        zoom = 18
        name = self.instructions["regions"][self.region]["name"]
        excelReport = ExcelXmlReport()
        heading = "Report %s, Region %d (%s)" % (pretty_ticket(self.ticket),self.region+1,name)
        excelReport.makeHeader(heading,["Rank","Designation","Latitude","Longitude","Concentration","Amplitude"],[30,150,80,80,80,80])
        for i in range(len(peakDict)):
            r = i+1
            tstr = time.strftime("%Y%m%dT%H%M%S",time.gmtime(peakDict[r].etm))
            anz = peakDict[r].data['ANALYZER']
            lat = peakDict[r].data['GPS_ABS_LAT']
            lng = peakDict[r].data['GPS_ABS_LONG']
            coords = "%s,%s" % (lat,lng)
            ch4 = peakDict[r].data['CH4']
            ampl = peakDict[r].data['AMPLITUDE']
            des = "%s_%s" % (anz,tstr)
            excelReport.makeDataRow(r,des,lat,lng,ch4,ampl,zoom)
        op.write(excelReport.xmlWorkbook("Region %d (%s)" % (self.region+1,name)))
        return
        
    def run(self):
        markerTypes = {"None":MT_NONE,"Concentration":MT_CONC,"Rank":MT_RANK}
        if "done" in getStatus(self.peaksStatusFname) and "done" in getStatus(self.wedgesStatusFname):
            return  # This has already been computed and the output files exist
        else:
            updateStatus(self.peaksStatusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            updateStatus(self.wedgesStatusFname,{"start":time.strftime("%Y%m%dT%H%M%S")},True)
            mp = self.mapParams
            sl = SurveyorLayers(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
            try:
                markers = []
                MarkerParams = namedtuple('MarkerParams',['label','color','lat','lng'])
                if "markers" in self.instructions:
                    for m in self.instructions["markers"]:
                        lat, lng = m.get("location",(0.0,0.0))
                        mp = MarkerParams(m.get("label","*"), 
                                          colorStringToRGB(m.get("color","#FFFFFF")),
                                          lat,
                                          lng)
                        markers.append(mp)
                runParams = []
                if "runs" in self.instructions:
                    RunParams = namedtuple('RunParams',['analyzer','startEtm','endEtm','minAmpl',
                                              'maxAmpl','mType','mColor','showWedges','exclRadius'])
                    for ir,params in enumerate(self.instructions["runs"]):
                        mType  = MT_RANK
                        mColor = colorStringToRGB(params["marker"])
                        if not mColor: mType = MT_NONE
                        showPeaks = (mType != MT_NONE)
                        showWedges = colorStringToRGB(params["wedges"])
                        if showPeaks or showWedges:
                            startEtm = strToEtm(params["startEtm"])
                            endEtm   = strToEtm(params["endEtm"])
                            analyzer = params["analyzer"]
                            minAmpl  = params["minAmpl"]
                            maxAmpl  = None
                            exclRadius = params["exclRadius"]
                            runParams.append(RunParams(analyzer,startEtm,endEtm,minAmpl,maxAmpl,
                                                mType,mColor,showWedges,exclRadius))
                im1,im2,pkDict,selMarkers = sl.makeMarkers(runParams,markers)
                # Now write out the maps
                if im1 is not None:
                    im1 = backgroundToOverlay(im1)
                    op = open(self.peaksMapFname,"wb")
                    op.write(asPNG(im1))
                    op.close()
                if im2 is not None:
                    im2 = backgroundToOverlay(im2)
                    op = open(self.wedgesMapFname,"wb")
                    op.write(asPNG(im2))
                    op.close()
                op = open(self.peaksHtmlFname,"wb")
                self.makePeakReport(op,pkDict)
                op.close()
                op = open(self.markerHtmlFname,"wb")
                self.makeMarkerReport(op,selMarkers)
                op.close()
                op = open(self.peaksXmlFname,"wb")
                self.makePeakXml(op,pkDict,selMarkers)
                op.close()
                updateStatus(self.peaksStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
                updateStatus(self.wedgesStatusFname,{"done":1, "end":time.strftime("%Y%m%dT%H%M%S")})            
            except:
                msg = traceback.format_exc()
                updateStatus(self.peaksStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})
                updateStatus(self.wedgesStatusFname,{"error":msg, "end":time.strftime("%Y%m%dT%H%M%S")})
                
class PlatFetcher(object):
    def getPlatParams(self,platName,minLng,maxLng,minLat,maxLat,padX=50,padY=50):
        return self.getPlat(platName,minLng,maxLng,minLat,maxLat,padX,padY,fetchPlat=False)
        
    def getPlat(self,platName,minLng,maxLng,minLat,maxLat,padX=50,padY=50,fetchPlat=True):
        tifFile = os.path.join(PLAT_TIF_ROOT, platName+".tif")
        pngFile = os.path.join(PLAT_PNG_ROOT, platName+".png")
        if not os.path.exists(pngFile):
            print 'Convert "%s" "%s"' % ( tifFile, pngFile)
            if not os.path.exists(tifFile):
                return (None, None) if fetchPlat else None
            subprocess.call([IMGCONVERT, tifFile, pngFile])
        p = Image.open(pngFile)
        nx,ny = p.size
        mp = MapParams(minLng,minLat,maxLng,maxLat,nx,ny,padX,padY)
        if not fetchPlat: return mp
        q = Image.new('RGBA',(nx+2*padX,ny+2*padY),(255,255,255,255))
        q.paste(p,(padX,padY))
        return q,mp

class GoogleMap(object):
    def getMap(self,latCen,lonCen,zoom,nx,ny,scale=1,satellite=True):
        url = 'http://maps.googleapis.com/maps/api/staticmap'
        params = dict(center="%.6f,%.6f"%(latCen,lonCen),zoom="%d"%zoom,size="%dx%d" % (nx,ny),scale="%d"%scale,sensor="false")
        if satellite: params["maptype"] = "satellite"
        if APIKEY is not None: params["key"] = APIKEY
        paramStr = urllib.urlencode(params)
        get_url = url+("?%s" % paramStr)
        print get_url
        timeout = 15.0
        nAttempts = 10
        for i in range(nAttempts):
            try:
                socket.setdefaulttimeout(timeout)
                resp = urllib2.urlopen(get_url)
            except urllib2.URLError, e:
                print "Attempt: %d" % (i+1,)
                if hasattr(e, 'reason'):
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                elif hasattr(e, 'code'):
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
                time.sleep(1.0)
            except:
                print "Attempt: %d" % (i+1,)
                print traceback.format_exc()
                time.sleep(1.0)
            else:
                return resp.read()
        raise RuntimeError,"Cannot fetch map after %d attempts" % (nAttempts,)
        
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
            p = Image.open(cStringIO.StringIO(self.getMap(meanLat,meanLng,zoom,mx,my,scale,satellite)))
            q = Image.new('RGBA',(scale*mx+2*padX,scale*my+2*padY),(255,255,255,255))
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
        timeout = 5.0
        try:
            socket.setdefaulttimeout(timeout)
            resp = urllib2.urlopen(get_url)
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
            raise
        except:
            print traceback.format_exc()
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
        return Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
    
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
        result = process(source,self.nWindow,self.stabClass,self.minLeak,self.minAmpl,self.astdParams)
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
                        temp = Image.new('RGBA',(xmax-xmin+1,ymax-ymin+1),(0,0,0,0))
                        tdraw = ImageDraw.Draw(temp)
                        tdraw.polygon([(x1-xmin,y1-ymin),(x2-xmin,y2-ymin),(x3-xmin,y3-ymin),(x4-xmin,y4-ymin)],
                                        fill=makeSwath+(128,),outline=makeSwath+(200,))
                        mask = (self.padX+xmin,self.padY+ymin)
                        sv = overBackground(temp,sv,mask)
                        
            lastLng, lastLat, lastDeltaLng, lastDeltaLat = lng, lat, deltaLng, deltaLat
    
    def makePathAndSwath(self,analyzer,startEtm,endEtm,makePath,makeSwath,reportFunc=None,timeout=None):
        """Use analyzer name, start and end epoch times to make a REST call to P3 to draw the path taken 
        by the vehicle and the associated swath. Only points lying in the layer rectangle (within the padded region)
        are displayed. There may be many drive-arounds (represented by a distinct LOGNAMEs) associated with 
        single run. Return a set of these, together with images of the path and swath"""
        lognames = set()
        startTime = time.clock()
        colors = dict(normal=(0,0,255,255),analyze=(0,0,0,255),inactive=(255,0,0,255))
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
        def colorPathFromInstrumentStatus(instStatus,color):
            if (instStatus & sis.INSTMGR_STATUS_MASK) != sis.INSTMGR_STATUS_GOOD:
                color = colors["inactive"]
                lastColor[0] = color
            return color
        ov, sv = None, None
        if makePath:
            ov = Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            odraw = ImageDraw.Draw(ov)
        if makeSwath:
            sv = Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            sdraw = ImageDraw.Draw(sv)
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
            instStatus = m.data.get("INST_STATUS",0)
            color = getColorFromValveMask(mask)
            color = colorPathFromInstrumentStatus(instStatus,color)
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
                if (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY):
                    lognames.add(m.data.get("LOGNAME",""))
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
        return ov, sv, lognames
            
    def makeMarkers(self,runParams,markers):
        markersByRank = {}
        peaks = []
        anyPeaks = False
        anyWedges = False
        
        for r,(analyzer,startEtm,endEtm,minAmpl,maxAmpl,mType,mColor,makeWedges,exclRadius) in enumerate(runParams):
            # runParams specifies parameters for each region in turn, and r is the region number
            if not mColor: mType = MT_NONE
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
        # Select the markers that lie within this region
        selMarkers = []
        for m in markers:
            x,y = self.xform(m.lng,m.lat)
            if (self.minLng<=m.lng<self.maxLng) and (self.minLat<=m.lat<self.maxLat):
                selMarkers.append((m,(x,y)))
        
        peaks.sort()
        if anyPeaks or selMarkers:
            ov1 = Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            # Count ranked markers
            nRanked = 0
            for amp,m,region in peaks:
                mType = runParams[region].mType
                if mType == MT_RANK:
                    lat = m.data["GPS_ABS_LAT"]
                    lng = m.data["GPS_ABS_LONG"]
                    if (self.minLng<=lng<self.maxLng) and (self.minLat<=lat<self.maxLat) and (amp>minAmpl) and ((maxAmpl is None) or (amp<=maxAmpl)): nRanked += 1
            rank = nRanked
            #
            for amp,m,region in peaks:
                analyzer,startEtm,endEtm,minAmpl,maxAmpl,mType,mColor,makeWedges,exclRadius = runParams[region]
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                amp = m.data["AMPLITUDE"]
                ch4 = m.data["CH4"]
                x,y = self.xform(lng,lat)
                if (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY) and \
                   (amp>minAmpl) and ((maxAmpl is None) or (amp<=maxAmpl)):
                    if mType in [MT_CONC, MT_RANK]:
                        if mType == MT_CONC:
                            size = (self.ny/1000.0)*amp**0.25    # Make these depend on number of pixels in the image
                            fontsize = min(100,int(18.0*size))
                            color = "%02x%02x%02x" % tuple(mColor)
                            msg = "%.1f" % ch4
                        elif mType == MT_RANK:
                            size = (self.ny/1000.0)
                            fontsize = min(100,int(20.0*size))
                            color = "%02x%02x%02x" % tuple(mColor)
                            if (self.minLng<=lng<self.maxLng) and (self.minLat<=lat<self.maxLat):
                                msg = "%d" % rank
                                markersByRank[rank] = m
                                rank -= 1
                            else:
                                msg = "*"
                        buff = cStringIO.StringIO(GoogleMarkers().getMarker(size,fontsize,msg,color))
                        b = Image.open(buff)
                        bx,by = b.size
                        box = (self.padX+x-bx//2,self.padY+y-by)
                        ov1 = overBackground(b,ov1,box)
            for m,(x,y) in selMarkers:
                size = (self.ny/1000.0)
                fontsize = min(100,int(14.0*size))
                color = "%02x%02x%02x" % tuple(m.color)
                buff = cStringIO.StringIO(GoogleMarkers().getMarker(size,fontsize,m.label,color))
                b = Image.open(buff)
                bx,by = b.size
                box = (self.padX+x-bx//2,self.padY+y-by)
                ov1 = overBackground(b,ov1,box)

        if anyWedges:
            ov2 = Image.new('RGBA',(self.nx+2*self.padX,self.ny+2*self.padY),(0,0,0,0))
            odraw2 = ImageDraw.Draw(ov2)
            for amp,m,region in peaks:
                analyzer,startEtm,endEtm,minAmpl,maxAmpl,mType,mColor,makeWedges,exclRadius = runParams[region]
                if not makeWedges: continue
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                vcar = getPossibleNaN(m.data,"CAR_SPEED",0.0)
                windN = getPossibleNaN(m.data,"WIND_N",0.0)
                windE = getPossibleNaN(m.data,"WIND_E",0.0)
                dstd  = DTR*getPossibleNaN(m.data,"WIND_DIR_SDEV",0.0)
                x,y = self.xform(lng,lat)
                if np.isfinite(dstd) and (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY) and \
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
                    b = Image.new('RGBA',(2*radius+1,2*radius+1),(0,0,0,0))
                    bdraw = ImageDraw.Draw(b)
                    bdraw.pieslice((0,0,2*radius,2*radius),int(minBearing-90.0),int(maxBearing-90.0),fill=makeWedges+(128,),
                                   outline=(0,0,0,255))
                    ov2 = overBackground(b,ov2,(self.padX+x-radius,self.padY+y-radius))
                   
        return ov1, ov2, markersByRank, selMarkers

class BubbleMaker(object):
    def getMarker1(self,size):
        def nint(x): return int(round(x))
        nx = nint(36 * size + 1)
        ny = nint(65 * size + 1)
        xoff = (nx - 1) / 2
        h = ny - 1
        r = (nx - 1) / 2.0
        R = h * (0.5 * h / r - 1.0)
        phi = np.arcsin(R / (R + r))
        b = Image.new('RGBA',(nx,ny),(255,255,255,255))
        bdraw = ImageDraw.Draw(b)
        n1 = 10
        n2 = 20
        arc1 = [(nint(xoff - R + R * np.cos(th)), nint(ny - 1 - R*np.sin(th))) for th in np.linspace(0.0,0.5*np.pi-phi,n1,endpoint=False)]
        arc2 = [(nint(xoff - r * np.sin(th)), nint(r + r * np.cos(th))) for th in np.linspace(phi, 2 * np.pi - phi, n2, endpoint=False)]
        arc3 = [(nint(xoff + R - R * np.cos(th)), nint(ny - 1 - R*np.sin(th))) for th in np.linspace(0.5*np.pi-phi,0.0,n1,endpoint=False)]
        bdraw.polygon(arc1 + arc2 + arc3, fill=(255,255,0,255), outline=(0,0,0,255))
        bdraw.line(arc1 + arc2 + arc3, fill=(0,0,0,255), width=3)
        return asPNG(b)
    
    def getMarker(self,size):
        def nint(x): return int(round(x))
        t = 2
        r = 18*size - t
        h = 65*size - 2*t
        nx = nint(36*size + 1)
        ny = nint(65*size + 1)
        w = size
        R = ((h-r)*(h-r) - (r*r - 0.25*w*w))/float(2*r-w)
        phi = np.arcsin((R + 0.5*w) / (R + r))
        cen1 = ( -(R+0.5*w), h-r )
        cen2 = ( 0, 0 )
        cen3 = ( (R+0.5*w), h-r )
        xoff = r + t
        yoff = r + t
        b = Image.new('RGBA',(nx,ny),(255,255,255,255))
        bdraw = ImageDraw.Draw(b)
        n1 = 20
        n2 = 40
        arc1 = [(xoff + nint(cen1[0] + R * np.cos(th)), nint(yoff + cen1[1] - R*np.sin(th))) for th in np.linspace(0.0,0.5*np.pi-phi,n1,endpoint=False)]
        arc2 = [(xoff + nint(cen2[0] - r * np.sin(th)), nint(yoff + cen2[1] + r * np.cos(th))) for th in np.linspace(phi, 2 * np.pi - phi, n2, endpoint=False)]
        arc3 = [(xoff + nint(cen3[0] - R * np.cos(th)), nint(yoff + cen3[1] - R*np.sin(th))) for th in np.linspace(0.5*np.pi-phi,0.0,n1,endpoint=True)]
        bdraw.polygon(arc1 + arc2 + arc3, fill=(255,255,0,255), outline=(0,0,0,255))
        bdraw.line(arc1 + arc2 + arc3 + arc1[0:1], fill=(0,0,0,255), width=t)
        return asPNG(b)
        