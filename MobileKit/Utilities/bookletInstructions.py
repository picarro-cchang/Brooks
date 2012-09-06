#!/usr/bin/python
#
"""
File Name: ReportBookletSupport.py
Purpose: Support for Surveyor report generation in booklet format

File History:
    24-Aug-2012  D. Steele  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""

try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple

from numpy import arange, arcsin, arctan2, arctan, tan, asarray, cos, isfinite, isnan
from numpy import log, pi, sin, sqrt, unwrap
    
LatLng = namedtuple( 'LatLng', ["lat", "lng"] )
MapRect = namedtuple( 'MapRect', ["swCorner", "neCorner"] )

RunBlockParams = namedtuple('RunParams',['analyzer','startEtm','endEtm','markerColor','wedgeColor', 'swathColor', 'minApl', 'exclRadius', 'stabClass', 'comments'])
MinimalRunParams = namedtuple( 'MinimalRunParams', [ 'startEtm','endEtm','minAmpl','exclRadius', 'stabClass' ])    

RegionParams = namedtuple( 'RegionParams', ['baseType', 'name', 'swCorner', 'neCorner', 'comments'] )
GridParams = namedtuple( 'GridParams', ['mapRect', 'ncol', 'nrow', 'baseName', 'baseType'] )

def distVincenty(lat1, lng1, lat2, lng2):
    # WGS-84 ellipsiod. lat and lng in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563;
    toRad = pi/180.0
    L = (lng2-lng1)*toRad
    U1 = arctan((1-f) * tan(lat1*toRad))
    U2 = arctan((1-f) * tan(lat2*toRad));
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

def distVincenty2(mapRect):
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
 
def getAspectRatioAndDistance(mapRect):
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
    
# Given a mapRect set of lat/long coordinates defining a bounding box on the Earth's surface 
# (as approximated in distVincenty), determine the minimum number of rows and columns 
# needed to divide it into subsections with an aspect ratio (width/height) within the range 
# specified and portraying no more than a distance of maxDist and no less than minDist (meters) 
# across the diagonal.
#  If isPortrait == True, attempt to reach minAspectRatio, else attempt to reach maxAspectRatio
#  H = page height, h = cell height
#  W = page width, w = cell width
#  d = sqrt( h**2 + w**2 )
#  a = w/h = (W/ncol) / (H/nrow)
#  Brute force method: calculate a_xy for nrow,ncol>=0 until d>=maxdist. Keep track of 
#  a, nrow, ncol, d, for the combination of ncol,nrow that has max d and a closeset to the desired
#  limit 
def aspectAndDistToXYDivisors( mapRect, minAspectRatio, maxAspectRatio, minDist, maxDist, isPortrait ):
    print "aspectAndDistToDivisors: Doing nothing for now"
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
  
# Partitions a mapRect set of coordinates into ncol colums and nrow rows. 
# Returns a list containing a list of mapRect for each row    
def partitionMap( mapRect, ncol, nrow ):
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

# Get input and ask user if that's what they really meant    
def getInputNicely( question ):
    answer = raw_input( question )
    print "   You answered: " + answer
    happy = raw_input("   Is that correct? [y/n] ")
    if "y" in happy:
        return answer
    else:
        return getInputNicely( question )

# This function can be used to get certain "minimal" run parameters, that is, parameters that 
# change often (date, time, etc. as opposed to analyzer and colors), from the command line. 
# It is intended for use during development. Returns a list of MinimalRunParams.
def getMinimalRunParametersListFromCommandLine():
    nrunsStr = getInputNicely("How many runs to include? ")
    nruns = int(nrunsStr)
    minAmpl = getInputNicely("Minimum amplitude? (will be applied to all runs) ")
    exclRad = getInputNicely("Exclusion radius? (will be applied to all runs) ")    
    minRunParamsList = []
    
    for i in range(nruns):
        print "Please specifiy parameters for run ", (i+1), ": "
        startDate = getInputNicely("Run start date? (YYYY-MM-DD): ") 
        startTime = getInputNicely("Run start time (GMT)? (HH:MM): ") 
        startString = startDate + " " + startTime
        endDate = getInputNicely("Run end date? (YYYY-MM-DD): ") 
        endTime = getInputNicely("Run end time (GMT)? (HH:MM): ")
        endString = endDate + " " + endTime
        stabClass = getInputNicely("Stability class? ") 
        minRunParamsList.append( MinimalRunParams( startString, endString, minAmpl, exclRad, stabClass ) )
        
    return minRunParamsList

def getMinimalRunParametersTest():
    startTime = "2012-08-27 18:30"
    endTime = "2012-08-27 20:30"
    ampl = "0.05"
    exclR = "15"
    stab = "B"
    minRunParamsList = []
    minRunParamsList.append( MinimalRunParams( startTime, endTime, ampl, exclR, stab ) )
    return minRunParamsList
    
# Ask the user for     
def getGridParametersFromCommandLine():
    print "Specify the map and grid parameters: "
    swCornerLat = float(getInputNicely( "  SW Corner Latitude  (deg): " ))
    swCornerLng = float(getInputNicely( "  SW Corner Longitude (deg): " ))
    swCorner = LatLng( swCornerLat, swCornerLng )
    neCornerLat = float(getInputNicely( "  NE Corner Latitude  (deg): " ))
    neCornerLng = float(getInputNicely( "  NE Corner Longitude (deg): " ))  
    neCorner = LatLng( neCornerLat, neCornerLng )    
    map = MapRect( swCorner, neCorner )
    nCol = int( getInputNicely( "  Number of columns: " ) )
    nRow =  int( getInputNicely( "  Number of rows: " ) )
    gridPars = GridParams( map, nCol, nRow, "", "" )
    return gridPars

def getGridParametersFromCommandLine2():

    # Default settings:
    minAspect = 0.65
    maxAspect = 0.9
    minDist = 400.0
    maxDist = 700.0
  
    isPortrait = True
    inpt = raw_input("Would you like me to help you choose the number of columns and rows for the grid? ")  
    if ("y" in inpt):
    #swCornerLat = float(getInputNicely( "  SW Corner Latitude  (deg): " ))
    #swCornerLng = float(getInputNicely( "  SW Corner Longitude (deg): " ))
    swCornerLat = 32.74839
    swCornerLng = -96.76693
    swCorner = LatLng( swCornerLat, swCornerLng )
    #neCornerLat = float(getInputNicely( "  NE Corner Latitude  (deg): " ))
    #neCornerLng = float(getInputNicely( "  NE Corner Longitude (deg): " ))  
    neCornerLat = 32.75676
    neCornerLng = -96.75592
    neCorner = LatLng( neCornerLat, neCornerLng )    
    map = MapRect( swCorner, neCorner )
    print "The default settings are: "
    print "   Minimum aspect ratio: ", minAspect
    print "      Maximum aspect ratio: ", maxAspect
    print "   Minimum diagonal distance (meters): ", minDist
    print "      Maximum diagonal distance (meters): ", maxDist
    inpt = raw_input("Would you like to change the default settings? ")
    if ( "y" in inpt ):
        minAspect = getInputNicely("Minimum aspect ratio? ")
        maxAspect = getInputNicely("Maximum aspect ratio? ")    
        minDist = getInputNicely("Minimum diagonal distance? ")        
            maxDist = getInputNicely("Minimum diagonal distance? ")
    ncol, nrow = aspectAndDistToXYDivisors( map, minAspect, maxAspect, minDist, maxDist, isPortrait )
    gridPars = GridParams( map, ncol, nrow, "", "" )
    
    else:
    return getGridParametersFromCommandLine()
    
    
def getGridParametersTest():
    swCorner = LatLng( 32.74839, -96.76693 )
    neCorner = LatLng( 32.75676, -96.75592 )
    map = MapRect( swCorner, neCorner )
    print "This is a test\n"
    gridPars = GridParams( map, 3, 2, "", "" )
    return gridPars
    
# Return a string in block format containing the specified region parameters    
#def getRegionBlock(mapType, name, mapRect, comments="" ):
def getRegionBlock(regionParams):
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
    regionBlock += blws + blws + blws + "\"comments\": \"" + regionParams.comments + "\"\n"   
    regionBlock += blws + blws + "}"        
    return regionBlock
 
# Translate the parameters for a single run block into text for an instructions file
def getRunBlock(runBlockParams): 
    blws = "    " 
    runBlock = blws + blws + "{\n"
    runBlock += blws + blws + blws + "\"analyzer\": \"" + runBlockParams.analyzer + "\",\n"
    runBlock += blws + blws + blws + "\"startEtm\": \"" + runBlockParams.startEtm + "\",\n"
    runBlock += blws + blws + blws + "\"endEtm\": \"" + runBlockParams.endEtm + "\",\n"
    runBlock += blws + blws + blws + "\"marker\": \"" + runBlockParams.markerColor + "\",\n"
    runBlock += blws + blws + blws + "\"wedges\": \"" + runBlockParams.wedgeColor + "\",\n"
    runBlock += blws + blws + blws + "\"swath\": \"" + runBlockParams.swathColor + "\",\n"
    runBlock += blws + blws + blws + "\"minAmpl\": " + runBlockParams.minApl + ",\n"   
    runBlock += blws + blws + blws + "\"exclRadius\": " + runBlockParams.exclRadius + ",\n"
    runBlock += blws + blws + blws + "\"stabClass\": \"" + runBlockParams.stabClass + "\",\n"  
    runBlock += blws + blws + blws + "\"comments\": \"" + runBlockParams.comments + "\"\n"
    runBlock += blws + blws + "}"
    return runBlock 

# For now, this just returns an empty marker block    
def getMarkerBlock():
    blws = "    "  
    markerBlock = blws + "\"markers\": [\n" + blws + "]\n"
    return markerBlock

# Produces instructions to make a grid (ncol by nrow) of maps according to the specified parameters:
#   gridPars contains a mapRect and ncol, nrow, baseName for the sections, and baseType for the map type (map or satellite)
#   runBlockParamList is a list of RunBlockParams 
def getInstructions( gridPars, runBlockParamList ):
    blws = "    "
    instructions = "// Instructions file for region " + gridPars.baseName + "\n"
    instructions += "{\n"
    instructions += blws + "\"regions\": [\n"
    
    regionsList = partitionMap( gridPars.mapRect, gridPars.ncol, gridPars.nrow )
    
    counter = 0
    for y in range( len(regionsList) ):   # for each row
        for x in range( len( regionsList[y] ) ): 
            regName = gridPars.baseName + str( counter )
            curRegionParams = RegionParams( gridPars.baseType, regName, regionsList[y][x].swCorner, regionsList[y][x].neCorner, "" )
            instructions += getRegionBlock( curRegionParams )
            if ( x < len( regionsList[y] ) - 1 ) or (y < len(regionsList) - 1):
                instructions += ",\n"
            else:
                instructions += "\n"
            counter = counter + 1
    instructions += blws + "],\n"
    
    # Now write the run block
    instructions += blws + "\"runs\": [\n"

    for i in range (len(runBlockParamList)):
        instructions += getRunBlock( runBlockParamList[i] )
        if (i < len(runBlockParamList)-1):
            instructions += ",\n"
        else:
            instructions += "\n"
    instructions += blws + "],\n"
             
    instructions += getMarkerBlock()
    instructions += "}"
    
    return instructions
    
# Write a set of instructions files to make a report (booklet type)
#   basename_summaryMaps.json: Makes the overall summary maps, list of LISAs sorted by amplitude.
#   basename_tiles_maps.json: Makes the maps for the zoomed-in sections 
#   basename_tiles_sat.json: Makes the satellite views for the zoomed-in sections
# This is intended for for use during development only. 
# If ncol or nrow are zero, try to determine them automatically (not yet available)
#   RegionParams = nameTuple( 'RegionParams', ['baseType', 'name', 'swCorner', 'neCorner', 'comments'] )
#   GridParams = namedtuple( 'GridParams', ['mapRect', 'ncol', 'nrow', 'baseName', 'baseType'] )
def writeReportInstructionsFiles( basename, analyzer, gridPars, minRunParamsList ):   

    # Default Colors
    bubbleColor = "#00FFFF"        # Cyan
    wedgeColor = "#FFFF00"         # Yellow
    nightSwathColor = "#00FF00"    # Green
    daySwathColor = "#FFFF00"      # Yellow

    runParamsList = []
    for i in range ( len(minRunParamsList) ):
        runParamsList.append( RunBlockParams( analyzer, 
                                minRunParamsList[i].startEtm, 
                                minRunParamsList[i].endEtm,
                                bubbleColor, 
                                wedgeColor, 
                                "None", 
                                minRunParamsList[i].minAmpl, 
                                minRunParamsList[i].exclRadius, 
                                minRunParamsList[i].stabClass,
                                ""
                            )    
        )  

    # Make the summary/overview map  
    summaryMapGridPars = GridParams( gridPars.mapRect, 1, 1, basename, "map")
    summaryMapInstructions = getInstructions( summaryMapGridPars, runParamsList )
    #print summaryMapInstructions
    
    # Make the satellite/overview map
    summarySatGridPars = GridParams( gridPars.mapRect, 1, 1, basename, "satellite")
    summarySatInstructions = getInstructions( summarySatGridPars, runParamsList )    
    
    # Make the swath map: Use different colors for day vs. night
    runParamsSwathList = []
    for i in range ( len(minRunParamsList) ):
        swathColor = nightSwathColor
        if ( minRunParamsList[i].stabClass < "D" ):
            swathColor = daySwathColor
        runParamsSwathList.append(  RunBlockParams( analyzer, 
                                    minRunParamsList[i].startEtm, 
                                    minRunParamsList[i].endEtm,
                                    "None", 
                                    "None", 
                                    swathColor, 
                                    minRunParamsList[i].minAmpl, 
                                    minRunParamsList[i].exclRadius, 
                                    minRunParamsList[i].stabClass,
                                    ""
                                )    
        )      
    summarySwathPars = GridParams( gridPars.mapRect, 1, 1, basename, "satellite")
    summarySwathInstructions = getInstructions( summarySatGridPars, runParamsSwathList )    
    #print summarySwathInstructions
        
    #Make the grid google maps
    mapGridPars = GridParams( gridPars.mapRect, gridPars.ncol, gridPars.nrow, basename, "map")   
    mapGridInstructions = getInstructions( mapGridPars, runParamsList )
    
    #Make the grid satellite maps
    satGridPars = GridParams( gridPars.mapRect, gridPars.ncol, gridPars.nrow, basename, "satellite")   
    satGridInstructions = getInstructions( satGridPars, runParamsList )

    #Write the instructions to files
    sum_map_fn = basename + "_summary_map.json"
    sum_sat_fn = basename + "_summary_sat.json"
    sum_swath_fn = basename + "_summary_swath.json"
    grid_map_fn = basename + "_grid_map.json"
    grid_sat_fn = basename + "_grid_sat.json"    
    
    fp_sum_map = file(sum_map_fn,"wb")
    fp_sum_map.write(summaryMapInstructions) 
    fp_sum_map.close()
  
    fp_sum_sat = file(sum_sat_fn,"wb")
    fp_sum_sat.write(summarySatInstructions) 
    fp_sum_sat.close()  
    
    fp_sum_swath = file(sum_swath_fn,"wb")
    fp_sum_swath.write(summarySwathInstructions) 
    fp_sum_swath.close()      
    
    fp_grid_map = file(grid_map_fn,"wb")
    fp_grid_map.write(mapGridInstructions) 
    fp_grid_map.close()      

    fp_grid_sat = file(grid_sat_fn,"wb")
    fp_grid_sat.write(satGridInstructions) 
    fp_grid_sat.close()     

if __name__ == "__main__":    
    print "\nPicarro Surveyor Report Booklet Generation -- Command Line Interface\n"
    print "Copyright (c) 2012 Picarro, Inc., All Rights Reserved.\n\n"
    print "Please answer the following questions and I will generate instructions files for batchReport.exe . . .\n\n"
    areaName = raw_input("Name of survey area? (e.g. \"CompanyArea1\" no spaces, please): ")
    analyzer = raw_input("Name of analyzer? (e.g. \"FCDS2010\"): ")
    writeReportInstructionsFiles (areaName, analyzer)