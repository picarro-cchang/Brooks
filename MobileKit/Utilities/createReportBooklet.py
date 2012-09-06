#!/usr/bin/python
#
"""
File Name: createReportBooklet.py
Purpose: Picarro Surveyor(TM) report generation in booklet format
         Automatically assemble a full report into a PDF document
         Temporary solution to suffice during implementation on P3

File History:
    29-Aug-2012  D. Steele  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""


try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple

from bookletInstructions import *    
from FetchingGoogleMaps import *
from Host.Common.configobj import ConfigObj
import os
import shutil
import subprocess
import time
import traceback
import urllib
import urllib2
import batchReport2
import glob
import sys
from numpy import arange, arcsin, arctan2, asarray, cos, isfinite, isnan
from numpy import log, pi, sin, sqrt, unwrap


appPath = sys.executable
appDir = os.path.split(appPath)[0]

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
    
appDir = os.path.split(appPath)[0]


# Executable for HTML to PDF conversion
configFile = "..\\WeatherStation\\reportServer.ini"

# configFile = os.path.splitext(appPath)[0] + ".ini"
print "config: ", configFile
config = ConfigObj(configFile)
WKHTMLTOPDF = config["HelperApps"]["wkhtml_to_pdf"]
IMGCONVERT  = config["HelperApps"]["image_convert"]

def checkDirectory( dirName ):
    newDir = dirName
    dirExists = False
    if (os.path.isdir(dirName)):
        print "Directory", dirName, "already exists."
        userInput = raw_input( "   Do you wish to overwrite the contents of this directory? [y/n] ")
        if ( "y" in userInput ):
            print "   Overwriting directory", dirName
            dirExists = True
        else:
            newDir = raw_input("   Specify a new directory name: ")    
            newDir, dirExists = checkDirectory( newDir )
    return newDir, dirExists

def setupReportDirectories( areaName ):
    dirToTry = areaName
    topDir, topDirExists = checkDirectory( dirToTry )
    success = True
    print "Preparing subdirectories for the report on", areaName, "in directory", topDir
    if not topDirExists:
        os.mkdir(topDir)
    os.chdir(topDir)

    if ( os.path.isdir("maps") ):
        print "   Subdirectory \"maps\" already exists. Contents will be overwritten! "
        userInput = raw_input("   Do you wish to continue anyway? [y/n] ")
        if ("y" in userInput):
            print "   Will overwrite contents of \"maps\""
            os.remove("maps")
            os.mkdir("maps")
        else:
            success = False
    else:
        os.mkdir("maps")
           
    if ( os.path.isdir("instructions") ):
        print "   Subdirectory \"instructions\" already exists. Contents will be overwritten! "
        userInput = raw_input("   Do you wish to continue anyway? [y/n] ")
        if ("y" in userInput):
            print "   Will overwrite contents of \"instructions\""
        filesToDelete = glob.glob( "instructions\*" )
        for f in filesToDelete:
            os.remove(f)           
        else:
            success = False
    else:
        os.mkdir("instructions")
            
    return topDir, success
    
# Fetch, and save the grid key map to the current directory    
def makeGridKeyMap( gridPars, padX=50, padY=50 ):

    useSatellite = ( "sat" in gridPars.baseType )
    q, mp = GoogleMap().getPlat(    gridPars.mapRect.swCorner.lng,
                                    gridPars.mapRect.neCorner.lng,
                                    gridPars.mapRect.swCorner.lat,
                                    gridPars.mapRect.neCorner.lat,
                                    useSatellite, 
                                    padX,
                                    padY,
                                    fetchPlat=True
                                )
                                
    rectList = partition(gridPars.mapRect,gridPars.nrow,gridPars.ncol)
    pm = PartitionedMap(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
    q1 = pm.drawPartition(q,partition(gridPars.mapRect,gridPars.nrow,gridPars.ncol))
    op = file("mapKey.png","wb")
    op.write(asPNG(q1))
    op.close()
    
def runInstructions(baseName, fnExtensions):
    # Set up a subdirectory to hold the results of interest for each instructions file
    subDirBase = "result"
    for i in range( len(fnExtensions) ):
        subdir = subDirBase+str(i)
        os.mkdir(subdir)
    
    # Run each instructions file and copy results to appropriate subdir
    resultsToKeep = ['composite']
    
    for i in range( len(fnExtensions) ):
        batchReport2.process( baseName+fnExtensions[i] )
        for j in range( len(resultsToKeep) ):
            for data in glob.glob( resultsToKeep[j]+"*" ):
                shutil.move( data, subDirBase+str(i) )
   
def picHTML( picName, widthPCT ):
    picUrl = "file:%s" % urllib.pathname2url(os.path.abspath(picName))
    picUrl = picUrl.replace("|",":")
    pic = '<img src="%s" alt="" width="' % picUrl
    pic += str(widthPCT) 
    pic += '%%">' 
    return pic
   
def reportParamsToHTML(analyzer, minRunParList):
    #page = '<p>Report parameters:</p>\n'
    page = '<table border="0">'
    page += '<tr><td>Analyzer:</td><td>%s</td></tr>' % analyzer
    page += '<tr><td>Minimum Amplitude (ppm):</td><td>%s</td></tr>' % str(minRunParList[0].minAmpl)
    page += '<tr><td>Exclusion Radius (m):</td><td>%s</td></tr>' % str(minRunParList[0].exclRadius)    
    page += '</table>'
    page += '<br>'
    page += '<h3>Runs included:</h3>'
    for run in range( len(minRunParList) ):
        #page += '<h3>Run %s:</h3>' % str(run+1)
        page += '<table border="0">'
        page += '<tr><td>Start (GMT):</td><td>%s</td></tr>' % minRunParList[run].startEtm
        page += '<tr><td>End (GMT):</td><td>%s</td></tr>' % minRunParList[run].endEtm   
        page += '<tr><td>Stability Class:</td><td>%s</td></tr>' % minRunParList[run].stabClass        
        page += '</table>'
        page += '<br>' 
    return page

def getReportCoverPage( areaName, analyzer, minRunParamsList ):
    coverPage = "<h1>Picarro Surveyor&#0153; for Natural Gas Leaks</h1>\n"
    coverPage += "<h2>Report for %s</h2>" % areaName
    coverPage += reportParamsToHTML(analyzer, minRunParamsList)
    return coverPage

def getMapKeyPage( areaName ):
    page = "<h2 style=\"page-break-before:always;\">Map Key:</h2>"
    page += picHTML( "mapKey.png", 95 )
    return page

def getBookletPageHeader( areaName, minRunParsList ):
    return 'Area %(areaName)s &nbsp; Min Amplitude: %(minAmp)d &nbsp; Excl Radius: %(rad)d' % \
      { "areaName": areaName, "minAmp": minRunParsList[0].minAmpl, "rad": minRunParsList[0].exclRadius }
    
def getReportSummaryPages( dirList, areaName, minRunParamsList ):
    page = "" # "<h2 style=\"page-break-before:always;\">Summary Maps</h2>"
    for d in dirList:
        page += "<p style=\"page-break-before:always;\">%(a)s &emsp;&emsp; Min Ampl: %(b)s &emsp;&emsp; Excl Rad: %(c)s</p>" % \
            { "a": areaName, "b": str(minRunParamsList[0].minAmpl), "c": str(minRunParamsList[0].exclRadius) }
        os.chdir( d )
        picName = "composite.0.png"
        page += picHTML( picName, 95 )
        os.chdir( "..\\" )
    return page
 
# The images are numbered from zero starting with the lower left corner, increasing to the right and up. 
# Return a list that orders the images from the top left increasing to the right and down 
# The first page of row r where r is indexed from 0 is (ny-r-1)*nx
# Also return a list of alpha-numeric page numbers 
def getPageOrderAndNumbers( gridPars ):
    nx = gridPars.ncol
    ny = gridPars.nrow
    n = nx * ny
    pageOrder = []
    pageNumber = []
    pRow = chr( ord("A") + ny - 1 ) 
    for r in range(ny):
        for c in range(nx):
            pageOrder.append( (ny-r-1)*nx + c )
            pn = pRow + str(c+1)
            pageNumber.append( pn )
        pRow = chr( ord(pRow) - 1 )

    return pageOrder, pageNumber
 
def getReportPlatBooklet( dirList, gridPars, pageList, pageNumbers, areaName, minRunParamsList ):
    booklet = ""
    for page in pageList: 
        booklet += "<p style=\"page-break-before:always;\">%(a)s &emsp;&emsp; Min Ampl: %(b)s &emsp;&emsp; Excl Rad: %(c)s &emsp;&emsp; <b>Grid: %(d)s</b></p>" % \
            { "a": areaName, "b": str(minRunParamsList[0].minAmpl), "c": str(minRunParamsList[0].exclRadius), "d": pageNumbers[page] }
        for d in dirList:
            os.chdir(d)
            booklet += picHTML( "composite."+str(page)+".png", 95 )
            os.chdir("..\\")
    return booklet
       
def getAreaNameFromFile( fn ):
    config = ConfigObj(fn)
    areaName = config["ReportParams"]["area_name"]
    return areaName
    
def getAnalyzerNameFromFile( fn ):
    config = ConfigObj(fn)
    analyzerName = config["RunParams1"]["analyzer"]
    return analyzerName
       
def getGridParsFromFile( fn ):
    config = ConfigObj(fn)
    swCornerLat = float(config["ReportParams"]["sw_lattitude_deg"])
    swCornerLng = float(config["ReportParams"]["sw_longitude_deg"])
    swCorner = LatLng( swCornerLat, swCornerLng )
    neCornerLat = float(config["ReportParams"]["ne_lattitude_deg"])
    neCornerLng = float(config["ReportParams"]["ne_longitude_deg"])
    neCorner = LatLng( neCornerLat, neCornerLng )    
    map = MapRect( swCorner, neCorner )
    nCol = int(config["GridParams"]["n_columns"])
    nRow = int(config["GridParams"]["n_columns"])
    auto_grid = int(config["GridParams"]["auto_grid"])
    if (auto_grid > 0):
        minAspect = float(config["GridParams"]["min_aspect_ratio"])
        maxAspect = float(config["GridParams"]["max_aspect_ratio"])
        minDist = float(config["GridParams"]["min_diagonal_dist_meters"])
        maxDist = float(config["GridParams"]["max_diagonal_dist_meters"])
        isPortraitInt = int(config["GridParams"]["is_portrait"])
        isPortrait = False
        if (isPortraitInt > 0):
            isPortrait = True
        nCol, nRow = aspectAndDistToXYDivisors( mapRect, minAspect, maxAspect, minDist, maxDist, isPortrait )
    gridPars = GridParams( map, nCol, nRow, "", "" )
    return gridPars

def getMinRunParamsListFromFile( fn ):
    runParamsList = []
    config = ConfigObj(fn) 
    n_runs = int(config["ReportParams"]["n_runs"])
    run_key_list = []
    for i in range(n_runs):
        run_number = i+1
        run_key_list.append( "RunParams"+str(run_number) )
    for run in run_key_list:
        startDate = str( config[run]["run_start_date_gmt"] )
        startTime = str( config[run]["run_start_time_gmt"] )
        startEtm = startDate + " " + startTime
        endDate = str( config[run]["run_end_date_gmt"] )
        endTime = str( config[run]["run_end_time_gmt"] )
        endEtm = endDate + " " + endTime
        exclRad = config["ReportParams"]["exclusion_radius_meters"] 
        minAmpl = config["ReportParams"]["min_amplitude_ppm"]         
        stabClass = str( config[run]["stab_class"] )
        runParamsList.append( MinimalRunParams( startEtm, endEtm, minAmpl, exclRad, stabClass ) )   
    return runParamsList
    
if __name__ == "__main__":
    
    instruction_file_extentions = [ "_summary_map.json", "_summary_sat.json", "_summary_swath.json", "_grid_map.json", "_grid_sat.json" ]    
    
    print "\nPicarro Surveyor Report Booklet Generation -- Command Line Interface"
    print "Copyright (c) 2012 Picarro, Inc., All Rights Reserved.\n"

    makeMaps = True
    useFileInput = False
    
    topDir = os.getcwd()
    
    inpt = raw_input("   Input report parameters manually? (y/n): ")
    inptFile = ""
    if ("n" in inpt):
        useFileInput = True
        inptFileNameInpt = raw_input("   Name of report parameters file? ")
        inptFileName = topDir + "\\" + inptFileNameInpt
        print "Input file is ", inptFileName
        areaName = getAreaNameFromFile(inptFileName)
    else:
        areaName = raw_input("   Name of survey area? (example: CompanyArea1 no spaces, please): ")
 
    if makeMaps:
        topDir, ready = setupReportDirectories( areaName )
        if (useFileInput):
            analyzer = getAnalyzerNameFromFile(inptFileName)
            gridPars = getGridParsFromFile(inptFileName)
            minRunParamsList = getMinRunParamsListFromFile(inptFileName)
        else:
            analyzer = raw_input("   Name of analyzer? (example: FCDS2010) ")
            gridPars = getGridParametersFromCommandLine()
            #gridPars = getGridParametersFromCommandLine2()
            #gridPars = getGridParametersTest()
            minRunParamsList = getMinimalRunParametersListFromCommandLine()
            #minRunParamsList = getMinimalRunParametersTest()            
    else:
        print "Doing nothing for now"
        '''
        ready = True
        os.chdir("Example")
        analyzer = "FDDS2008"
        gridPars = getGridParametersTest()
        minRunParamsList = getMinimalRunParametersTest()
        '''

    if (ready):
        os.chdir("maps")
        keyGridParams = GridParams( gridPars.mapRect, gridPars.ncol, gridPars.nrow, areaName, "map") 
        makeGridKeyMap( keyGridParams )
        os.chdir("..\instructions")
        if makeMaps:
            writeReportInstructionsFiles(areaName, analyzer, gridPars, minRunParamsList)
            runInstructions(areaName, instruction_file_extentions)

        #Now assemble everything
        os.chdir("..\instructions")
        report = getReportCoverPage( areaName, analyzer, minRunParamsList )
        summaryDirList = [ "result0", "result1", "result2" ]
        report += getReportSummaryPages( summaryDirList, areaName, minRunParamsList )
        os.chdir("..\maps")
        report += getMapKeyPage( areaName )
        os.chdir("..\instructions")       
        zoomDirList = [ "result3", "result4" ]
        pageList, pageNumbers = getPageOrderAndNumbers( gridPars )
        #print pageNumbers
        #print pageList
        report += getReportPlatBooklet( zoomDirList, gridPars, pageList, pageNumbers, areaName, minRunParamsList )
        
        #Convert to PDF
        os.chdir("..\\")
        fn = "Report_" + areaName + ".pdf"
        proc = subprocess.Popen([WKHTMLTOPDF,"-",fn],
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        proc.communicate(report)     

        # Copy the Excel and PDF lists
        #src = "
        
    else:
        print "Report Generation Aborted"
