#!/usr/bin/python
#
"""
File Name: createReportBooklet.py
Purpose: Picarro Surveyor(TM) report generation in booklet format
         Automatically assemble a full report into a PDF document
         Temporary solution to suffice during implementation on P3

File History:
    29-Aug-2012  D. Steele  Initial version.
    04-Oct-2012  D. Steele  Added getKMLParamsFromFile
    10-Oct-2012  D. Steele  Added ReportBookletConfig class. Fixed error when trying to overwrite existing directories
    26-Nov-2012  D. Steele  Completed upgrades: Map display is now completely configurable. 
                            Also, all code needed to run is in this file, except FetchingGoogleMaps
    
    Outstanding Issues/TODO List:
       --When "*" is selected for the weather, show the actual stab class in the report rather than *
       --Command line instructions
         --Reimplement
         --Handle lower case stab class properly
         --Print ini file based on command-line instructions
       --Make sure the case of no KML is handled properly
       --Auto-grid
       --Run mode options: grid key only, assemble only, etc . . .
    
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""


try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple
try:
    import json
except:
    import simplejson as json
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
import numpy as np
from numpy import arange, arcsin, arctan2, asarray, cos, isfinite, isnan
from numpy import log, pi, sin, sqrt, unwrap

LatLng = namedtuple( 'LatLng', ["lat", "lng"] )
MapRect = namedtuple( 'MapRect', ["swCorner", "neCorner"] )

RunBlockParams = namedtuple('RunParams',['analyzer','startEtm','endEtm','showPath','markerColor','wedgeColor','swathColor','minAmpl','exclRadius','stabClass','comments'])
MinimalRunParams = namedtuple( 'MinimalRunParams', [ 'analyzer','startEtm','endEtm','stabClass' ])    

RegionParams = namedtuple( 'RegionParams', ['baseType', 'name', 'swCorner', 'neCorner', 'comments'] )
GridParams = namedtuple( 'GridParams', ['mapRect', 'ncol', 'nrow', 'baseName', 'baseType'] )

MapDisplayConfig = namedtuple( 'MapConfig', ['baseType', 'bubbleColor', 'wedgeColor', 'swathColor', 'overlayKml', 'overlayUserMarkers', 'showTrail'] )
AssetDisplayConfig = namedtuple( 'AssetConfig', ['fileName', 'lineWidth', 'lineColor', 'filter' ] )

MarkerInfo = namedtuple( 'MarkerInfo', [ 'name', 'lat', 'lng', 'color' ] )

# Executable for HTML to PDF conversion
# configFile = "..\\WeatherStation\\reportServer.ini"
configFile = "reportServer.ini"

# configFile = os.path.splitext(appPath)[0] + ".ini"
config = ConfigObj(configFile)
WKHTMLTOPDF = config["HelperApps"]["wkhtml_to_pdf"]
IMGCONVERT  = config["HelperApps"]["image_convert"]

class ReportApiService(object):
    def __init__(self, *args, **kwargs):
        self.sockettimeout = 10
        self.csp_url = None    
        if 'csp_url' in kwargs: self.csp_url = kwargs['csp_url']
        self.sleep_seconds = None
        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds']:
                self.sleep_seconds = float(kwargs['sleep_seconds'])
        if self.sleep_seconds == None: self.sleep_seconds = 1.0
        self.ticket = 'None'
        
    def getTicket(self):
        print "Not implemented"
        
    def get(self, svc, ver, rsc, qryparms_obj):
        info = {}
        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            rtn_data = None
            rslt = None
            err_str = None
            try:
                assert 'qry' in qryparms_obj
                qry = qryparms_obj['qry']
                del qryparms_obj['qry']
                data = urllib.urlencode(qryparms_obj)
                qry_url = '%s/rest/%s?%s' % (self.csp_url,qry,data)
                if self.debug == True: print "qry_url: %s" %(qry_url)
                socket.setdefaulttimeout(self.sockettimeout)
                resp = urllib2.urlopen(qry_url, )
                info = resp.info()
                rtn_data = resp.read()
                
            except urllib2.HTTPError, e:
                err_str = e.read()
                if "invalid ticket" in err_str:
                    if self.debug == True:
                        print "We Have an invalid or expired ticket"
                    self.getTicket()
                    waitForRetryCtr += 1
                    if waitForRetryCtr < 100:
                        waitForRetry = None
                else:
                    if self.debug == True:
                        print 'EXCEPTION in ReportApiService - get.\n%s\n' % err_str
                    break
                
            except Exception, e:
                if self.debug:
                    print 'EXCEPTION in ReportApiService - get failed \n%s\n' % e
                
                time.sleep(self.sleep_seconds)
                continue
           
            if (rtn_data):
                if 'json' in info['content-type']:
                    rslt = json.loads(rtn_data)
                    if self.debug == True:
                        print "rslt: ", rslt
                else:
                    print "rslt of type: ", info['content-type']
                    rslt = rtn_data
                break
                
            if waitForRetry: time.sleep(self.timeout)
            waitForRetry = True
            
        return { "error": err_str, "return": rslt, "info": dict(info.items()) }

class GridConfiguration(object):
    '''Automatically choose the number of rows and colums for a report booklet
    based on user-defined constraints
    
       This class is in development and is not yet used
    '''
    def __init__(self):
        self.nColumns = 1
        self.nRows = 1
    
        self.maxGroundDistanceMeters = 200 
        self.idealAspectRatio = 0.9
        self.minAspectRatio = 1.0
        self.maxAspectRatio = 0.7
        
    def distVincenty2(self,mapRect):
        # WGS-84 ellipsiod. lat and lng in DEGREES
        a = 6378137
        b = 6356752.3142
        f = 1/298.257223563;
        toRad = pi/180.0
        L = (mapRect.neCorner.lng-mapRect.swCorner.lng)*toRad
        U1 = arctan((1-f) * tan(mapRect.swCorner.lat*toRad))
        U2 = arctan((1-f) * tan(mapRect.neCorner.lat*toRad));
        sinU1 = sin(U1)
        cosU1 = cos(U1)
        sinU2 = sin(U2)
        cosU2 = cos(U2)
      
        Lambda = L
        iterLimit = 100;
        for iter in range(iterLimit):
            sinLambda = sin(Lambda)
            cosLambda = cos(Lambda)
            sinSigma = sqrt((cosU2*sinLambda) * (cosU2*sinLambda) + 
                            (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
            if sinSigma==0: 
                return 0  # co-incident points
            cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
            sigma = arctan2(sinSigma, cosSigma)
            sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
            cosSqAlpha = 1 - sinAlpha*sinAlpha
            if cosSqAlpha == 0:
                cos2SigmaM = 0
            else:
                cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
            C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
            lambdaP = Lambda;
            Lambda = L + (1-C) * f * sinAlpha * \
              (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))
            if abs(Lambda-lambdaP)<=1.e-12: break
        else:
            raise ValueError("Failed to converge")

        uSq = cosSqAlpha * (a*a - b*b) / (b*b)
        A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
        B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
        deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-
                     B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
        return b*A*(sigma-deltaSigma)    
     
    def getAspectRatioAndDistance(self,mapRect):
        width = distVincenty( mapRect.swCorner.lat, mapRect.neCorner.lng, mapRect.swCorner.lat, mapRect.swCorner.lng )
        height = distVincenty( mapRect.neCorner.lat, mapRect.swCorner.lng, mapRect.swCorner.lat, mapRect.swCorner.lng )
        if (height > 0):
            aspect = width/height
            distance = sqrt(width**2 + height**2)
            return aspect,distance
        else:
            print "Warning: getAspectRatioAndDistance: attempt to divide by 0!"
            return 0.,0.
      
    def toXY(lat,lng,lat_ref,lng_ref):
        x = distVincenty(lat_ref,lng_ref,lat_ref,lng)
        if lng<lng_ref: x = -x
        y = distVincenty(lat_ref,lng,lat,lng)
        if lat<lat_ref: 
            y = -y
        return x,y
        
    def aspectAndDistToXYDivisors( self, mapRect, minAspectRatio, maxAspectRatio, minDist, maxDist, isPortrait ):
        '''Given a mapRect set of lat/long coordinates defining a bounding box on the Earth's surface 
        (as approximated in distVincenty), determine the minimum number of rows and columns 
        needed to divide it into subsections with an aspect ratio (width/height) within the range 
        specified and portraying no more than a distance of maxDist and no less than minDist (meters) 
        across the diagonal.
        If isPortrait == True, attempt to reach minAspectRatio, else attempt to reach maxAspectRatio
            H = page height, h = cell height
            W = page width, w = cell width
            d = sqrt( h**2 + w**2 )
            a = w/h = (W/ncol) / (H/nrow)
        Brute force method: calculate a_xy for nrow,ncol>=0 until d>=maxdist. Keep track of 
        a, nrow, ncol, d, for the combination of ncol,nrow that has max d and a closeset to the desired
        limit'''     

        bestNCol = 1
        bestNRow = 1
        maxNCol = 30    
        maxNRow = 30
        bestD = 0
        bestA = 0
        # Do we want to maximize or minimize "A"?
        if ( isPortrait ):
            bestA = 3.       # In the case we want to be closer to minAspectRatio, make bestA large
        for x in range( maxNCol ):
            ncol = x + 1
            for y in range( maxNRow ):
                nrow = y + 1
                upperRightCorner = LatLng( mapRect.swCorner.lat + ( mapRect.neCorner.lat - mapRect.swCorner.lat ) / nrow,
                               mapRect.swCorner.lng + ( mapRect.neCorner.lng - mapRect.swCorner.lng ) / ncol )
                tile = MapRect( mapRect.swCorner, upperRightCorner )
                thisA,thisD = getAspectRatioAndDistance( tile )
                if ( (thisD <= maxDist) and (thisD >= minDist) ):
                    if (( thisA >= minAspectRatio ) and ( thisA <= maxAspectRatio )):
                    # The choice of ncol, nrow satisfies the range criteria. 
                    # Is it better than what we have already?
                        if (isPortrait):
                            if (thisA < bestA):
                                bestNCol = ncol
                                bestNRow = nrow
                                bestA = thisA
                                bestD = thisD
                                print "New grid params (ncol, nrow, a, d): ", ncol, nrow, thisA, thisD
                        else:
                            if (thisA > bestA):
                                bestNCol = ncol
                                bestNRow = nrow
                                bestA = thisA
                                bestD = thisD
                                print "New grid params (ncol, nrow, a, d): ", ncol, nrow, thisA, thisD
                    
        return [bestNCol, bestNRow]        
    
class ReportBookletConfig(object):
    def __init__(self, *args, **kwargs):
   
        # Configuration Handling
        self.configUsingFile = False
        self.configFileName = ""
        self.userMarkersFile = None
        self.userMarkerList = []
        self.topDir = os.getcwd()
        self.reportDir = ""
        self.areaName = ""
        self.summaryMapDirList = []
        self.bookletMapDirList = []
        self.instructionsSubDir = "instructions"
        self.mapsSubDir = "maps"
        self.summaryMapsSubDir = "summary"
        self.bookletMapsSubDir = "booklet"
        self.sumDirBaseName = "summaryMap"
        self.tileDirBaseName = "tileMap"
        self.keyMapBaseType = "map"
        self.keyMapPadX = 50
        self.keyMapPadY = 50
        
        # Report parameters and data ranges
        self.report_title = ""
        self.sw_lattitude_deg = 0.
        self.sw_longitude_deg = 0.
        self.ne_lattitude_deg = 0.
        self.ne_longitude_deg = 0.
        self.min_amplitude_ppm = 0.03
        self.exclusion_radius_meters = 0 
        self.n_runs = 1
        
        # Data runs
        self.minimalRunParamsList = []
        
        # System map config
        self.n_kml = 0
        self.kmlConfigList = []
        
        # Summary and booklet section config: retrieved by GetMapDisplayConfigFromFile
        self.summaryMapConfigList = []   # a list of MapDisplayConfig
        self.tileDisplayConfigList = []  # a list of MapDisplayConfig
        self.nSummaryMaps = 3            
        self.nTileMaps = 2      
        self.gridParams = None
        
        # Debug options
        self.verbosity = 0
        self.assembleOnly = False

    def checkDirectory( self, dirName ):
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
        
    def setUpDirectories( self ): 
        dirToTry = self.areaName
        reportSubDir, dirExists = self.checkDirectory( dirToTry )
        self.areaName = reportSubDir
        success = True
        print "Preparing subdirectories in directory", reportSubDir
        if not dirExists:
            os.mkdir(reportSubDir)
        else:
            shutil.rmtree(reportSubDir, True)
            if not os.path.isdir(reportSubDir):
                os.mkdir(reportSubDir)    
        os.chdir(reportSubDir)
      
        os.mkdir(self.mapsSubDir)
        os.mkdir(self.instructionsSubDir)
        os.chdir(self.instructionsSubDir)
        os.mkdir(self.summaryMapsSubDir)
        os.mkdir(self.bookletMapsSubDir)
        os.chdir(self.summaryMapsSubDir)
        for dir in self.summaryMapDirList:
            os.mkdir(dir)
        os.chdir("../" + self.bookletMapsSubDir)
        for dir in self.bookletMapDirList:
            os.mkdir(dir)    
        os.chdir(self.topDir)
        
    def GetConfigModeFromUser(self):
        '''Determine whether or not to use a config file'''
        inpt = raw_input("   Input report parameters via config file? (y/n): ")
        inptFile = ""
        if ("y" in inpt):
            useFileInput = True
            inptFileNameInpt = raw_input("   Name of report parameters file? ")
            self.configFileName = self.topDir + "\\" + inptFileNameInpt
            self.configUsingFile = True
        else:
            self.configUsingFile = False

    def GetReportParamsFromFile(self, fn):
        '''This basically gets everything we haven't taken care of from the ReportParams block'''
        config = ConfigObj(fn)
        self.sw_lattitude_deg = config["ReportParams"]["sw_lattitude_deg"]
        self.sw_longitude_deg = config["ReportParams"]["sw_longitude_deg"]
        self.ne_lattitude_deg = config["ReportParams"]["ne_lattitude_deg"]
        self.ne_longitude_deg = config["ReportParams"]["ne_longitude_deg"]
        self.min_amplitude_ppm = config["ReportParams"]["min_amplitude_ppm"]
        self.exclusion_radius_meters = config["ReportParams"]["exclusion_radius_meters"] 
        self.n_runs = config["ReportParams"]["n_runs"]
        self.show_user_markers = config["ReportParams"]["show_user_markers"] 
        self.userMarkersFile = config["ReportParams"]["user_markers_file"]    
        self.report_title = config["ReportParams"]["report_title"]  
        self.reportDir = config["ReportParams"]["area_name"]
        self.areaName = config["ReportParams"]["area_name"]       
        self.keyBapBaseType = config["ReportParams"]["key_map_baseType"]
    
    def GetMinimalRunParamsListFromFile(self, fn):
        '''Retrieve the run information and create the run parms list'''
        config = ConfigObj(fn)
        self.n_runs = int(config["ReportParams"]["n_runs"])       
        key_list = []
        for i in range(self.n_runs):
            key_list.append("RunParams" + str(i+1))
        for i in key_list:
            startEtm = str( config[i]["run_start_date_gmt"] ) + " " + str(config[i]["run_start_time_gmt"])
            endEtm = str( config[i]["run_end_date_gmt"] ) + " " + str(config[i]["run_end_time_gmt"])
            self.minimalRunParamsList.append( MinimalRunParams( str( config[i]["analyzer"] ), startEtm, endEtm, str( config[i]["stab_class"] ) ) ) 
                                
    # Retrieves the configuration for the summary maps and tile maps from the config file.     
    def GetMapDisplayConfigFromFile(self, fn):
        config = ConfigObj(fn)
        self.nSummaryMaps = int(config["ReportParams"]["n_summary_maps"])    
        self.nTileMaps = int(config["ReportParams"]["n_maps_per_tile"])
        summary_map_key_list = []
        for i in range(self.nSummaryMaps):
            summary_map_key_list.append("SummaryMap" + str(i+1))
            self.summaryMapDirList.append( self.sumDirBaseName + str(i+1) )
        for i in summary_map_key_list:
            self.summaryMapConfigList.append( MapDisplayConfig( str( config[i]["baseType"] ),
                                                           str( config[i]["markerColor"] ),
                                                           str( config[i]["wedgeColor"] ),
                                                           str( config[i]["swathColor"] ),
                                                           int( config[i]["showKML"] ),
                                                           int( config[i]["showUserMarkers"] ),
                                                           str( config[i]["showTrail"] )                                                           
                                                          ) 
                                        )
        tile_map_key_list = []
        for i in range(self.nTileMaps):
            tile_map_key_list.append("TileMap" + str(i+1))
            self.bookletMapDirList.append(self. tileDirBaseName + str(i+1))
        for i in tile_map_key_list:
            self.tileDisplayConfigList.append( MapDisplayConfig( str( config[i]["baseType"] ),
                                                            str( config[i]["markerColor"] ),
                                                            str( config[i]["wedgeColor"] ),
                                                            str( config[i]["swathColor"] ),
                                                            int( config[i]["showKML"] ),
                                                            int( config[i]["showUserMarkers"] ), 
                                                            str( config[i]["showTrail"] )                                                               
                                                          ) 
                                        )    
        self.gridParams = GridParams( MapRect( LatLng(float(config["ReportParams"]["sw_lattitude_deg"]),
                                                      float(config["ReportParams"]["sw_longitude_deg"])), 
                                               LatLng(float(config["ReportParams"]["ne_lattitude_deg"]),
                                                      float(config["ReportParams"]["ne_longitude_deg"])) ), 
                                               int(config["GridParams"]["n_columns"]), 
                                               int(config["GridParams"]["n_rows"]), '', '' )
                                               
    def GetAssetDisplayConfig(self, fn): 
        '''Retrieve the KMLParams blocks'''
        config = ConfigObj(fn)
        n_kml = int(config["ReportParams"]["n_kml"])       
        key_list = []
        for i in range(n_kml):
            key_list.append("KMLParams" + str(i+1))
        for i in key_list:
            self.kmlConfigList.append( AssetDisplayConfig( str( config[i]["kml_filename"] ),
                                                      str( config[i]["kml_linewidth"] ),
                                                      str( config[i]["kml_linecolor"] ), 
                                                      str( config[i]["kml_filter"] )
                                                    )
                                )

    def GetUserMarkersFromFile( self, fn ):
        if not (os.path.isfile(self.userMarkersFile)):
            print "Markers file ", self.userMarkersFile, "does not exist!"
        else:
            id, lng, lat, color = np.genfromtxt(self.userMarkersFile, unpack=True, dtype="O")
            for i in range(len(id)):
                self.userMarkerList.append( MarkerInfo(id[i], lng[i], lat[i], color[i]) )     
            #print "Marker list has ", str(len(self.userMarkerList)), " entries"
        
    def DoConfig(self):
        self.GetConfigModeFromUser() 
        if (self.configUsingFile):
            self.GetReportParamsFromFile(self.configFileName)
            self.GetMapDisplayConfigFromFile(self.configFileName)
            self.GetAssetDisplayConfig(self.configFileName)
            self.GetMinimalRunParamsListFromFile(self.configFileName)
            self.GetUserMarkersFromFile(self.userMarkersFile)
        else:
            print "Sorry, you must configure your report using a config file for now." 
        if not (self.assembleOnly):
            self.setUpDirectories()
        os.chdir( self.topDir + '\\' + self.reportDir )

class InstructionsWriter(object):
    '''Take a configuration object and write all of the instructions needed to create a report booklet'''
    def __init__(self, config):
        self.cfg = config

    def PartitionMap( self, mapRect, ncol, nrow ):
        rectRowList = []
        swCorner = mapRect.swCorner
        neCorner = mapRect.neCorner
        dy = float(( float(neCorner.lat) - float(swCorner.lat) ) / int(nrow))
        dx = float(( float(neCorner.lng) - float(swCorner.lng) ) / int(ncol))
        curSwCornerLat = float(swCorner.lat)
        curSwCornerLng = float(swCorner.lng)
        curNeCornerLat = float(swCorner.lat) + dy
        curNeCornerLng = float(swCorner.lng) + dx
        for y in range(nrow):    
            rectList = []
            curSwCornerLng = float(swCorner.lng)
            curNeCornerLng = float(swCorner.lng) + dx
            for x in range(ncol):
                curSwCorner = LatLng( curSwCornerLat, curSwCornerLng )
                curNeCorner = LatLng( curNeCornerLat, curNeCornerLng )
                rectList.append( MapRect(curSwCorner,curNeCorner) )
                curSwCornerLng += dx
                curNeCornerLng += dx
            curSwCornerLat += dy
            curNeCornerLat += dy
            rectRowList.append( rectList )
        return rectRowList    
        
    def GetRegionBlock(self, regionParams, kmlParams=None):
        blws = "    "
        regionBlock = blws + blws + "{\n"
        regionBlock += blws + blws + blws + "\"baseType\": \"" + regionParams.baseType + "\",\n"
        regionBlock += blws + blws + blws + "\"name\": \"" + regionParams.name + "\",\n"
        regionBlock += blws + blws + blws + "\"swCorner\": [\n"
        regionBlock += blws + blws + blws + blws + str( regionParams.swCorner.lat ) + ",\n"
        regionBlock += blws + blws + blws + blws + str( regionParams.swCorner.lng ) + "\n"
        regionBlock += blws + blws + blws + "],\n"
        regionBlock += blws + blws + blws + "\"neCorner\": [\n"
        regionBlock += blws + blws + blws + blws + str( regionParams.neCorner.lat ) + ",\n"
        regionBlock += blws + blws + blws + blws + str( regionParams.neCorner.lng ) + "\n"
        regionBlock += blws + blws + blws + "],\n"
        regionBlock += blws + blws + blws + "\"comments\": \"" + regionParams.comments + "\",\n"
        #regionBlock += blws + blws + blws + "\"kml\": \": [\n"
        #regionBlock += blws + blws + blws + blws + "\"" + kml_fn + "\",\n"
        #regionBlock += blws + blws + blws + blws + "\"" + kml_fn + "\",\n" 
        regionBlock += self.GetKmlBlock( kmlParams ) + "\n"
        regionBlock += blws + blws + "}"        
        return regionBlock
     
    # Translate the parameters for a single run block into text for an instructions file
    def GetRunBlock( self, minimalRunParams, displayConfig ): 
        blws = "    " 
        runBlock = blws + blws + "{\n"
        runBlock += blws + blws + blws + "\"analyzer\": \"" + minimalRunParams.analyzer + "\",\n"
        runBlock += blws + blws + blws + "\"startEtm\": \"" + minimalRunParams.startEtm + "\",\n"
        runBlock += blws + blws + blws + "\"endEtm\": \"" + minimalRunParams.endEtm + "\",\n"
        runBlock += blws + blws + blws + "\"path\": \"" + displayConfig.showTrail + "\",\n"
        runBlock += blws + blws + blws + "\"marker\": \"" + displayConfig.bubbleColor + "\",\n"
        runBlock += blws + blws + blws + "\"wedges\": \"" + displayConfig.wedgeColor + "\",\n"
        runBlock += blws + blws + blws + "\"swath\": \"" + str(displayConfig.swathColor) + "\",\n"
        runBlock += blws + blws + blws + "\"minAmpl\": " + self.cfg.min_amplitude_ppm + ",\n"   
        runBlock += blws + blws + blws + "\"exclRadius\": " + self.cfg.exclusion_radius_meters + ",\n"
        runBlock += blws + blws + blws + "\"stabClass\": \"" + minimalRunParams.stabClass + "\",\n"  
        runBlock += blws + blws + blws + "\"comments\": \"\"\n"
        runBlock += blws + blws + "}"
        return runBlock 
         
    def GetMarkerBlock( self, markerList=None ):
        blws = "    "  
        markerBlock = blws + "\"markers\": [\n" 
        if ( markerList == None ) or ( len(markerList) == 0 ):
            markerBlock += blws + "]\n"
            return markerBlock
        
        first = True
        for marker in markerList:
            if (not first):
                newEntry = blws + blws + "},\n"
            else:
                newEntry = ""
            newEntry += blws + blws + "{\n"
            newEntry += blws + blws + blws + '"label": "' + marker.name + '",\n'
            newEntry += blws + blws + blws + '"location": [\n'
            newEntry += blws + blws + blws + blws + marker.lat + ',\n'
            newEntry += blws + blws + blws + blws + marker.lng + '\n'
            newEntry += blws + blws + blws + '],\n'
            newEntry += blws + blws + blws + '"color": "#' + marker.color + '",\n'
            newEntry += blws + blws + blws + '"comments": ""\n'     
            first = False
            markerBlock += newEntry
        markerBlock += blws + blws + "}\n"
        markerBlock += blws + "]\n"
        return markerBlock

    def GetKmlBlock( self, kmlList = None ):
        '''kmlList is a list of AssetDisplayConfig'''
        blws = "    "
        kmlBlock = blws + blws + blws + "\"kml\": [\n" 
        if ( kmlList == None ) or ( len(kmlList)==0 ):
            kmlBlock += blws + blws + blws + "]"
            return kmlBlock    

        first = True
        for entry in kmlList:
            if (not first):
                newEntry = blws + blws + blws + blws + "},\n"
            else:
                newEntry = ""
            newEntry += blws + blws + blws + blws + "{\n"
            newEntry += blws + blws + blws + blws + blws + '"filename": "' + entry.fileName + '",\n'
            newEntry += blws + blws + blws + blws + blws + '"linewidth": ' + entry.lineWidth + ',\n'
            newEntry += blws + blws + blws + blws + blws + '"linecolor": "' + entry.lineColor + '",\n'
            newEntry += blws + blws + blws + blws + blws + '"filter": "' + entry.filter + '"\n'        
            first = False
            kmlBlock += newEntry
        kmlBlock += blws + blws + blws + blws + "}\n"
        kmlBlock += blws + blws + blws + "]"
        return kmlBlock  
    
        
    def WriteTileInstructions( self, fn, displayConfig ):
        '''write the instructions for a single set of tiles (grid boxes)'''
        blws = "    "
        instructions = "// Instructions file generated by createReportBooklet\n"
        instructions += "{\n"
        instructions += blws + "\"regions\": [\n"
        
        regionsList = self.PartitionMap( self.cfg.gridParams.mapRect, self.cfg.gridParams.ncol, self.cfg.gridParams.nrow )
        
        counter = 0
        for y in range( len(regionsList) ):   # for each row
            for x in range( len( regionsList[y] ) ): 
                regName = self.cfg.gridParams.baseName + str( counter )
                curRegionParams = RegionParams( displayConfig.baseType, regName, regionsList[y][x].swCorner, regionsList[y][x].neCorner, "" )
                if ( displayConfig.overlayKml==1 ):
                    instructions += self.GetRegionBlock( curRegionParams, self.cfg.kmlConfigList )
                else: 
                    instructions += self.GetRegionBlock( curRegionParams )               
                if ( x < len( regionsList[y] ) - 1 ) or (y < len(regionsList) - 1):
                    instructions += ",\n"
                else:
                    instructions += "\n"
                counter += 1
        instructions += blws + "],\n"
        
        # Now write the run block
        instructions += blws + "\"runs\": [\n"

        for i in range (len(self.cfg.minimalRunParamsList)):
            instructions += self.GetRunBlock( self.cfg.minimalRunParamsList[i], displayConfig )
            if (i < len(self.cfg.minimalRunParamsList)-1):
                instructions += ",\n"
            else:
                instructions += "\n"
        instructions += blws + "],\n"
        if (displayConfig.overlayUserMarkers==1):
            instructions += self.GetMarkerBlock(cfg.userMarkerList)    
        else:
            instructions += self.GetMarkerBlock()
        instructions += "}"         
        instFile = file(fn,"wb")
        instFile.write(instructions)
        instFile.close()
    
    def WriteSummaryInstructions( self, fn, displayConfig ):
        '''write the intructions for a single summary map'''
        '''write the instructions for a single set of tiles (grid boxes)'''
        blws = "    "
        instructions = "// Instructions file generated by createReportBooklet\n"
        instructions += "{\n"
        instructions += blws + "\"regions\": [\n"
        
        regName = cfg.gridParams.baseName
        swCorner = LatLng( cfg.sw_lattitude_deg, cfg.sw_longitude_deg )
        neCorner = LatLng( cfg.ne_lattitude_deg, cfg.ne_longitude_deg )
        curRegionParams = RegionParams( displayConfig.baseType, regName, swCorner, neCorner, "" )
        if ( displayConfig.overlayKml==1 ):
            instructions += self.GetRegionBlock( curRegionParams, cfg.kmlConfigList )
        else:
            instructions += self.GetRegionBlock( curRegionParams )        
        instructions += "\n"
        instructions += blws + "],\n"
        
        # Now write the run block
        instructions += blws + "\"runs\": [\n"

        for i in range (len(cfg.minimalRunParamsList)):
            instructions += self.GetRunBlock( cfg.minimalRunParamsList[i], displayConfig )
            if (i < len(cfg.minimalRunParamsList)-1):
                instructions += ",\n"
            else:
                instructions += "\n"
        instructions += blws + "],\n"
        if (displayConfig.overlayUserMarkers==1):
            instructions += self.GetMarkerBlock(cfg.userMarkerList)    
        else:
            instructions += self.GetMarkerBlock()      
        instructions += "}"        
        instFile = file(fn,"wb")
        instFile.write(instructions)
        instFile.close()
        
    def WriteAllInstructions( self ):
        os.chdir( cfg.instructionsSubDir )
        fnBase = "instructions_"
        for i in range(len(cfg.summaryMapConfigList)):
            fn = fnBase + cfg.summaryMapDirList[i] + ".json"
            self.WriteSummaryInstructions( fn, cfg.summaryMapConfigList[i] )            
        for i in range(len(cfg.tileDisplayConfigList)):
            fn = fnBase + cfg.bookletMapDirList[i] + ".json"
            self.WriteTileInstructions( fn, cfg.tileDisplayConfigList[i] )
        os.chdir( cfg.topDir + '\\' + cfg.reportDir )
            
class InstructionsProcessor(object):            
    '''Run the instructions files and move the results to the proper subdirs
    Requires GoogleMap class from FetchingGoogleMaps
    Each step assumes we start and end up in the top-level working directory of the report'''
    
    def __init__(self, config):
        self.cfg = config      

    def raiseOnError(self, result):
        if 'error' in result and result['error'] is not None: raise RuntimeError(result['error'])
        result = result['return']
        if 'error' in result and result['error'] is not None: raise RuntimeError(result['error'])
        return result        
        
    def processJSON(self, instructions, subDir):
        '''Argument is the name of JSON instruction file'''
        reportApi = ReportApiService()
        reportApi.csp_url = "http://localhost:5200"
        # reportApi.ticket_url = P3Api.csp_url + "/rest/sec/dummy/1.0/Admin/"
        # reportApi.identity = "85490338d7412a6d31e99ef58bce5de6"
        # reportApi.psys = "APITEST"
        # reportApi.rprocs = '["ReportGen"]'
        reportApi.debug = True
        
        #if len(sys.argv) >= 2:
        #    instructions = sys.argv[1]
        #else:
        #    instructions = raw_input("Name of instructions file? ")
        
        fp = open(instructions,"rb")
        contents = fp.read().splitlines()
        fp.close()

        while contents[0].startswith("//"):
            contents.pop(0)
        # Check this is valid JSON
        contents = "\n".join(contents)
        json.loads(contents)    # Throws exception on faulty JSON
        
        # Get the secure hash for prepending        
        qryparms = { 'qry': 'download', 'content': contents,  'filename': 'instructions.json'}
        contents = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))

        op = file("validated.json","wb")
        op.write(contents)
        op.close()
        
        qryparms = { 'qry': 'validate', 'contents': contents }
        result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        contents = result['contents']
        
        qryparms = { 'qry': 'getTicket', 'contents': contents }
        result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        ticket = result['ticket']
        
        ###
        qryparms = { 'qry': 'remove', 'ticket': ticket }
        self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        # print raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))

        qryparms = { 'qry': 'getReportStatus', 'ticket': ticket }
        self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        
        qryparms = { 'qry': 'instrUpload', 'contents': contents }
        self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        
        status = None
        while True:
            qryparms = { 'qry': 'getReportStatus', 'ticket': ticket }
            result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
            if 'files' in result and 'json' in result['files']:
                status = result['files']['json']
                if 'done' in status and status['done']:
                    break
            time.sleep(2.0)
            
        # Get the composite maps and reports
        if status:
            for f in status:
                if f.startswith('composite'):
                    region = int(f.split('.')[-1])
                    qryparms = { 'qry': 'getComposite', 'ticket': ticket, 'region': region }
                    result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
                    fp = open(f + ".png","wb")
                    fp.write(result);
                    fp.close()
                    qryparms = { 'qry': 'getPDF', 'ticket': ticket, 'region': region }
                    result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
                    fp = open(f + ".pdf","wb")
                    fp.write(result);
                    fp.close()
                    qryparms = { 'qry': 'getXML', 'ticket': ticket, 'region': region }
                    result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
                    fp = open(f + ".xml","wb")
                    fp.write(result);
                    fp.close()
                    qryparms = { 'qry': 'getPeaks', 'ticket': ticket, 'region': region }
                    result = self.raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
                    fp = open(f + ".markerTable.html","wb")
                    fp.write(result);
                    fp.close()
        
    def RunKeyMap(self):
        '''Make the key map'''
        '''Change to the map dir'''
        os.chdir( cfg.mapsSubDir )
        useSatellite = ( "sat" in cfg.keyMapBaseType )
        q, mp = GoogleMap().getPlat( cfg.gridParams.mapRect.swCorner.lng,
                                     cfg.gridParams.mapRect.neCorner.lng,
                                     cfg.gridParams.mapRect.swCorner.lat,
                                     cfg.gridParams.mapRect.neCorner.lat,
                                     useSatellite, 
                                     cfg.keyMapPadX,
                                     cfg.keyMapPadY
                                    )
                                
        rectList = partition(cfg.gridParams.mapRect,cfg.gridParams.nrow,cfg.gridParams.ncol)
        pm = PartitionedMap(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
        q1 = pm.drawPartition(q,partition(cfg.gridParams.mapRect,cfg.gridParams.nrow,cfg.gridParams.ncol))
        op = file("mapKey.png","wb")
        op.write(asPNG(q1))
        op.close()
        os.chdir( cfg.topDir + '\\' + cfg.reportDir )   

    def RunSummaryMaps(self):
        '''Make the summary maps'''
        os.chdir( cfg.instructionsSubDir )
        for subDir in cfg.summaryMapDirList:
            instructionsFile = 'instructions_' + subDir + '.json'
            self.processJSON( instructionsFile, subDir )
            # Move results to appropriate subdir
            resultsToKeep = ['composite']
            for j in range( len(resultsToKeep) ):
                for data in glob.glob( resultsToKeep[j]+"*" ):
                    shutil.move( data, cfg.summaryMapsSubDir + '\\' + subDir )  
        os.chdir( cfg.topDir + '\\' + cfg.reportDir )
        
    def RunTileMaps(self):
        '''Make the tile maps'''
        os.chdir( cfg.instructionsSubDir )
        for subDir in cfg.bookletMapDirList:
            instructionsFile = 'instructions_' + subDir + '.json'
            self.processJSON( instructionsFile, subDir )      
            # Move results to appropriate subdir
            resultsToKeep = ['composite']
            for j in range( len(resultsToKeep) ):
                for data in glob.glob( resultsToKeep[j]+"*" ):
                    shutil.move( data, cfg.bookletMapsSubDir + '\\' + subDir )   
        os.chdir( cfg.topDir + '\\' + cfg.reportDir )
        
    def RunAllInstructions(self):
        if not cfg.assembleOnly:
            self.RunKeyMap()
            self.RunSummaryMaps()
            self.RunTileMaps()

class ReportAssembler(object):
    '''Assemble the report from the various elements contained in subdirs'''
    def __init__(self, config):
        self.cfg = config
        self.report = ''

    def reportParamsToHTML(self):
        page = '<table border="0">'
        page += '<tr><td>Minimum Amplitude (ppm):</td><td>%s</td></tr>' % str(cfg.min_amplitude_ppm)
        page += '<tr><td>Exclusion Radius (m):</td><td>%s</td></tr>' % str(cfg.exclusion_radius_meters)    
        page += '</table>'
        page += '<br>'
        page += '<h3>User-defined runs included:</h3>'
        for run in cfg.minimalRunParamsList:
            #page += '<h3>Run %s:</h3>' % str(run+1)
            page += '<table border="0">'
            page += '<tr><td>Analyzer:</td><td>%s</td></tr>' % str(run.analyzer)
            page += '<tr><td>Start (GMT):</td><td>%s</td></tr>' % str(run.startEtm)
            page += '<tr><td>End (GMT):</td><td>%s</td></tr>' % str(run.endEtm)
            page += '<tr><td>Stability Class:</td><td>%s</td></tr>' % str(run.stabClass)        
            page += '</table>'
            page += '<br>' 
        return page
        
    def getLogsTable(self):    
        '''Return of list of the logs that were included in the report'''
        page = ''
        return page
        
    def getMarkerTable(self):
        '''There must be at least one summary map directory'''
        fn = cfg.topDir + '\\' + cfg.reportDir+'\\'+cfg.instructionsSubDir+'\\'+cfg.summaryMapsSubDir+'\\'+cfg.sumDirBaseName+'1\\composite.0.markerTable.html'
        f = file(fn,"rb")
        lineList = f.readlines()   
        contents = "<h3>Leak Indications:</h3>\n"
        for line in lineList:
            contents += line + '\n'
        f.close()
        return contents     

    def removeTD( self, line ):
        newline = line.replace('<td>',"")    
        newline = newline.replace('</td>',"")
        newline = newline.replace("\n","")
        return newline        
        
    def getMarkerListFromHTML( self, fn ):
        markerList = []
        f = file(fn,"rb")
        # Loop thru the lines and look for <tr>. Ignore the first instance, which is accompanied by <thead>
        line = f.readline()
        while (line != ""):
            if (( ('<tr>' in line) and ( not ('thead' in line)) and ( not ('/tr' in line)) )):
                name = self.removeTD(f.readline())  # This line contains the name
                lat = f.readline()
                lat = self.removeTD(f.readline())
                lng = self.removeTD(f.readline())
                markerList.append( MarkerInfo( name, lat, lng, "00FFFF") )
            line = f.readline()
        f.close()
        #print "MarkerList: ", markerList
        return markerList        
        
    def getUserMarkerTable(self):
        '''Return a table containing the user-defined markers'''
        contents = ''
        return contents
        
    def getReportCoverPage(self):
        coverPage = "<h1>Picarro Surveyor&#0153; for Natural Gas Leaks</h1>\n"
        coverPage += "<h2>%s</h2>" % cfg.report_title
        coverPage += self.reportParamsToHTML()
        coverPage += self.getLogsTable()
        coverPage += self.getMarkerTable()
        coverPage += self.getUserMarkerTable()
        return coverPage   

    def picHTML(self, picName, widthPCT):
        picUrl = "file:%s" % urllib.pathname2url(os.path.abspath(picName))
        picUrl = picUrl.replace("|",":")
        pic = '<img src="%s" alt="" width="' % picUrl
        pic += str(widthPCT) 
        pic += '%%">' 
        return pic     

    def getMapKeyPage(self):
        page = "<h2 style=\"page-break-before:always;\">Map Key</h2>"
        fn = self.cfg.topDir + '\\' + self.cfg.reportDir + '\\' + self.cfg.mapsSubDir + '\\mapKey.png'
        page += self.picHTML( fn, 95 )
        return page        
        
    def GetSummaryMapPages(self):
        page = "<h2 style=\"page-break-before:always;\">Overview</h2>"
        pathBase = self.cfg.topDir + '\\' + self.cfg.reportDir + '\\' + self.cfg.instructionsSubDir + '\\' + self.cfg.summaryMapsSubDir
        for d in self.cfg.summaryMapDirList:
            #page += "<p style=\"page-break-before:always;\">%(a)s &emsp;&emsp; Min Ampl: %(b)s &emsp;&emsp; Excl Rad: %(c)s</p>" % \
            #    { "a": self.cfg.areaName, "b": str(self.cfg.min_amplitude_ppm), "c": str(self.cfg.exclusion_radius_meters) }
            page += "<p>%(a)s &emsp;&emsp; Min Ampl: %(b)s &emsp;&emsp; Excl Rad: %(c)s</p>" % \
                { "a": self.cfg.areaName, "b": str(self.cfg.min_amplitude_ppm), "c": str(self.cfg.exclusion_radius_meters) }
            picName = pathBase + '\\' + d + '\\' + "composite.0.png"
            page += self.picHTML( picName, 95 )
            os.chdir( "..\\" )
        return page        
  
    def getPageOrderAndNumbers(self):
        '''The images are numbered from zero starting with the lower left corner, increasing to the right and up. 
        Return a list that orders the images from the top left increasing to the right and down 
        The first page of row r where r is indexed from 0 is (ny-r-1)*nx
        Also return a list of alpha-numeric page numbers''' 
        nx = self.cfg.gridParams.ncol
        ny = self.cfg.gridParams.nrow
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
        
    def getMarkerListForHeader( self, markerList ):
        header = "<p>Indications: "
        first = True
        for marker in markerList:
            if not first:
                header += ", "
            header += str(marker.name)
            first = False
        header += "</p>"
        return header        
  
    def replaceMarkerNames( self, markerList, masterList ):
        newMarkerList = []
        for marker in markerList:
            newName = ""
            for master in masterList:
                if ( marker.lat == master.lat ) and ( marker.lng == master.lng ):
                    newName = master.name
                    break
            newMarkerList.append( MarkerInfo( newName, marker.lat, marker.lng, marker.color ) )
        return newMarkerList  
  
    def GetBookletPages(self):
        '''There must be at least one category of tile map'''
        booklet = ""
        pageList, pageNumbers = self.getPageOrderAndNumbers()
        markerTableFile = self.cfg.topDir+'\\'+self.cfg.reportDir+'\\'+self.cfg.instructionsSubDir+'\\'+self.cfg.summaryMapsSubDir+'\\'+self.cfg.sumDirBaseName+'1\\composite.0.markerTable.html'
        masterMarkerList = self.getMarkerListFromHTML(markerTableFile)
        for page in pageList: 
            booklet += "<p style=\"page-break-before:always;\">%(a)s &emsp;&emsp; Min Ampl: %(b)s &emsp;&emsp; Excl Rad: %(c)s &emsp;&emsp; <b>Grid: %(d)s</b></p>" % \
                { "a": str(self.cfg.areaName), "b": str(self.cfg.min_amplitude_ppm), "c": str(self.cfg.exclusion_radius_meters), "d": pageNumbers[page] }
            # Include the list of markers on this page
            fn = self.cfg.topDir+'\\'+self.cfg.reportDir+'\\'+self.cfg.instructionsSubDir+'\\'+self.cfg.bookletMapsSubDir+'\\'+self.cfg.tileDirBaseName+'1\\composite.%s.markerTable.html' % str( page )
            localMarkerList = self.getMarkerListFromHTML(fn)
            markerList = self.replaceMarkerNames( localMarkerList, masterMarkerList )
            booklet += self.getMarkerListForHeader(markerList)
            os.chdir( self.cfg.topDir + '\\' + self.cfg.reportDir +'\\'+ self.cfg.instructionsSubDir +'\\'+ self.cfg.bookletMapsSubDir )
            for d in self.cfg.bookletMapDirList:
                os.chdir(d)
                booklet += self.picHTML( "composite."+str(page)+".png", 95 )
                os.chdir("..\\")
            os.chdir( self.cfg.topDir )
        return booklet        
   
    def AssembleReport(self):
        self.report += self.getReportCoverPage()
        self.report += self.getMapKeyPage()
        self.report += self.GetSummaryMapPages()
        self.report += self.GetBookletPages()
      
        #Convert to PDF
        os.chdir(cfg.topDir + '\\' + cfg.reportDir)
        fn = "Report_" + self.cfg.areaName + ".pdf"
        proc = subprocess.Popen([WKHTMLTOPDF,"-",fn],
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        proc.communicate(self.report)   
        # Copy the Excel and PDF lists
        xml_fn = self.cfg.topDir + '\\'+ self.cfg.reportDir + "\\Report_" + self.cfg.areaName + ".xml"    
        dir_to_file = self.cfg.topDir +'\\'+ self.cfg.reportDir +'\\'+ self.cfg.instructionsSubDir +'\\'+ self.cfg.summaryMapsSubDir +'\\'+ self.cfg.sumDirBaseName + '1'
        shutil.copy(dir_to_file + '\\composite.0.xml', xml_fn)        
        
if __name__ == "__main__":
    
    print "\nPicarro Surveyor Report Booklet Generation -- Command Line Interface\n(November, 2012 version)"
    print "Copyright (c) 2012 Picarro, Inc., All Rights Reserved.\n"
    print "  See the example files:"
    print "     createReportBooklet.ini"
    print "     serMarkers.dat\n"
    cfg = ReportBookletConfig()
    cfg.DoConfig()
    #print "Cur dir is ", os.getcwd()
    writer = InstructionsWriter(cfg)
    writer.WriteAllInstructions()
    instrProc = InstructionsProcessor(cfg)
    instrProc.RunAllInstructions()
    assembler = ReportAssembler(cfg)
    assembler.AssembleReport()
    
