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
import cPickle
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
                mp = PlatFetcher().getPlatParams(self.name, self.minLng,
                                                 self.maxLng, self.minLat, self.maxLat)
                if mp is None:
                    mp = GoogleMap(self.logFunc).getPlatParams(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            else:
                raise ValueError("Base type %s not yet supported" % t)
            mpList.append(mp)
        return mpList

    def run(self):
        fnames = []
        for t in self.baseType:
            if t == "map":
                image, mp = GoogleMap(self.logFunc).getPlat(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            elif t == "satellite":
                image, mp = GoogleMap(self.logFunc).getPlat(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=True)
            elif t == "plat":
                image, mp = PlatFetcher().getPlat(self.name, self.minLng,
                                                  self.maxLng, self.minLat, self.maxLat)
                if mp is None:
                    image, mp = GoogleMap(self.logFunc).getPlat(self.minLng, self.maxLng, self.minLat, self.maxLat, satellite=False)
            else:
                raise ValueError("Base type %s not yet supported" % t)
            fname = os.path.join(self.reportDir, "%s/%s.%d.png" %
                                 (self.ticket, t, self.region))
            fnames.append(fname)
            with open(fname, "wb") as op:
                op.write(asPNG(image))
            if self.region == SUMMARY_REGION:
                nx = self.instructions["summary"]["nx"]
                ny = self.instructions["summary"]["ny"]
                mapRect = MapRect(LatLng(
                    mp.minLat, mp.minLng), LatLng(mp.maxLat, mp.maxLng))
                rectList = partition(mapRect, ny, nx)
                mg = MapGrid(mp.minLng, mp.minLat, mp.maxLng,
                             mp.maxLat, mp.nx, mp.ny, mp.padX, mp.padY)
                q1 = mg.drawPartition(rectList)
                fname = os.path.join(self.reportDir, "%s/%s.grid.%d.png" %
                                     (self.ticket, t, self.region))
                with open(fname, "wb") as op:
                    op.write(asPNG(q1))
                fnames.append(fname)
        self.logFunc({"fileNames": fnames})


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
        self.pathMapFname = os.path.join(
            self.reportDir, "%s/path.%d.png" % (self.ticket, self.region))
        self.swathMapFname = os.path.join(
            self.reportDir, "%s/swath.%d.png" % (self.ticket, self.region))
        if "summary" in instructions:
            self.pathDataFname = os.path.join(
                self.reportDir, "%s/pathData.dat" % (self.ticket,))
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
            with open(self.pathDataFname, "rb") as op:
                savedData = cPickle.load(op)
            pathMap, swathMap = sl.makeSubmapPath(savedData)
            pathMaps = [pathMap]
            swathMaps = [swathMap]
        else:
            if "runs" in self.instructions:
                pathMaps = []
                swathMaps = []
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
                        pMap, sMap, lognames, savedPath, savedSwath = \
                            sl.makePathAndSwath(analyzer, startEtm, endEtm, showPath,
                                                showSwath, report, self.timeout, saveData)
                        savedData.append((savedPath, savedSwath))
                        for n in lognames:
                            if n in self.paramsByLogname:
                                raise ValueError(
                                    "Log %s appears in more than one run" % n)
                            self.paramsByLogname[n] = dict(params).copy()
                        if showPath:
                            pathMaps.append(pMap)
                        if showSwath:
                            swathMaps.append(sMap)
        # Now merge the paths on the run maps together to form the composite path
        if pathMaps:
            image = sl.makeEmpty()
            for m in pathMaps:
                image = overBackground(m, image, None)
            image = backgroundToOverlay(image)
            with open(self.pathMapFname, "wb") as op:
                op.write(asPNG(image))
        if swathMaps:
            image = sl.makeEmpty()
            for m in swathMaps:
                image = overBackground(m, image, None)
            image = backgroundToOverlay(image)
            with open(self.swathMapFname, "wb") as op:
                op.write(asPNG(image))
        with open(self.pathHtmlFname, "wb") as op:
            self.makePathReport(op)
        if saveData:
            with open(self.pathDataFname, "wb") as op:
                cPickle.dump(savedData, op, -1)

MT_NONE, MT_CONC, MT_RANK = 0, 1, 2


class ReportMarkerMap(object):
    def __init__(self, reportDir, ticket, instructions, mapParams, region, logFunc):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.peaksHtmlFname = os.path.join(
            self.reportDir, "%s/peaks.%d.html" % (self.ticket, self.region))
        self.markerHtmlFname = os.path.join(
            self.reportDir, "%s/markers.%d.html" % (self.ticket, self.region))
        self.peaksXmlFname = os.path.join(
            self.reportDir, "%s/peaks.%d.xml" % (self.ticket, self.region))
        self.peaksMapFname = os.path.join(
            self.reportDir, "%s/peaks.%d.png" % (self.ticket, self.region))
        self.wedgesMapFname = os.path.join(
            self.reportDir, "%s/wedges.%d.png" % (self.ticket, self.region))
        if "summary" in instructions:
            self.markerDataFname = os.path.join(
                self.reportDir, "%s/markerData.dat" % (self.ticket,))
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
        for msg, data, pkColor, wedgeColor in peaks:
            if self.digits.match(msg):
                tstr = time.strftime("%Y%m%dT%H%M%S", time.gmtime(data['EPOCH_TIME']))
                anz = data['ANALYZER']
                lat = data['GPS_ABS_LAT']
                lng = data['GPS_ABS_LONG']
                ch4 = data['CH4']
                ampl = data['AMPLITUDE']
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
        for m, (x, y) in selMarkers:
            coords = "%s,%s" % (m.lat, m.lng)
            markerTableString.append('<tr>')
            markerTableString.append('<td><a href="http://maps.google.com?q=%s+(%s)&z=%d" target="_blank">%s</a></td>' % (coords, m.label, zoom, m.label))
            markerTableString.append('<td>%s</td>' % m.lat)
            markerTableString.append('<td>%s</td>' % m.lng)
            markerTableString.append('</tr>')
        markerTableString.append('</tbody>')
        markerTableString.append('</table>')
        op.write("\n".join(markerTableString))

    def makePeakCsv(self, op, peaks, selMarkers):
        zoom = 18
        writer = csv.writer(op, dialect='excel')
        writer.writerow(('Rank', 'Designation', 'Latitude',
                        'Longitude', 'Concentration', 'Amplitude', 'URL'))
        for msg, data, pkColor, wedgeColor in peaks:
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
        for msg, data, pkColor, wedgeColor in peaks:
            if self.digits.match(msg):
                tstr = time.strftime("%Y%m%dT%H%M%S", time.gmtime(data['EPOCH_TIME']))
                anz = data['ANALYZER']
                lat = data['GPS_ABS_LAT']
                lng = data['GPS_ABS_LONG']
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
        MarkerParams = namedtuple(
            'MarkerParams', ['label', 'color', 'lat', 'lng'])
        if "markers" in self.instructions:
            for m in self.instructions["markers"]:
                lat, lng = m.get("location", (0.0, 0.0))
                mp = MarkerParams(m.get("label", "*"),
                                  colorStringToRGB(m.get("color", "#FFFFFF")),
                                  lat,
                                  lng)
                markers.append(mp)
        # We either have to treat each regional map on its own, and generate markers
        #  for that region in its own right, or alternatively, if it is part of a set
        #  of submaps with a summary map, the markers and wedges are inherited from those
        #  calculated for the summary map
        if "summary" in self.instructions and self.region != SUMMARY_REGION:
            with open(self.markerDataFname, "rb") as op:
                savedMarkers = cPickle.load(op)
            im1, im2, peaks, selMarkers = sl.makeSubmapMarkers(savedMarkers)
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
            im1, im2, peaks, selMarkers = sl.makeMarkers(runParams, markers)
            # Write out the peak and marker information from the summary region
            if self.region == SUMMARY_REGION:
                with open(self.markerDataFname, "wb") as op:
                    cPickle.dump((peaks, selMarkers), op, -1)

        # Now write out the maps
        if im1 is not None:
            im1 = backgroundToOverlay(im1)
            with open(self.peaksMapFname, "wb") as op:
                op.write(asPNG(im1))
        if im2 is not None:
            im2 = backgroundToOverlay(im2)
            with open(self.wedgesMapFname, "wb") as op:
                op.write(asPNG(im2))
        with open(self.peaksHtmlFname, "wb") as op:
            self.makePeakReport(op, peaks)
        with open(self.markerHtmlFname, "wb") as op:
            self.makeMarkerReport(op, selMarkers)
        with open(self.peaksXmlFname, "wb") as op:
            self.makePeakXml(op, peaks, selMarkers)


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
            p = Image.open(cStringIO.StringIO(self.getMap(
                meanLat, meanLng, zoom, mx, my, scale, satellite)))
            q = Image.new('RGBA', (scale * mx + 2 * padX,
                          scale * my + 2 * padY), (255, 255, 255, 255))
            q.paste(p, (padX, padY))
            return q, mp
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

    def drawSwath(self, source, sv, makeSwath):
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
                            temp = Image.new('RGBA', (xmax - xmin + 1, ymax - ymin + 1), (0, 0, 0, 0))
                            tdraw = ImageDraw.Draw(temp)
                            tdraw.polygon(
                                [(x1 - xmin, y1 - ymin), (x2 - xmin, y2 - ymin), (x3 - xmin, y3 - ymin), (x4 - xmin, y4 - ymin)],
                                fill=makeSwath + (128,), outline=makeSwath + (200,))
                            mask = (self.padX + xmin, self.padY + ymin)
                            sv = overBackground(temp, sv, mask)

            lastLng, lastLat, lastDeltaLng, lastDeltaLat = lng, lat, deltaLng, deltaLat
        return extract_dictionary(source, ["EPOCH_TIME", "GPS_ABS_LONG", "GPS_ABS_LAT", "DELTA_LONG", "DELTA_LAT"])

    def makePathAndSwath(self, analyzer, startEtm, endEtm, makePath, makeSwath, reportFunc=None, timeout=None, saveData=False):
        """Use analyzer name, start and end epoch times to make a REST call to P3 to draw the path taken
        by the vehicle and the associated swath. Only points lying in the layer rectangle (within the padded region)
        are displayed. There may be many drive-arounds (represented by a distinct LOGNAMEs) associated with
        single run. Return a set of these, together with images of the path and swath. If saveData
        is True, the swath and path are storedso that they may be reused, e.g. for subMaps.
        """
        lognames = set()
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

        def colorPathFromInstrumentStatus(instStatus, color):
            if (instStatus & sis.INSTMGR_STATUS_MASK) != sis.INSTMGR_STATUS_GOOD:
                color = colors["inactive"]
                lastColor[0] = color
            return color
        ov, sv = None, None
        if makePath:
            ov = Image.new('RGBA', (self.nx + 2 * self.padX,
                           self.ny + 2 * self.padY), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(ov)
        if makeSwath:
            sv = Image.new('RGBA', (self.nx + 2 * self.padX,
                           self.ny + 2 * self.padY), (0, 0, 0, 0))
            sdraw = ImageDraw.Draw(sv)
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
                            odraw.line(path, fill=pathColor, width=2)
                            if saveData:
                                savedPath.append((pathLatLng, pathColor))
                        if makeSwath and pathColor == colors["normal"]:
                            result = process(bufferedPath, self.nWindow, self.stabClass,
                                             self.minLeak, self.minAmpl, self.astdParams)
                            s = self.drawSwath(result, sv, makeSwath)
                            if saveData:
                                savedSwath.append((s, makeSwath))
                        if newPath:
                            path = []
                            bufferedPath = []
                            pathLatLng = []
                        else:
                            path = [path[-1]]
                            bufferedPath = [bufferedPath[-1]]
                            pathLatLng = []
                    pathColor = color
                path.append((self.padX + x, self.padY + y))
                if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY):
                    lognames.add(m.data.get("LOGNAME", ""))
                bufferedPath.append(m.data)
                pathLatLng.append(extract_dictionary(m.data,["GPS_ABS_LAT", "GPS_ABS_LONG"]))
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
                odraw.line(path, fill=pathColor, width=2)
                if saveData:
                    savedPath.append((pathLatLng, pathColor))
            if makeSwath and pathColor == colors["normal"]:
                result = process(bufferedPath, self.nWindow, self.stabClass,
                                 self.minLeak, self.minAmpl, self.astdParams)
                s = self.drawSwath(result, sv, makeSwath)
                if saveData:
                    savedSwath.append((s, makeSwath))
        return ov, sv, lognames, savedPath, savedSwath

    def makeSubmapPath(self, savedData):
        """Draw path and swath on a submap, staring from the path and swath that were
        computed for the summary map"""
        ov = Image.new('RGBA', (self.nx + 2 * self.padX,
                       self.ny + 2 * self.padY), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(ov)
        sv = Image.new('RGBA', (self.nx + 2 * self.padX,
                       self.ny + 2 * self.padY), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sv)
        for sd in savedData:
            savedPath, savedSwath = sd
            for pathLatLng, pathColor in savedPath:
                path = []
                for data in pathLatLng:
                    lat = data["GPS_ABS_LAT"]
                    lng = data["GPS_ABS_LONG"]
                    x, y = self.xform(lng, lat)
                    if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY):
                        path.append((self.padX + x, self.padY + y))
                    else:
                        if path:
                            odraw.line(path, fill=pathColor, width=2)
                        path = []
                if path:
                    odraw.line(path, fill=pathColor, width=2)
            for s, makeSwath in savedSwath:
                self.drawSwath(s, sv, makeSwath)
        return ov, sv

    def makeMarkers(self, runParams, markers):
        """Draw peaks, wedges and additional markers on a map, using the runParams to
        select the appropriate data from the PeakFinder output"""
        peaksByAmpl = []
        peaks = []
        anyPeaks = False
        anyWedges = False

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

        ov1, ov2 = None, None
        # Select the markers that lie within this region
        selMarkers = []
        for m in markers:
            x, y = self.xform(m.lng, m.lat)
            if (self.minLng <= m.lng < self.maxLng) and (self.minLat <= m.lat < self.maxLat):
                selMarkers.append((m, (x, y)))
        peaks.sort()
        # At this point we have the peaks from all runs in "peaks" sorted by rank
        if anyPeaks or selMarkers:
            ov1 = Image.new('RGBA', (self.nx + 2 * self.padX,
                            self.ny + 2 * self.padY), (0, 0, 0, 0))
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
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                amp = m.data["AMPLITUDE"]
                ch4 = m.data["CH4"]
                x, y = self.xform(lng, lat)
                if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY) and \
                   (amp > minAmpl) and ((maxAmpl is None) or (amp <= maxAmpl)):
                    if mType in [MT_CONC, MT_RANK]:
                        m = extract_dictionary(m.data, ["ANALYZER", "EPOCH_TIME", "GPS_ABS_LAT", "GPS_ABS_LONG", "AMPLITUDE", "CH4", "CAR_SPEED", "WIND_N", "WIND_E", "WIND_DIR_SDEV"])
                        if mType == MT_CONC:
                            size = (self.ny / 1000.0) * amp ** 0.25    # Make these depend on number of pixels in the image
                            msg = "%.1f" % ch4
                        elif mType == MT_RANK:
                            size = (self.ny / 1000.0)
                            if (self.minLng <= lng < self.maxLng) and (self.minLat <= lat < self.maxLat):
                                msg = "%d" % rank
                                rank -= 1
                            else:
                                msg = "*"
                        if len(msg) <= 2:
                            fontsize = min(100, int(20.0 * size))
                        else:
                            fontsize = min(100, int(14.0 * size))
                        peaksByAmpl.append((msg, m, mColor, makeWedges))
                        color = "%02x%02x%02x" % tuple(mColor)
                        buff = cStringIO.StringIO(GoogleMarkers().getMarker(size, fontsize, msg, color))
                        b = Image.open(buff)
                        bx, by = b.size
                        box = (self.padX + x - bx // 2, self.padY + y - by)
                        ov1 = overBackground(b, ov1, box)
            peaksByAmpl.reverse()   # So these are  now in decreasing order of amplitude

            for m, (x, y) in selMarkers:
                size = (self.ny / 1000.0)
                if len(m.label) <= 2:
                    fontsize = min(100, int(20.0 * size))
                else:
                    fontsize = min(100, int(14.0 * size))
                color = "%02x%02x%02x" % tuple(m.color)
                buff = cStringIO.StringIO(
                    GoogleMarkers().getMarker(size, fontsize, m.label, color))
                b = Image.open(buff)
                bx, by = b.size
                box = (self.padX + x - bx // 2, self.padY + y - by)
                ov1 = overBackground(b, ov1, box)

        if anyWedges:
            ov2 = Image.new('RGBA', (self.nx + 2 * self.padX,
                            self.ny + 2 * self.padY), (0, 0, 0, 0))
            odraw2 = ImageDraw.Draw(ov2)
            for amp, m, region in peaks:
                analyzer, startEtm, endEtm, minAmpl, maxAmpl, path, mType, mColor, makeWedges, exclRadius = runParams[region]
                if not makeWedges:
                    continue
                lat = m.data["GPS_ABS_LAT"]
                lng = m.data["GPS_ABS_LONG"]
                vcar = getPossibleNaN(m.data, "CAR_SPEED", 0.0)
                windN = getPossibleNaN(m.data, "WIND_N", 0.0)
                windE = getPossibleNaN(m.data, "WIND_E", 0.0)
                dstd = DTR * getPossibleNaN(m.data, "WIND_DIR_SDEV", 0.0)
                x, y = self.xform(lng, lat)
                if np.isfinite(dstd) and (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY) and \
                   (amp > minAmpl) and ((maxAmpl is None) or (amp <= maxAmpl)):
                    wind = math.hypot(windN, windE)
                    radius = 50.0
                    speedmin = 0.5
                    meanBearing = RTD * math.atan2(windE, windN)
                    dstd = math.hypot(dstd, self.astd(wind, vcar))
                    windSdev = RTD * dstd
                    # Check for NaN
                    if wind == wind and meanBearing == meanBearing:
                        minBearing = meanBearing - min(2 * windSdev, 180.0)
                        maxBearing = meanBearing + min(2 * windSdev, 180.0)
                    else:
                        minBearing = 0
                        maxBearing = 360.0
                    radius = int(radius / self.mpp)
                    b = Image.new('RGBA', (
                        2 * radius + 1, 2 * radius + 1), (0, 0, 0, 0))
                    bdraw = ImageDraw.Draw(b)
                    bdraw.pieslice(
                        (0, 0, 2 * radius, 2 * radius), int(minBearing - 90.0), int(maxBearing - 90.0), fill=makeWedges + (128,),
                                   outline=(0, 0, 0, 255))
                    ov2 = overBackground(b, ov2, (
                        self.padX + x - radius, self.padY + y - radius))

        return ov1, ov2, peaksByAmpl, selMarkers

    def makeSubmapMarkers(self, savedMarkers):
        """Draw peaks, wedges and additional markers on a submap, staring from the
        markers that were computed for the summary map"""
        peaks, markers = savedMarkers

        peaksByAmpl = []
        selMarkers = []
        for m in markers:
            x, y = self.xform(m.lng, m.lat)
            if (self.minLng <= m.lng < self.maxLng) and (self.minLat <= m.lat < self.maxLat):
                selMarkers.append((m, (x, y)))

        if peaks or selMarkers:
            ov1 = Image.new('RGBA', (self.nx + 2 * self.padX,
                                     self.ny + 2 * self.padY), (0, 0, 0, 0))
            ov2 = Image.new('RGBA', (self.nx + 2 * self.padX,
                                     self.ny + 2 * self.padY), (0, 0, 0, 0))
            for msg, data, pkColor, wedgeColor in peaks:
                lat = data["GPS_ABS_LAT"]
                lng = data["GPS_ABS_LONG"]
                x, y = self.xform(lng, lat)
                if (-self.padX <= x < self.nx + self.padX) and (-self.padY <= y < self.ny + self.padY):
                    if "." in msg:  # This is a concentration
                        amp = data["AMPLITUDE"]
                        size = (self.ny / 1000.0) * amp ** 0.25
                    else:
                        size = (self.ny / 1000.0)
                    if len(msg) <= 2:
                        fontsize = min(100, int(20.0 * size))
                    else:
                        fontsize = min(100, int(14.0 * size))
                    peaksByAmpl.append((msg, data, pkColor, wedgeColor))
                    color = "%02x%02x%02x" % tuple(pkColor)
                    buff = cStringIO.StringIO(GoogleMarkers().getMarker(size, fontsize, msg, color))
                    b = Image.open(buff)
                    bx, by = b.size
                    box = (self.padX + x - bx // 2, self.padY + y - by)
                    ov1 = overBackground(b, ov1, box)
                    if wedgeColor:
                        vcar = getPossibleNaN(data, "CAR_SPEED", 0.0)
                        windN = getPossibleNaN(data, "WIND_N", 0.0)
                        windE = getPossibleNaN(data, "WIND_E", 0.0)
                        dstd = DTR * getPossibleNaN(data, "WIND_DIR_SDEV", 0.0)
                        if np.isfinite(dstd):
                            wind = math.hypot(windN, windE)
                            radius = 50.0
                            speedmin = 0.5
                            meanBearing = RTD * math.atan2(windE, windN)
                            dstd = math.hypot(dstd, self.astd(wind, vcar))
                            windSdev = RTD * dstd
                            # Check for NaN
                            if wind == wind and meanBearing == meanBearing:
                                minBearing = meanBearing - min(2 * windSdev, 180.0)
                                maxBearing = meanBearing + min(2 * windSdev, 180.0)
                            else:
                                minBearing = 0
                                maxBearing = 360.0
                            radius = int(radius / self.mpp)
                            b = Image.new('RGBA', (
                                2 * radius + 1, 2 * radius + 1), (0, 0, 0, 0))
                            bdraw = ImageDraw.Draw(b)
                            bdraw.pieslice(
                                (0, 0, 2 * radius, 2 * radius), int(minBearing - 90.0), int(maxBearing - 90.0), fill=wedgeColor + (128,),
                                           outline=(0, 0, 0, 255))
                            ov2 = overBackground(b, ov2, (
                                self.padX + x - radius, self.padY + y - radius))

            for m, (x, y) in selMarkers:
                size = (self.ny / 1000.0)
                if len(m.label) <= 2:
                    fontsize = min(100, int(20.0 * size))
                else:
                    fontsize = min(100, int(14.0 * size))
                color = "%02x%02x%02x" % tuple(m.color)
                buff = cStringIO.StringIO(
                    GoogleMarkers().getMarker(size, fontsize, m.label, color))
                b = Image.open(buff)
                bx, by = b.size
                box = (self.padX + x - bx // 2, self.padY + y - by)
                ov1 = overBackground(b, ov1, box)

        return ov1, ov2, peaksByAmpl, selMarkers


class BubbleMaker(object):
    def getMarker1(self, size):
        def nint(x):
            return int(round(x))
        nx = nint(36 * size + 1)
        ny = nint(65 * size + 1)
        xoff = (nx - 1) / 2
        h = ny - 1
        r = (nx - 1) / 2.0
        R = h * (0.5 * h / r - 1.0)
        phi = np.arcsin(R / (R + r))
        b = Image.new('RGBA', (nx, ny), (255, 255, 255, 255))
        bdraw = ImageDraw.Draw(b)
        n1 = 10
        n2 = 20
        arc1 = [(nint(xoff - R + R * np.cos(th)), nint(ny - 1 - R * np.sin(th))) for th in np.linspace(0.0, 0.5 * np.pi - phi, n1, endpoint=False)]
        arc2 = [(nint(xoff - r * np.sin(th)), nint(r + r * np.cos(th))) for th in np.linspace(phi, 2 * np.pi - phi, n2, endpoint=False)]
        arc3 = [(nint(xoff + R - R * np.cos(th)), nint(ny - 1 - R * np.sin(th))) for th in np.linspace(0.5 * np.pi - phi, 0.0, n1, endpoint=False)]
        bdraw.polygon(arc1 + arc2 + arc3, fill=(255, 255, 0, 255),
                      outline=(0, 0, 0, 255))
        bdraw.line(arc1 + arc2 + arc3, fill=(0, 0, 0, 255), width=3)
        return asPNG(b)

    def getMarker(self, size):
        def nint(x):
            return int(round(x))
        t = 2
        r = 18 * size - t
        h = 65 * size - 2 * t
        nx = nint(36 * size + 1)
        ny = nint(65 * size + 1)
        w = size
        R = ((h - r) * (h - r) - (r * r - 0.25 * w * w)) / float(2 * r - w)
        phi = np.arcsin((R + 0.5 * w) / (R + r))
        cen1 = (-(R + 0.5 * w), h - r)
        cen2 = (0, 0)
        cen3 = ((R + 0.5 * w), h - r)
        xoff = r + t
        yoff = r + t
        b = Image.new('RGBA', (nx, ny), (255, 255, 255, 255))
        bdraw = ImageDraw.Draw(b)
        n1 = 20
        n2 = 40
        arc1 = [(xoff + nint(cen1[0] + R * np.cos(th)), nint(yoff + cen1[1] - R * np.sin(th))) for th in np.linspace(0.0, 0.5 * np.pi - phi, n1, endpoint=False)]
        arc2 = [(xoff + nint(cen2[0] - r * np.sin(th)), nint(yoff + cen2[1] + r * np.cos(th))) for th in np.linspace(phi, 2 * np.pi - phi, n2, endpoint=False)]
        arc3 = [(xoff + nint(cen3[0] - R * np.cos(th)), nint(yoff + cen3[1] - R * np.sin(th))) for th in np.linspace(0.5 * np.pi - phi, 0.0, n1, endpoint=True)]
        bdraw.polygon(arc1 + arc2 + arc3, fill=(255, 255, 0, 255),
                      outline=(0, 0, 0, 255))
        bdraw.line(
            arc1 + arc2 + arc3 + arc1[0:1], fill=(0, 0, 0, 255), width=t)
        return asPNG(b)
