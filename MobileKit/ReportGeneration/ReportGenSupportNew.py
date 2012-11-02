#!/usr/bin/python
#
"""
File Name: ReportGenSupportNew.py
Purpose: Support for Surveyor report generation which uses more client-side
 JavaScript to assemble report maps

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
import cPickle
import cStringIO
import geohash
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
import ImageFont
import ImageMath
from Host.Common.SwathProcessor import process
import re
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
from ReportCommon import MapRect, LatLng
if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# Executable for HTML to PDF conversion
configFile = os.path.splitext(appPath)[0] + ".ini"
WKHTMLTOPDF = None
IMGCONVERT = None
APIKEY = None
PLAT_TIF_ROOT = r"S:\Projects\Picarro Surveyor\Files from PGE including TIFF maps\GEMS\CompTif\Gas\Distribution"
PLAT_PNG_ROOT = r"static\plats"

if os.path.exists(configFile):
    config = ConfigObj(configFile)
    WKHTMLTOPDF = config["HelperApps"]["wkhtml_to_pdf"]
    IMGCONVERT = config["HelperApps"]["image_convert"]
    APIKEY = config["P3Logs"].get("apikey", None)

    if "Plats" in config:
        PLAT_TIF_ROOT = config["Plats"]["tif_root"]
        PLAT_PNG_ROOT = config["Plats"]["png_root"]

SVCURL = "http://localhost:5200/rest"
RTD = 180.0 / math.pi
DTR = math.pi / 180.0
EARTH_RADIUS = 6378100
SUMMARY_REGION = 0
NOT_A_NUMBER = 1e1000 / 1e1000

PLAT_TIF_ROOT = os.path.join(appDir, PLAT_TIF_ROOT)
PLAT_PNG_ROOT = os.path.join(appDir, PLAT_PNG_ROOT)
if not os.path.exists(PLAT_PNG_ROOT):
    os.makedirs(PLAT_PNG_ROOT)
MapParams = namedtuple("MapParams", ["minLng", "minLat", "maxLng",
                       "maxLat", "nx", "ny", "padX", "padY"])

statusLock = threading.Lock()
statusLocks = {}


def partition(mapRect, ny, nx):
    swCorner = mapRect.swCorner
    neCorner = mapRect.neCorner
    dx = float(neCorner.lng - swCorner.lng) / nx
    dy = float(neCorner.lat - swCorner.lat) / ny
    maxLat = neCorner.lat
    rectList = []
    for my in range(ny):
        minLat = maxLat - dy
        minLng = swCorner.lng
        rowList = []
        for mx in range(nx):
            maxLng = minLng + dx
            rowList.append(
                MapRect(LatLng(minLat, minLng), LatLng(maxLat, maxLng)))
            minLng = maxLng
        rectList.append(rowList)
        maxLat = minLat
    return rectList


def overBackground(a, b, box):
    # Overlay the RGBA image a on top of an RGBA background image b,
    #  where the color channels in b are multiplied by the alpha.
    #  Returns a reference to the modified image b, which can
    #  be used as the background in further operations.

    # Alternatively, b can be an RGB background image which is assumed
    #  to be opaque. The result is then an RGB image again with an
    #  opaque background
    b.paste(a.convert('RGB'), box, a)
    return b


def backgroundToOverlay(im):
    r, g, b, a = im.split()
    r = ImageMath.eval("int(256 * n / (d + 1))", n=r, d=a).convert('L')
    g = ImageMath.eval("int(256 * n / (d + 1))", n=g, d=a).convert('L')
    b = ImageMath.eval("int(256 * n / (d + 1))", n=b, d=a).convert('L')
    return Image.merge("RGBA", (r, g, b, a))


def merge_dictionary(dst, src):
    stack = [(dst, src)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst


def extract_dictionary(src, keys):
    """Create a new dictionary from src containing only the specified keys"""
    return {k: src[k] for k in keys}


def asPNG(image):
    output = cStringIO.StringIO()
    image.save(output, format="PNG")
    try:
        return output.getvalue()
    finally:
        output.close()


def strToEtm(s):
    return calendar.timegm(time.strptime(s, "%Y-%m-%d  %H:%M"))


def pretty_ticket(ticket):
    t = ticket.upper()
    return " ".join([t[s:s + 4] for s in range(0, 32, 4)])


def getPossibleNaN(d, k, default):
    try:
        result = float(d.get(k, default))
    except:
        result = NOT_A_NUMBER
    return result


def lod2dol(listOfDict):
    """Starting with a list of dictionaries all of which have the same keys, convert to a dictionary
    of lists that can be more compactly JSON encoded"""
    result = {}
    if listOfDict:
        for k in listOfDict[0].keys():
            result[k] = [d[k] for d in listOfDict]
    return result


def dol2lod(dictOfList):
    if dictOfList:
        v = dictOfList.values()[0]
        n = len(v)
        return [{k:dictOfList[k][i] for k in dictOfList} for i in range(n)]
    else:
        return []


class ReportCompositeMap(object):
    def __init__(self, reportDir, ticket, region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.region = region
        self.compositeMapFname = os.path.join(self.reportDir, "%s/compositeMap.%d.png" % (self.ticket, self.region))
        self.statusFname = os.path.join(self.reportDir, "%s/compositeMap.%d.status" % (self.ticket, self.region))

    def getStatus(self):
        return getStatus(self.statusFname)

    def run(self):
        if "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.statusFname, {"start":
                         time.strftime("%Y%m%dT%H%M%S")}, True)
            try:
                files = {}
                imageFnames = {}
                statusFnames = {}
                targetDir = os.path.join(self.reportDir, "%s" % self.ticket)
                for dirPath, dirNames, fileNames in os.walk(targetDir):
                    for name in fileNames:
                        atoms = name.split('.')
                        if len(atoms) >= 2 and atoms[-2] == ("%d" % self.region) and atoms[-1] == 'png':
                            key = '.'.join(atoms[:-2])
                            base = '.'.join(atoms[:-1])
                            # Having found a png file, look for the associated .status file
                            #  to see if the png file is valid
                            statusName = os.path.join(
                                targetDir, base + '.status')
                            pngName = os.path.join(targetDir, name)
                            if "done" in getStatus(statusName):
                                try:
                                    files[key] = file(pngName, "rb").read()
                                    imageFnames[key] = pngName
                                    statusFnames[key] = statusName
                                except:
                                    pass
                layers = ['baseMap', 'pathMap', 'swathMap',
                          'wedgesMap', 'peaksMap']
                compositeImage = None
                for layer in layers:
                    if layer in files:
                        image = Image.open(cStringIO.StringIO(files[layer]))
                        if compositeImage is None:
                            compositeImage = Image.new(
                                'RGBA', image.size, (0, 0, 0, 0))
                        compositeImage = overBackground(
                            image, compositeImage, None)
                        # Remove the component status and image files
                        os.remove(statusFnames[layer])
                        os.remove(imageFnames[layer])
                with open(self.compositeMapFname, "wb") as op:
                    op.write(asPNG(compositeImage))
                updateStatus(self.statusFname, {"done": 1,
                             "end": time.strftime("%Y%m%dT%H%M%S")})
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname, {"error":
                             msg, "end": time.strftime("%Y%m%dT%H%M%S")})


class ReportPDF(object):
    def __init__(self, reportDir, ticket, instructions, region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.PdfFname = os.path.join(
            self.reportDir, "%s/report.%d.pdf" % (self.ticket, self.region))
        self.statusFname = os.path.join(self.reportDir, "%s/report.%d.status" %
                                        (self.ticket, self.region))

    def getStatus(self):
        return getStatus(self.statusFname)

    def run(self):
        style = """
        <style>
            table.table-fmt1 td {text-align:center; vertical-align:middle; }
            table.table-fmt1 th {text-align:center; }
        </style>
        """
        if self.region == 0:
            name = self.instructions["summary"]["name"]
            heading = "<h2>Report %s, Summary (%s)</h2>" % (
                pretty_ticket(self.ticket), name)
        else:
            name = self.instructions["regions"][self.region - 1]["name"]
            heading = "<h2>Report %s, Region %d (%s)</h2>" % (
                pretty_ticket(self.ticket), self.region, name)
        peaksHeading = "<h3>Methane Peaks Detected</h3>"
        markerHeading = "<h3>Markers</h3>"
        surveyHeading = "<h3>Surveys</h3>"
        if "done" in getStatus(self.statusFname):
            return  # This has already been computed and the output exists
        else:
            updateStatus(self.statusFname, {"start":
                         time.strftime("%Y%m%dT%H%M%S")}, True)
            try:
                # Find the peaks report file and the path report file
                peaksReportFname = os.path.join(self.reportDir, "%s/peaksMap.%d.html" % (self.ticket, self.region))
                markerReportFname = os.path.join(self.reportDir, "%s/markerMap.%d.html" % (self.ticket, self.region))
                pathReportFname = os.path.join(self.reportDir, "%s/pathMap.%d.html" % (self.ticket, self.region))
                compositeMapFname = os.path.join(self.reportDir, "%s/compositeMap.%d.png" % (self.ticket, self.region))

                params = {"ticket": self.ticket, "region": self.region}
                compositeMapUrl = "%s/getComposite?%s" % (
                    SVCURL, urllib.urlencode(params))
                # compositeMapUrl = "file:%s" % urllib.pathname2url(compositeMapFname)
                # Read in the peaks report and path report
                peaksReport = peaksHeading
                fp = None
                try:
                    fp = file(peaksReportFname, "rb")
                    peaksReport += fp.read()
                except:
                    peaksReport = ""
                finally:
                    if fp:
                        fp.close()

                markerReport = markerHeading
                fp = None
                try:
                    fp = file(markerReportFname, "rb")
                    markerReport += fp.read()
                except:
                    markerReport = ""
                    print traceback.format_exc()
                finally:
                    if fp:
                        fp.close()

                pathReport = surveyHeading
                fp = None
                try:
                    fp = file(pathReportFname, "rb")
                    pathReport += fp.read()
                except:
                    pathReport = ""
                finally:
                    if fp:
                        fp.close()
                # Generate the composite map as an image
                # pic = '<img id="image" src="%s" alt="" width="95%%" style="-moz-transform:rotate(90deg);-webkit-transform:rotate(90deg);"></img>' % compositeMapUrl
                pic = '<img id="image" src="%s" alt="" width="95%%"></img>' % compositeMapUrl
                s = style + heading + peaksReport + \
                    markerReport + pathReport + heading + pic
                proc = subprocess.Popen([WKHTMLTOPDF, "-", self.PdfFname],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout = proc.communicate(s)
                updateStatus(self.statusFname, {"done": 1,
                             "end": time.strftime("%Y%m%dT%H%M%S")})
            except:
                msg = traceback.format_exc()
                updateStatus(self.statusFname, {"error":
                             msg, "end": time.strftime("%Y%m%dT%H%M%S")})


class LayerFilenamesGetter(object):
    def __init__(self, reportDir, ticket):
        self.reportDir = reportDir
        self.ticket = ticket

    def run(self):
        files = {}
        targetDir = os.path.join(self.reportDir, "%s" % self.ticket)
        for dirPath, dirNames, fileNames in os.walk(targetDir):
            for name in fileNames:
                atoms = name.split('.')
                if atoms[-1] == 'png':
                    key = '.'.join(atoms[:-1])
                    files[key] = name
        return files


class ReportStatus(object):
    def __init__(self, reportDir, ticket):
        self.reportDir = reportDir
        self.ticket = ticket

    def run(self):
        files = {}
        targetDir = os.path.join(self.reportDir, "%s" % self.ticket)
        for dirPath, dirNames, fileNames in os.walk(targetDir):
            for name in fileNames:
                atoms = name.split('.')
                if len(atoms) >= 2 and atoms[-2] == 'json' and atoms[-1] == 'status':
                    key = '.'.join(atoms[:-1])
                    try:
                        files[key] = json.load(
                            file(os.path.join(dirPath, name), "rb"))
                    except:
                        files[key] = {}
        return dict(files=files)


class ReportGen(object):
    def __init__(self, reportDir, contents):
        self.reportDir = reportDir
        self.contents = contents
        self.instructions = None
        self.ticket = None

    def run(self):
        self.ticket = getTicket(self.contents)
        targetDir = os.path.join(self.reportDir, "%s" % self.ticket)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
        instrFname = os.path.join(self.reportDir, "%s/json" % self.ticket)
        statusFname = os.path.join(
            self.reportDir, "%s/json.status" % self.ticket)
        try:
            if os.path.exists(statusFname):  # This job has already been done
                status = getStatus(statusFname)
                # If there is an "error" in the status, we delete everything in this directory
                #  so as to get a fresh start
                if "error" in status:
                    for dirPath, dirNames, fileNames in os.walk(targetDir):
                        for name in fileNames:
                            os.remove(os.path.join(targetDir, name))
                else:
                    return self.ticket
            if os.path.exists(instrFname):
                with open(instrFname, "rb") as ip:
                    if ip.read() != self.contents:
                        updateStatus(statusFname, {"start":
                                     time.strftime("%Y%m%dT%H%M%S")}, True)
                        raise ValueError(
                            "MD5 hash collision in cached instructions")
            else:
                with open(instrFname, "wb") as ip:
                    ip.write(self.contents)

            updateStatus(
                statusFname, {"start": time.strftime("%Y%m%dT%H%M%S")}, True)
            # Read the instructions as a JSON object
            self.instructions = json.loads(self.contents)
            o = Supervisor(self.reportDir, self.ticket, self.instructions)
            th = threading.Thread(target=o.run)
            th.setDaemon(True)
            th.start()
        except:
            msg = traceback.format_exc()
            updateStatus(statusFname, {"error": msg, "end":
                         time.strftime("%Y%m%dT%H%M%S")})
        return self.ticket


class ReportBaseMap(object):
    def __init__(self, reportDir, ticket, instructions, region, logFunc):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.logFunc = logFunc
        self.baseData = os.path.join(
            self.reportDir, "%s/baseData.%d.json" % (self.ticket, region))

        # region 0 is a special case for the summary map
        if region == SUMMARY_REGION:
            self.name = self.instructions["summary"]["name"]
            self.minLat, self.minLng = self.instructions["summary"]["swCorner"]
            self.maxLat, self.maxLng = self.instructions["summary"]["neCorner"]
            self.baseType = self.instructions["summary"]["baseType"]
        else:
            region -= 1
            self.name = self.instructions["regions"][region]["name"]
            self.minLat, self.minLng = self.instructions[
                "regions"][region]["swCorner"]
            self.maxLat, self.maxLng = self.instructions[
                "regions"][region]["neCorner"]
            self.baseType = self.instructions["regions"][region]["baseType"]

    def getMapParams(self):
        mpList = []
        for t in self.baseType:
            if t == "map":
                mp = GoogleMap(self.logFunc).getPlatParams(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            elif t == "satellite":
                mp = GoogleMap(self.logFunc).getPlatParams(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=True)
            elif t == "plat":
                #mp = PlatFetcher().getPlatParams(self.name, self.minLng,
                #                                 self.maxLng, self.minLat, self.maxLat)
                if mp is None:
                    mp = GoogleMap(self.logFunc).getPlatParams(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            else:
                raise ValueError("Base type %s not yet supported" % t)
            mpList.append(mp)
        return mpList

    def run(self):
        paramList = []
        for t in self.baseType:
            if t == "map":
                imageParams, mp = GoogleMap(self.logFunc).getPlat(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            elif t == "satellite":
                imageParams, mp = GoogleMap(self.logFunc).getPlat(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=True)
            elif t == "plat":
                imageParams, mp = PlatFetcher().getPlat(self.name, self.minLng,
                                                  self.maxLng, self.minLat, self.maxLat)
                if mp is None:
                    imageParams, mp = GoogleMap(self.logFunc).getPlat(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            else:
                raise ValueError("Base type %s not yet supported" % t)
            paramList.append((imageParams, mp))
        regionParams = dict(name=self.name, region=self.region, type=t)
        if self.region == SUMMARY_REGION:
            regionParams["nx"] = self.instructions["summary"]["nx"]
            regionParams["ny"] = self.instructions["summary"]["ny"]
        with open(self.baseData, "wb") as op:
            json.dump((regionParams, paramList), op)


def colorStringToRGB(colorString):
    if colorString == "None":
        return False
    if colorString[0] != "#":
        raise ValueError("Invalid color string")
    red = int(colorString[1:3], 16)
    green = int(colorString[3:5], 16)
    blue = int(colorString[5:7], 16)
    return (red, green, blue)


def makeColorPatch(value):
    if value == "None":
        result = "None"
    else:
        result = '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;'
        result += 'background-color:%s;"></div>' % value
    return result


def mostCommon(iterable):
    hist = {}
    for c in iterable:
        if c not in hist:
            hist[c] = 0
        hist[c] += 1
    sc = [(hist[c], c) for c in iterable]
    sc.sort()
    return sc[-1][1] if sc else None


def getStabClass(alog):
    p3 = gp3.P3_Accessor_ByPos(alog)
    gen = p3.genAnzLog("dat")(startPos=0, endPos=100)
    weatherCodes = [(int(d.data["INST_STATUS"]) >> sis.INSTMGR_AUX_STATUS_SHIFT) & sis.INSTMGR_AUX_STATUS_WEATHER_MASK for d in gen]
    stabClasses = [sis.classByWeather.get(c - 1, "None") for c in weatherCodes]
    return mostCommon(stabClasses)


class ReportPathMap(object):
    """ Generate the path and swath. The parameters for each run (e.g. colors for markers, wedges,
        minimum amplitudes, etc.) are associated with the various drive-arounds which make up
        the run, so these can be included in the path report. """

    def __init__(self, reportDir, ticket, instructions, mapParams, region, logFunc, timeout=1800):
        self.reportDir = reportDir
        self.ticket = ticket
        self.region = region
        self.instructions = instructions
        self.pathHtmlFname = os.path.join(
            self.reportDir, "%s/path.%d.html" % (self.ticket, self.region))
        if "summary" in instructions:
            self.pathData = os.path.join(
                self.reportDir, "%s/pathData.json" % (self.ticket,))
        self.mapParams = mapParams
        self.timeout = timeout
        self.logFunc = logFunc
        self.paramsByLogname = {}

    def makePathReport(self, op):
        pathTableString = []
        pathTableString.append('<table style="page-break-after:always;" class="table table-striped table-condensed table-fmt1">')
        pathTableString.append('<thead><tr>')
        pathTableString.append('<th style="width:20%%">%s</th>' % "Analyzer")
        pathTableString.append(
            '<th style="width:20%%">%s</th>' % "Survey Start (GMT)")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Markers")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Wedges")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Swath")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Min Ampl")
        pathTableString.append(
            '<th style="width:10%%">%s</th>' % "Excl Radius")
        pathTableString.append('<th style="width:10%%">%s</th>' % "Stab Class")
        pathTableString.append('</tr></thead>')
        pathTableString.append('<tbody>')
        # Helper to sort surveys by start time
        logHelper = []
        for logname in self.paramsByLogname:
            params = self.paramsByLogname[logname]
            anz, dt, tm = logname.split('-')[:3]
            utime = calendar.timegm(time.strptime(dt + tm, "%Y%m%d%H%M%SZ"))
            logHelper.append((utime, logname))
        logHelper.sort()
        # Iterate through sorted surveys
        for utime, logname in logHelper:
            if "sensor" in logname.lower():
                continue
            params = self.paramsByLogname[logname]
            anz, dt, tm = logname.split('-')[:3]
            pathTableString.append('<tr>')
            pathTableString.append('<td>%s</td>' % anz)
            tstr = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(utime))
            pathTableString.append('<td>%s</td>' % tstr)
            pathTableString.append(
                '<td>%s</td>' % makeColorPatch(params['peaks']))
            pathTableString.append(
                '<td>%s</td>' % makeColorPatch(params['wedges']))
            pathTableString.append(
                '<td>%s</td>' % makeColorPatch(params['swath']))
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

    def run(self):
        mp = self.mapParams
        saveData = (self.region == SUMMARY_REGION)
        savedData = []
        sl = SurveyorLayers(mp.minLng, mp.minLat, mp.maxLng,
                            mp.maxLat, mp.nx, mp.ny, mp.padX, mp.padY)
        # We either have to treat each regional map on its own, and generate the path
        #  and swath from the database, or alternatively, if it is part of a set with
        #  a summary map, the path and swath are inherited from those calculated for
        #  the summary.
        if "summary" in self.instructions and self.region != SUMMARY_REGION:
            with open(self.pathData, "rb") as op:
                paramsByLogname, savedData = json.load(op)
            lognames = sl.makeSubmapPath(savedData)
            for n in lognames:
                if n in self.paramsByLogname:
                    raise ValueError(
                        "Log %s appears in more than one run" % n)
                self.paramsByLogname[n] = paramsByLogname[n]
        else:
            if "runs" in self.instructions:
                for ir, params in enumerate(self.instructions["runs"]):
                    showPath = params.get("path", True)
                    showSwath = colorStringToRGB(params["swath"])

                    def report(nPoints):
                        self.logFunc({"run%d" % (ir,): "%d points" % nPoints})
                    if showPath or showSwath:
                        startEtm = strToEtm(params["startEtm"])
                        endEtm = strToEtm(params["endEtm"])
                        analyzer = params["analyzer"]
                        if showSwath:
                            minAmpl = params["minAmpl"]
                            stabClass = params["stabClass"]
                            sl.setSwathParams(minAmpl=minAmpl, stabClass=stabClass)
                        lognames, savedPath, savedSwath = \
                            sl.makePathAndSwath(analyzer, startEtm, endEtm, showPath,
                                                showSwath, report, self.timeout, saveData)
                        for n in lognames:
                            if n in self.paramsByLogname:
                                raise ValueError(
                                    "Log %s appears in more than one run" % n)
                            self.paramsByLogname[n] = dict(params).copy()
                        savedData.append((lognames, savedPath, savedSwath))
        with open(self.pathHtmlFname, "wb") as op:
            self.makePathReport(op)
        if saveData:
            with open(self.pathData, "wb") as op:
                json.dump([self.paramsByLogname, savedData], op)

MT_NONE, MT_CONC, MT_RANK = 0, 1, 2


class ReportMarkerMap(object):
    def __init__(self, reportDir, ticket, instructions, mapParams, region, logFunc):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        if "summary" in instructions:
            self.markersData = os.path.join(
                self.reportDir, "%s/markers.json" % (self.ticket,))
        self.peaksHtmlFname = os.path.join(
            self.reportDir, "%s/peaks.%d.html" % (self.ticket, self.region))
        self.markerHtmlFname = os.path.join(
            self.reportDir, "%s/markers.%d.html" % (self.ticket, self.region))
        self.peaksXmlFname = os.path.join(
            self.reportDir, "%s/peaks.%d.xml" % (self.ticket, self.region))
        self.mapParams = mapParams
        self.logFunc = logFunc
        self.digits = re.compile("\d+")

    def makePeakReport(self, op, peaks):
        peakTableString = []
        zoom = 18
        peakTableString.append('<table class="table table-striped table-condensed table-fmt1 table-datatable">')
        peakTableString.append('<thead><tr>')
        peakTableString.append('<th style="width:10%%">%s</th>' % "Rank")
        peakTableString.append(
            '<th style="width:30%%">%s</th>' % "Designation")
        peakTableString.append('<th style="width:20%%">%s</th>' % "Latitude")
        peakTableString.append('<th style="width:20%%">%s</th>' % "Longitude")
        peakTableString.append('<th style="width:10%%">%s</th>' % "Conc")
        peakTableString.append('<th style="width:10%%">%s</th>' % "Ampl")
        peakTableString.append('</tr></thead>')
        peakTableString.append('<tbody>')
        for data in peaks:
            msg = data['TEXT']
            pkColor = data['PEAK_COLOR']
            wedgeColor = data['WEDGE_COLOR']
            if self.digits.match(msg):
                tstr = time.strftime("%Y%m%dT%H%M%S", time.gmtime(data['EPOCH_TIME']))
                anz = data['ANALYZER']
                lat, lng = geohash.decode(data['LOCATION'])
                ampl = data['AMPLITUDE']
                ch4 = data['CH4']
                des = "%s_%s" % (anz, tstr)
                coords = "%s,%s" % (lat, lng)
                peakTableString.append('<tr>')
                peakTableString.append('<td>%s</td>' % msg)
                peakTableString.append('<td><a href="http://maps.google.com?q=%s+(%s)&z=%d" target="_blank">%s</a></td>' % (coords, des, zoom, des))
                peakTableString.append('<td>%.6f</td>' % lat)
                peakTableString.append('<td>%.6f</td>' % lng)
                peakTableString.append('<td>%.1f</td>' % ch4)
                peakTableString.append('<td>%.2f</td>' % ampl)
                peakTableString.append('</tr>')
        peakTableString.append('</tbody>')
        peakTableString.append('</table>')
        op.write("\n".join(peakTableString))

    def makeMarkerReport(self, op, selMarkers):
        zoom = 18
        markerTableString = []
        markerTableString.append('<table class="table table-striped table-condensed table-fmt1 table-datatable">')
        markerTableString.append('<thead><tr>')
        markerTableString.append(
            '<th style="width:30%%">%s</th>' % "Designation")
        markerTableString.append('<th style="width:20%%">%s</th>' % "Latitude")
        markerTableString.append(
            '<th style="width:20%%">%s</th>' % "Longitude")
        markerTableString.append('</tr></thead>')
        markerTableString.append('<tbody>')
        for m in dol2lod(selMarkers):
            lat, lng = geohash.decode(m["LOCATION"])
            coords = "%s,%s" % (lat, lng)
            markerTableString.append('<tr>')
            markerTableString.append('<td><a href="http://maps.google.com?q=%s+(%s)&z=%d" target="_blank">%s</a></td>' % (coords, m["label"], zoom, m["label"]))
            markerTableString.append('<td>%s</td>' % lat)
            markerTableString.append('<td>%s</td>' % lng)
            markerTableString.append('</tr>')
        markerTableString.append('</tbody>')
        markerTableString.append('</table>')
        op.write("\n".join(markerTableString))

    def makePeakCsv(self, op, peaks, selMarkers):
        zoom = 18
        writer = csv.writer(op, dialect='excel')
        writer.writerow(('Rank', 'Designation', 'Latitude',
                        'Longitude', 'Concentration', 'Amplitude', 'URL'))
        for data in peaks:
            msg = data['TEXT']
            pkColor = data['PEAK_COLOR']
            wedgeColor = data['WEDGE_COLOR']
            if self.digits.match(msg):
                tstr = time.strftime("%Y%m%dT%H%M%S", time.gmtime(data['EPOCH_TIME']))
                anz = peakDict[r].data['ANALYZER']
                lat = peakDict[r].data['GPS_ABS_LAT']
                lng = peakDict[r].data['GPS_ABS_LONG']
                coords = "%s,%s" % (lat, lng)
                ch4 = peakDict[r].data['CH4']
                ampl = peakDict[r].data['AMPLITUDE']
                des = "%s_%s" % (anz, tstr)
                url = "http://maps.google.com?q=%s+(%s)&z=%d" % (coords, des, zoom)
                writer.writerow((int(msg), des, lat, lng, ch4, ampl, url))
        return

    def makePeakXml(self, op, peaks, selMarkers):
        zoom = 18
        excelReport = ExcelXmlReport()
        if self.region == SUMMARY_REGION:
            name = self.instructions["summary"]["name"]
            heading = "Report %s, Summary (%s)" % (
                pretty_ticket(self.ticket), name)
        else:
            name = self.instructions["regions"][self.region - 1]["name"]
            heading = "Report %s, Region %d (%s)" % (
                pretty_ticket(self.ticket), self.region, name)
        excelReport.makeHeader(heading, ["Rank", "Designation", "Latitude", "Longitude", "Concentration", "Amplitude"], [30, 150, 80, 80, 80, 80])
        for data in peaks:
            msg = data['TEXT']
            pkColor = data['PEAK_COLOR']
            wedgeColor = data['WEDGE_COLOR']
            if self.digits.match(msg):
                tstr = time.strftime("%Y%m%dT%H%M%S", time.gmtime(data['EPOCH_TIME']))
                anz = data['ANALYZER']
                lat, lng = geohash.decode(data['LOCATION'])
                coords = "%s,%s" % (lat, lng)
                ch4 = data['CH4']
                ampl = data['AMPLITUDE']
                des = "%s_%s" % (anz, tstr)
                excelReport.makeDataRow(int(msg), des, lat, lng, ch4, ampl, zoom)
        op.write(
            excelReport.xmlWorkbook("Region %d (%s)" % (self.region, name)))
        return

    def run(self):
        markerTypes = {"None": MT_NONE, "Concentration": MT_CONC,
                       "Rank": MT_RANK}
        mp = self.mapParams
        sl = SurveyorLayers(mp.minLng, mp.minLat, mp.maxLng,
                            mp.maxLat, mp.nx, mp.ny, mp.padX, mp.padY)
        markers = []
        if "markers" in self.instructions:
            for m in self.instructions["markers"]:
                lat, lng = m.get("location", (0.0, 0.0))
                mp = dict(label=m.get("label", "*"),
                          color=colorStringToRGB(m.get("color", "#FFFFFF")),
                          lat=lat,
                          lng=lng)
                markers.append(mp)

        # We either have to treat each regional map on its own, and generate markers
        #  for that region in its own right, or alternatively, if it is part of a set
        #  of submaps with a summary map, the markers and wedges are inherited from those
        #  calculated for the summary map
        if "summary" in self.instructions and self.region != SUMMARY_REGION:
            with open(self.markersData, "rb") as op:
                savedMarkers = json.load(op)
            pColors, peaks, mColors, selMarkers = sl.makeSubmapMarkers(savedMarkers)
        else:
            runParams = []
            if "runs" in self.instructions:
                RunParams = namedtuple(
                    'RunParams', ['analyzer', 'startEtm', 'endEtm', 'minAmpl',
                                  'maxAmpl', 'path', 'mType', 'mColor', 'showWedges',
                                  'exclRadius'])
                for ir, params in enumerate(self.instructions["runs"]):
                    path = params.get("path", True)
                    mType = MT_RANK
                    mColor = colorStringToRGB(params["peaks"])
                    if not mColor:
                        mType = MT_NONE
                    showPeaks = (mType != MT_NONE)
                    showWedges = colorStringToRGB(params["wedges"])
                    if showPeaks or showWedges:
                        startEtm = strToEtm(params["startEtm"])
                        endEtm = strToEtm(params["endEtm"])
                        analyzer = params["analyzer"]
                        minAmpl = params["minAmpl"]
                        maxAmpl = None
                        exclRadius = params["exclRadius"]
                        runParams.append(
                            RunParams(analyzer, startEtm, endEtm, minAmpl, maxAmpl,
                                      path, mType, mColor, showWedges, exclRadius))
            pColors, peaks, mColors, selMarkers = sl.makeMarkers(runParams, markers)
            # Write out the peak and marker information from the summary region
            if self.region == SUMMARY_REGION:
                with open(self.markersData, "wb") as op:
                    json.dump([list(pColors), peaks,
                               list(mColors), selMarkers], op)

        peaksAsList = dol2lod(peaks)
        with open(self.peaksHtmlFname, "wb") as op:
            self.makePeakReport(op, peaksAsList)
        with open(self.markerHtmlFname, "wb") as op:
            self.makeMarkerReport(op, selMarkers)
        with open(self.peaksXmlFname, "wb") as op:
            self.makePeakXml(op, peaksAsList, selMarkers)


class PlatFetcher(object):
    def getPlatParams(self, platName, minLng, maxLng, minLat, maxLat, padX=50, padY=50):
        return self.getPlat(platName, minLng, maxLng, minLat, maxLat, padX, padY, fetchPlat=False)

    def getPlat(self, platName, minLng, maxLng, minLat, maxLat, padX=50, padY=50, fetchPlat=True):
        tifFile = os.path.join(PLAT_TIF_ROOT, platName + ".tif")
        pngFile = os.path.join(PLAT_PNG_ROOT, platName + ".png")
        if not os.path.exists(pngFile):
            print 'Convert "%s" "%s"' % (tifFile, pngFile)
            if not os.path.exists(tifFile):
                return (None, None) if fetchPlat else None
            subprocess.call([IMGCONVERT, tifFile, pngFile])
        p = Image.open(pngFile)
        nx, ny = p.size
        mp = MapParams(minLng, minLat, maxLng, maxLat, nx, ny, padX, padY)
        if not fetchPlat:
            return mp
        q = Image.new(
            'RGBA', (nx + 2 * padX, ny + 2 * padY), (255, 255, 255, 255))
        q.paste(p, (padX, padY))
        return q, mp


class GoogleMap(object):
    def __init__(self, logFunc):
        self.logFunc = logFunc

    def getMap(self, latCen, lonCen, zoom, nx, ny, scale=1, satellite=True):
        url = 'http://maps.googleapis.com/maps/api/staticmap'
        params = dict(center="%.6f,%.6f" % (latCen, lonCen), zoom="%d" % zoom, size="%dx%d" % (nx, ny), scale="%d" % scale, sensor="false")
        if satellite:
            params["maptype"] = "satellite"
        if APIKEY is not None:
            params["key"] = APIKEY
        paramStr = urllib.urlencode(params)
        get_url = url + ("?%s" % paramStr)
        self.logFunc({"url": get_url})
        timeout = 15.0
        nAttempts = 10
        for i in range(nAttempts):
            try:
                socket.setdefaulttimeout(timeout)
                resp = urllib2.urlopen(get_url)
            except urllib2.URLError, e:
                print "Attempt: %d" % (i + 1,)
                if hasattr(e, 'reason'):
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                elif hasattr(e, 'code'):
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
                time.sleep(1.0)
            except:
                print "Attempt: %d" % (i + 1,)
                print traceback.format_exc()
                time.sleep(1.0)
            else:
                self.logFunc({"nRetries": i})
                return resp.read()
        self.logFunc({"nRetries": nAttempts})
        raise RuntimeError("Cannot fetch map after %d attempts" % (nAttempts,))

    def getPlatParams(self, minLng, maxLng, minLat, maxLat, satellite=True, padX=50, padY=50):
        return self.getPlat(minLng, maxLng, minLat, maxLat, satellite, padX, padY, fetchPlat=False)

    def getPlat(self, minLng, maxLng, minLat, maxLat, satellite=True, padX=50, padY=50, fetchPlat=True):
        meanLat = 0.5 * (minLat + maxLat)
        meanLng = 0.5 * (minLng + maxLng)
        Xp = maxLng - minLng
        Yp = maxLat - minLat
        # Find the largest zoom consistent with these limits
        cosLat = math.cos(meanLat * DTR)
        zoom = int(math.floor(math.log(min((360.0 * 640) / (
            256 * Xp), (360.0 * 640 * cosLat) / (256 * Yp))) / math.log(2.0)))
        # Find the number of pixels in each direction
        fac = (256.0 / 360.0) * 2 ** zoom
        mx = int(math.ceil(fac * Xp))
        my = int(math.ceil(fac * Yp / cosLat))
        scale = 2
        mp = MapParams(minLng, minLat, maxLng, maxLat, mx * scale,
                       my * scale, padX, padY)
        if fetchPlat:
            imageParams = dict(meanLat=meanLat, meanLng=meanLng, zoom=zoom, mx=mx, my=my,
                    scale=scale, satellite=satellite)
            return imageParams, mp
        else:
            return mp


class MapGrid(object):
    def __init__(self, minLng, minLat, maxLng, maxLat, nx, ny, padX, padY):
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

    def xform(self, lng, lat):
        """Get pixel corresponding to (lng,lat), where pixel (0,0) is
           (minLng,maxLat) and (nx,ny) is (maxLng,minLat)"""
        x = int(self.nx * (lng - self.minLng) / (self.maxLng - self.minLng))
        y = int(self.ny * (lat - self.maxLat) / (self.minLat - self.maxLat))
        return x, y

    def drawPartition(self, rectList):
        font = ImageFont.truetype("ariblk.ttf", 60)
        gridLayer = Image.new('RGBA', (
            self.nx + 2 * self.padX, self.ny + 2 * self.padY), (0, 0, 0, 0))
        gDraw = ImageDraw.Draw(gridLayer)
        for ky, row in enumerate(rectList):
            for kx, mr in enumerate(row):
                x1, y1 = self.xform(mr.swCorner.lng, mr.swCorner.lat)
                x2, y2 = self.xform(mr.neCorner.lng, mr.neCorner.lat)
                gDraw.rectangle(((self.padX + x1, self.padY + y1), (
                    self.padX + x2, self.padY + y2)), outline=(0, 0, 0, 255))
                xc, yc = (x1 + x2) / 2, (y1 + y2) / 2
                label = chr(ord('A') + ky) + "%d" % (kx + 1,)
                w, h = gDraw.textsize(label, font=font)
                gDraw.text((self.padX + xc - w / 2, self.padY + yc -
                           h / 2), label, font=font, fill=(0, 0, 255, 128))
        return gridLayer


class GoogleMarkers(object):
    def getMarker(self, size, fontsize, text, color):
        url = 'http://chart.apis.google.com/chart'
        params = dict(chst="d_map_spin", chld="%s|0|%s|%s|b|%s" % (
            size, color, fontsize, text))
        paramStr = urllib.urlencode(params)
        get_url = url + ("?%s" % paramStr)
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
    def __init__(self, minLng, minLat, maxLng, maxLat, nx, ny, padX, padY):
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
        deltaLat = RTD / EARTH_RADIUS
        deltaLng = RTD / (EARTH_RADIUS * math.cos(0.5 * (
            self.minLat + self.maxLat) * DTR))
        mppx = (self.maxLng - self.minLng) / (deltaLng * self.nx)
        mppy = (self.maxLat - self.minLat) / (deltaLat * self.ny)
        self.mpp = 0.5 * (mppx + mppy)
        # Calculate padded lat and lng limits for selection of P3 data
        minPadDist = 200.0   # Extend by at least this distance beyond the map edges
        px = max((maxLng - minLng) * padX / nx, minPadDist * deltaLng)
        py = max((maxLat - minLat) * padY / ny, minPadDist * deltaLat)
        self.padMinLng = minLng - px
        self.padMinLat = minLat - py
        self.padMaxLng = maxLng + px
        self.padMaxLat = maxLat + py
        self.setSwathParams()   # Set up defaults, which may be overridden

    def xform(self, lng, lat):
        """Get pixel corresponding to (lng,lat), where pixel (0,0) is
           (minLng,maxLat) and (nx,ny) is (maxLng,minLat)"""
        x = int(self.nx * (lng - self.minLng) / (self.maxLng - self.minLng))
        y = int(self.ny * (lat - self.maxLat) / (self.minLat - self.maxLat))
        return x, y

    def makeEmpty(self):
        return Image.new('RGBA', (self.nx + 2 * self.padX, self.ny + 2 * self.padY), (0, 0, 0, 0))

    def setSwathParams(self, minAmpl=0.05, minLeak=1.0, stabClass='D', nWindow=10, astdParams=dict(a=0.15 * math.pi, b=0.25, c=0.0)):
        self.minAmpl = minAmpl
        self.minLeak = minLeak
        self.stabClass = stabClass
        self.nWindow = nWindow
        self.astdParams = astdParams.copy()

    def astd(self, wind, vcar):
        a = self.astdParams["a"]
        b = self.astdParams["b"]
        c = self.astdParams["c"]
        return min(math.pi, a * (b + c * vcar) / (wind + 0.01))

    def drawSwath(self, source):
        lastLng, lastLat, lastDeltaLng, lastDeltaLat = None, None, None, None
        for etm, lng, lat, deltaLng, deltaLat in zip(source["EPOCH_TIME"], source["GPS_ABS_LONG"], source["GPS_ABS_LAT"], source["DELTA_LONG"], source["DELTA_LAT"]):
            if lastLng is not None:
                noLastView = abs(lastDeltaLng) < 1.0e-6 and abs(lastDeltaLat) < 1.0e-6
                if not noLastView:
                    noView = abs(deltaLng) < 1.0e-6 and abs(deltaLat) < 1.0e-6
                    if not noView:
                        x1, y1 = self.xform(lastLng + lastDeltaLng, lastLat + lastDeltaLat)
                        x2, y2 = self.xform(lastLng, lastLat)
                        x3, y3 = self.xform(lng, lat)
                        x4, y4 = self.xform(lng + deltaLng, lat + deltaLat)
                        if ((-self.padX <= x1 < self.nx + self.padX) and (-self.padY <= y1 < self.ny + self.padY)) or \
                           ((-self.padX <= x2 < self.nx + self.padX) and (-self.padY <= y2 < self.ny + self.padY)) or \
                           ((-self.padX <= x3 < self.nx + self.padX) and (-self.padY <= y3 < self.ny + self.padY)) or \
                           ((-self.padX <= x4 < self.nx + self.padX) and (-self.padY <= y4 < self.ny + self.padY)):
                            xmin = min(x1, x2, x3, x4)
                            xmax = max(x1, x2, x3, x4)
                            ymin = min(y1, y2, y3, y4)
                            ymax = max(y1, y2, y3, y4)
            lastLng, lastLat, lastDeltaLng, lastDeltaLat = lng, lat, deltaLng, deltaLat
        return extract_dictionary(source, ["EPOCH_TIME", "GPS_ABS_LONG", "GPS_ABS_LAT", "DELTA_LONG", "DELTA_LAT"])

    def makePathAndSwath(self, analyzer, startEtm, endEtm, makePath, makeSwath, reportFunc=None, timeout=None, saveData=False):
        """Use analyzer name, start and end epoch times to make a REST call to P3 to draw the path taken
        by the vehicle and the associated swath. Only points lying in the layer rectangle (within the padded region)
        are displayed. There may be many drive-arounds (represented by a distinct LOGNAMEs) associated with
        single run. Return a set of these, together with images of the path and swath. If saveData
        is True, the swath and path are storedso that they may be reused, e.g. for subMaps.
        """
        lognames = {}
        startTime = time.clock()
        colors = dict(normal=(0, 0, 255, 255), analyze=(0, 0, 0, 255), inactive=(255, 0, 0, 255))
        lastColor = [colors["normal"]]
        savedSwath = []
        savedPath = []

        def getColorFromValveMask(mask):
            # Determine color of path from valve mask
            color = lastColor[0]
            imask = int(round(mask, 0))
            if abs(mask - imask) <= 1e-4:
                if imask & 1:
                    color = colors["analyze"]
                elif imask & 16:
                    color = colors["inactive"]
                else:
                    color = colors["normal"]
                lastColor[0] = color
            return color

        def geohashPath(p):
            p["PATH"] = [geohash.encode(lat, lng) for lat, lng in zip(p["GPS_ABS_LAT"], p["GPS_ABS_LONG"])]
            del p["GPS_ABS_LAT"]
            del p["GPS_ABS_LONG"]
            return p

        def geohashSwath(s):
            s["PATH"] = [geohash.encode(lat, lng) for lat, lng in zip(s["GPS_ABS_LAT"], s["GPS_ABS_LONG"])]
            s["EDGE"] = [geohash.encode(lat + dlat, lng + dlng) for lat, lng, dlat, dlng in zip(s["GPS_ABS_LAT"], s["GPS_ABS_LONG"], s["DELTA_LAT"], s["DELTA_LONG"])]
            del s["GPS_ABS_LAT"]
            del s["GPS_ABS_LONG"]
            del s["DELTA_LAT"]
            del s["DELTA_LONG"]
            return s

        def colorPathFromInstrumentStatus(instStatus, color):
            if (instStatus & sis.INSTMGR_STATUS_MASK) != sis.INSTMGR_STATUS_GOOD:
                color = colors["inactive"]
                lastColor[0] = color
            return color
        lastRow = -1
        penDown = False
        path = []               # Path in (x,y) coordinates
        bufferedPath = []       # Path for calculation of swath
        pathLatLng = []         # Path in lats and lngs to save
        pathColor = colors["normal"]
        newPath = True
        p3 = gp3.P3_Accessor(analyzer)
        gen = p3.genAnzLog("dat")(startEtm=startEtm, endEtm=endEtm, minLng=self.padMinLng,
                   maxLng=self.padMaxLng, minLat=self.padMinLat, maxLat=self.padMaxLat)
        i = 0
        for i, m in enumerate(gen):
            lat = m.data["GPS_ABS_LAT"]
            lng = m.data["GPS_ABS_LONG"]
            fit = m.data.get("GPS_FIT", 1)
            mask = m.data.get("ValveMask", 0)
            row = m.data.get("row", 0)   # Used to detect contiguous points
            instStatus = m.data.get("INST_STATUS", 0)
            color = getColorFromValveMask(mask)
            color = colorPathFromInstrumentStatus(instStatus, color)
            isNormal = (color == colors["normal"])
            x, y = self.xform(lng, lat)
            # newPath = True means that there is to be a break in the path. A simple change
            #  of color gives a new path which joins onto the last
            # if fit>=1 and (-self.padX<=x<self.nx+self.padX) and (-self.padY<=y<self.ny+self.padY) and (row == lastRow+1):
            if fit >= 1 and (row == lastRow + 1):
                if newPath or color != pathColor:
                    if path:  # Draw out old path
                        if makePath:
                            if saveData:
                                p = geohashPath(lod2dol(pathLatLng))
                                savedPath.append((p, pathColor))
                        if makeSwath and pathColor == colors["normal"]:
                            result = process(bufferedPath, self.nWindow, self.stabClass,
                                             self.minLeak, self.minAmpl, self.astdParams)
                            s = geohashSwath(self.drawSwath(result))
                            if saveData:
                                savedSwath.append((s, makeSwath))
                        if newPath:
                            path = []
                            bufferedPath = []
                            pathLatLng = []
                        else:
                            path = [path[-1]]
                            bufferedPath = [bufferedPath[-1]]
                            pathLatLng = [pathLatLng[-1]]
                    pathColor = color
                path.append((self.padX + x, self.padY + y))
                logname = None
                if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY):
                    logname = m.data.get("LOGNAME", "")
                    if logname not in lognames:
                        lognames[logname] = len(lognames)
                bufferedPath.append(m.data)
                latlng = extract_dictionary(m.data, ["GPS_ABS_LAT", "GPS_ABS_LONG"])
                latlng["LOG"] = lognames[logname] if logname else None
                pathLatLng.append(latlng)
                newPath = False
            else:
                newPath = True
            lastRow = row
            if i % 100 == 0:
                if reportFunc:
                    reportFunc(i)
                if timeout and (time.clock() - startTime) > timeout:
                    raise RuntimeError(
                        "makePathAndSwath is taking too long to complete")
        if reportFunc:
            reportFunc(i)
        if path:
            if makePath:
                if saveData:
                    p = geohashPath(lod2dol(pathLatLng))
                    savedPath.append((p, pathColor))
            if makeSwath and pathColor == colors["normal"]:
                result = process(bufferedPath, self.nWindow, self.stabClass,
                                 self.minLeak, self.minAmpl, self.astdParams)
                s = geohashSwath(self.drawSwath(result))
                if saveData:
                    savedSwath.append((s, makeSwath))
        return lognames, savedPath, savedSwath

    def makeSubmapPath(self, savedData):
        """Determine lognames for the path(s) in a submap"""
        lognames = {}
        for sd in savedData:
            logs, savedPath, savedSwath = sd
            revlogs = {logs[logname]: logname for logname in logs}
            for pathLatLng, pathColor in savedPath:
                for data in dol2lod(pathLatLng):
                    log = data["LOG"]
                    if log is not None:
                        lat, lng = geohash.decode(data["PATH"])
                        x, y = self.xform(lng, lat)
                        if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY):
                            logname = revlogs[log]
                            if logname not in lognames:
                                lognames[logname] = log
        return lognames

    def geohashPeaks(self, p):
        p["LOCATION"] = [geohash.encode(lat, lng) for lat, lng in zip(p["GPS_ABS_LAT"], p["GPS_ABS_LONG"])]
        del p["GPS_ABS_LAT"]
        del p["GPS_ABS_LONG"]
        return p

    def geohashMarkers(self, p):
        p["LOCATION"] = [geohash.encode(lat, lng) for lat, lng in zip(p["lat"], p["lng"])]
        del p["lat"]
        del p["lng"]
        return p

    def makeMarkers(self, runParams, markers):
        """Write out peaks, wedges and additional markers on a map, using the runParams to
        select the appropriate data from the PeakFinder output"""

        peaksByAmpl = []
        peaks = []
        anyPeaks = False
        anyWedges = False
        # Find set of all peak and marker colors present in this region
        pColors = set()
        mColors = set()

        for r, (analyzer, startEtm, endEtm, minAmpl, maxAmpl, path, mType, mColor, makeWedges, exclRadius) in enumerate(runParams):
            # runParams specifies parameters for each region in turn, and r is the region number
            if not mColor:
                mType = MT_NONE
            anyPeaks = anyPeaks or (mType != MT_NONE)
            anyWedges = anyWedges or makeWedges

            p3 = gp3.P3_Accessor(analyzer)
            gen = p3.genAnzLog("peaks")(startEtm=startEtm, endEtm=endEtm, minLng=self.padMinLng,
                                        maxLng=self.padMaxLng, minLat=self.padMinLat, maxLat=self.padMaxLat)
            pList = [(m.data["AMPLITUDE"], m, r) for m in gen]
            if exclRadius > 0:
                result = []
                ilat, ilng, iampl = [], [], []
                # We need to remove peaks which are closer to each other than the exclusion radius, keeping
                #  only the largest in each group
                for amp, m, region in pList:
                    ilat.append(m.data["GPS_ABS_LAT"])
                    ilng.append(m.data["GPS_ABS_LONG"])
                    iampl.append(m.data["AMPLITUDE"])
                ilat = np.asarray(ilat)
                ilng = np.asarray(ilng)
                iampl = np.asarray(iampl)

                # Get median latitude and longitude for estimating distance scale
                medLat = np.median(ilat)
                medLng = np.median(ilng)
                mpdLat = DTR * EARTH_RADIUS  # Meters per degree of latitude
                mpdLng = mpdLat * np.cos(DTR * medLat)  # Meters per degree of longitude

                # Find points which are close to a given location
                # Find permutations that sort by longitude as primary key
                perm = np.argsort(ilng)
                elow = ehigh = 0
                dlng = exclRadius / mpdLng
                for i in perm:
                    while elow < len(perm) and ilng[perm[elow]] < ilng[i] - dlng:
                        elow += 1
                    while ehigh < len(perm) and ilng[perm[ehigh]] <= ilng[i] + dlng:
                        ehigh += 1
                    for e in range(elow, ehigh):
                        j = perm[e]
                        lng, lat, ampl = ilng[j], ilat[j], iampl[j]
                        assert ilng[i] - dlng <= lng < ilng[i] + dlng
                        dx = mpdLng * (lng - ilng[i])
                        dy = mpdLat * (lat - ilat[i])
                        if 0 < dx * dx + dy * dy <= exclRadius * exclRadius:
                            if iampl[i] < ampl:
                                break
                            elif iampl[i] == ampl and i < j:
                                break
                    else:
                        # This is the largest peak in the exclusion zone
                        result.append(i)
                peaks += [pList[i] for i in result]
            else:
                peaks += pList

        peaks.sort()
        # At this point we have the peaks from all runs in "peaks" sorted by rank
        if anyPeaks:
            # Count ranked markers
            nRanked = 0
            for amp, m, region in peaks:
                analyzer, startEtm, endEtm, minAmpl, maxAmpl, path, mType, mColor, makeWedges, exclRadius = runParams[region]
                if mType == MT_RANK:
                    lat = m.data["GPS_ABS_LAT"]
                    lng = m.data["GPS_ABS_LONG"]
                    if (self.minLng <= lng < self.maxLng) and (self.minLat <= lat < self.maxLat) and (amp > minAmpl) and ((maxAmpl is None) or (amp <= maxAmpl)):
                        nRanked += 1
            rank = nRanked
            #
            for amp, m, region in peaks:
                analyzer, startEtm, endEtm, minAmpl, maxAmpl, path, mType, mColor, makeWedges, exclRadius = runParams[region]
                if mColor:
                    pColors.add(mColor)
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                amp = m.data["AMPLITUDE"]
                ch4 = m.data["CH4"]
                vcar = getPossibleNaN(m.data, "CAR_SPEED", 0.0)
                windN = getPossibleNaN(m.data, "WIND_N", 0.0)
                windE = getPossibleNaN(m.data, "WIND_E", 0.0)
                dstd = DTR * getPossibleNaN(m.data, "WIND_DIR_SDEV", 0.0)
                x, y = self.xform(lng, lat)
                if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY) and \
                   (amp > minAmpl) and ((maxAmpl is None) or (amp <= maxAmpl)):
                    if mType in [MT_CONC, MT_RANK]:
                        m = extract_dictionary(m.data, ["ANALYZER", "EPOCH_TIME", "GPS_ABS_LAT", "GPS_ABS_LONG", "AMPLITUDE", "CH4"])
                        if mType == MT_CONC:
                            size = (self.ny / 1000.0) * amp ** 0.25    # Make these depend on number of pixels in the image
                            msg = "%.1f" % ch4
                        elif mType == MT_RANK:
                            if (self.minLng <= lng < self.maxLng) and (self.minLat <= lat < self.maxLat):
                                msg = "%d" % rank
                                rank -= 1
                            else:
                                msg = "*"
                        if np.isfinite(dstd):
                            radius = 50.0
                            wind = math.hypot(windE, windN)
                            meanBearing = RTD * math.atan2(windE, windN)
                            dstd = math.hypot(dstd, self.astd(wind, vcar))
                            windSdev = RTD * dstd
                            m["WIND_DIR_MEAN"] = meanBearing
                            m["WIND_DIR_SDEV"] = windSdev
                        m["TEXT"] = msg
                        m["PEAK_COLOR"] = mColor
                        m["WEDGE_COLOR"] = makeWedges
                        peaksByAmpl.append(m)
            peaksByAmpl.reverse()   # So these are  now in decreasing order of amplitude

        # Select the markers that lie within this region
        selMarkers = []
        for m in markers:
            if (self.minLng <= m["lng"] < self.maxLng) and (self.minLat <= m["lat"] < self.maxLat):
                selMarkers.append(m)
            if m["color"]:
                mColors.add(m["color"])
        return pColors, self.geohashPeaks(lod2dol(peaksByAmpl)), mColors, self.geohashMarkers(lod2dol(selMarkers))

    def makeSubmapMarkers(self, savedMarkers):
        """Draw peaks, wedges and additional markers on a submap, staring from the
        markers that were computed for the summary map"""
        pColors = set()
        mColors = set()
        _, peaks, _, markers = savedMarkers
        peaksByAmpl = []
        selMarkers = []
        for m in dol2lod(markers):
            lat, lng = geohash.decode(m["LOCATION"])
            x, y = self.xform(lng, lat)
            if (self.minLng <= lng < self.maxLng) and (self.minLat <= lat < self.maxLat):
                selMarkers.append(m)
            mColors.add(tuple(m["color"]))
        for data in dol2lod(peaks):
            lat, lng = geohash.decode(data["LOCATION"])
            x, y = self.xform(lng, lat)
            if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY):
                peaksByAmpl.append(data)
            pColors.add(tuple(data["PEAK_COLOR"]))
        return pColors, lod2dol(peaksByAmpl), mColors, lod2dol(selMarkers)
