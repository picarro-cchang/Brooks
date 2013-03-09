'''
  Json2Kml.py
  
  Utility to convert swaths and paths from JSON instructions file into KML format
  
  D. Steele (dsteele@picarro.com)
   
  Revisions:
        -- 11/15/2012 Initial Version
'''

import sys
import numpy as np
from numpy import log, pi, sin, cos, sqrt, arctan, arctan2, tan
import geohash
try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple    
try:
    import json
except:
    import simplejson as json
    
LatLng = namedtuple( 'LatLng', ["lat", "lng"] )

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

def pathDistance( path ):
    '''Calculate the total distance along a path (defined by a list of LatLng)'''
    d = 0.
    for i in range( len(path)-1 ): 
        d += distVincenty( path[i].lat, path[i].lng, path[i+1].lat, path[i+1].lng )
    return d    
    
class Json2Kml(object):
    def __init__(self, vers='1.0', encod='UTF-8', url='http://www.opengis.net/kml/2.2'):
        '''Convert JSON representations of PATHs and SWATHs into KML'''
        self.version = str(vers)
        self.encoding = str(encod)
        self.xmlns = str(url)
        
        # default style values
        self.lineColor = 'FF000000'
        self.lineWidth = '2'
        self.polyColor = '50780A14'            
        
    def GetStyleBlock(self, styleName, indent=""):
        kml =  indent + '<Style id="' + styleName + '">\n'
        kml += indent + '<LineStyle>\n'
        kml += indent + '  <color>' + self.lineColor + '</color>\n'
        kml += indent + '  <width>' + self.lineWidth + '</width>\n'
        kml += indent + '</LineStyle>\n'
        kml += indent + '<PolyStyle>\n'
        kml += indent + '  <color>' + self.polyColor + '</color>\n'
        kml += indent + '  <outline>0</outline>\n'
        kml += indent + '  <fill>1</fill>\n'
        kml += indent + '  <colorMode>normal</colorMode>\n'
        kml += indent + '</PolyStyle>\n'
        kml += indent + '</Style>\n'
        return kml
        
    def GetKMLHeader(self, name="Picarro Surveyor"):
        kml = '<?xml version="' + self.version + '" encoding="' + self.encoding + '"?>\n'
        kml += '<kml xmlns="' + self.xmlns + '">\n'
        kml += '  <Document>\n'
        kml += '    <name>' + name + '</name>\n'
        return kml
        
    def GetKMLFooter(self):
        kml = '  </Document>\n'
        kml += '</kml>'
        return kml
        
    def ListOfPolygons2KMLBlock( self, polyList, indent="" ):
        '''Take a list of polygons and return the appropriate KML block'''
        '''Polygon coordinates must be listed in counter-clockwise order (no checking is done!)'''
        if (len(polyList) == 0):
            print "List of polys was empty"
            return ""
        kml = ""
        for list in polyList:
            kml += indent + '<Polygon>\n'
            kml += indent + '  <extrude>0</extrude>\n'
            # kml += indent + '  <altitudeMode>clampToGround</altitudeMode>\n'
            kml += indent + '  <outerBoundaryIs>\n'
            kml += indent + '    <LinearRing>\n'
            kml += indent + '      <coordinates>\n'
            for i in range(len(list)):   
                kml += indent + '          ' + str(list[i].lng) + ',' + str(list[i].lat) + ',0.\n'
            kml += indent + '      </coordinates>\n'
            kml += indent + '    </LinearRing>\n'
            kml += indent + '  </outerBoundaryIs>\n'
            kml += indent + '</Polygon>\n'
        return kml
        
    def GetKMLLineSegment( self, pl, indent="" ):
        '''Take a PolyLine and return a KML LineSegment'''
        ls = indent + '<LineString>\n'
        ls += indent + '  <extrude>0</extrude>\n'
        ls += indent + '  <tessellate>1</tessellate>\n'
        ls += indent + '  <altitudeMode>clampToGround</altitudeMode>\n'
        ls += indent + '  <coordinates>\n'
        for i in range(len(pl)):
            ls += indent + '      ' + str(pl[i].lng) + ',' + str(pl[i].lat) + ',0.\n'
        ls += indent + '  </coordinates>\n'
        ls += indent + '</LineString>\n'
        return ls

    def GetKMLOpenPlacemark( self, name, desc, styleUrl, indent="" ):
        kml = indent + '<Placemark>\n'
        kml += indent + '  <name>' + name + '</name>\n'
        kml += indent + '  <description>' + desc + '</description>\n'
        kml += indent + '  <styleUrl>#' + styleUrl + '</styleUrl>\n'
        return kml
        
    def GetKMLClosePlacemark( self, indent="" ):
        kml = indent + '</Placemark>\n'
        return kml
               
    def isClockwise( self, cooList ):
        '''check if a list of coordinates containing at least three elements is clockwise or not'''
        if len(cooList) < 3:
            return False
        a = np.array( [ cooList[1].lng- cooList[0].lng, cooList[1].lat - cooList[0].lat ] ) 
        b = np.array( [ cooList[2].lng - cooList[1].lng, cooList[2].lat - cooList[1].lat ] )
        if ( np.cross(a, b) < 0. ):
            return True
        else:
            return False       
        
    def allUnique( self, list ):
        for i in range(len(list)-1):
            for j in range(i+1, len(list)-1):
                if ((list[i].lng == list[j].lng) and (list[i].lat == list[j].lat)):
                    print i, j
                    return False
        return True
        
    def FOV2ListOfPoly( self, path, edge ):
        '''Take the two lists of coordinates ([ LatLng ]) and return a [] of polygons'''
        '''List coordinates in counter-clockwise order'''
        '''Skip any polygons that do not have four unique points'''
        polys = []   # A list of lists of LatLng
        for p in range(len(path) - 1):
            cooList = []
            cooList.append(path[p])
            cooList.append(path[p+1])
            cooList.append(edge[p+1])
            cooList.append(edge[p])
            cooList.append(path[p])
            if self.isClockwise(cooList):
                cooList.reverse()
            #if self.allUnique(cooList):
            polys.append( cooList )
        return polys
             
    def ExtractSwaths( self, jsn ):
        '''Extract the FOV portion of the JSON and return two lists of PolyLines'''    
        paths = []    # elements are lists of LatLng
        edges = []
        swaths = jsn["SWATHS"]
        # print "There are ", str(len(swaths)), " swaths in the file"
        for i in range(len(swaths)):
            # print "   Swath ", str(i), " has ", str(len(swaths[i]["PATH"]))," points and is from run ", str(swaths[i]["RUN"]), " and survey ", str(swaths[i]["SURVEY"])
            pathHash = swaths[i]["PATH"]
            edgeHash = swaths[i]["EDGE"]
            pathPoly = []
            edgePoly = []
            for j in range(len(pathHash)):
                pathPoly.append( LatLng( geohash.decode(pathHash[j])[0], geohash.decode(pathHash[j])[1] ) )
                edgePoly.append( LatLng( geohash.decode(edgeHash[j])[0], geohash.decode(edgeHash[j])[1] ) )
            paths.append( pathPoly  )
            edges.append( edgePoly  )
        return paths, edges
        
    def ExtractPaths( self, jsn, type=0):
        '''Extract all paths of the specified type. 
            type:   0 -> active path
                    1 -> doing isotopic analysis
                    2 -> inactive
                    3 -> bad instrument'''
        paths = []  
        pth = jsn["PATHS"]
        for i in range(len(pth)):
        #for i in range(3):
            if ( pth[i]["TYPE"] == type ):
                pathHash = pth[i]["PATH"]
                pathPoly = []
                print "Path has ", str(len(pathHash)), " points"
                for j in range(len(pathHash)):
                    pathPoly.append( LatLng( geohash.decode( pathHash[j] )[0], geohash.decode( pathHash[j] )[1] ) )
                paths.append( pathPoly )
        return paths
        
    def ConvertFileToKMLString( self, json_fn, dumpPath=True, dumpSwath=True ):
        json_str = open( json_fn ).read()
        jsn = json.loads( json_str )
        edge1List, edge2List = self.ExtractSwaths( jsn ) # returns two lists of lists of LatLng
        polyList = []    # this will also be a list of lists
        for i in range(len(edge1List)):
            polyList.append( self.FOV2ListOfPoly( edge1List[i], edge2List[i] ) )
        pathList = self.ExtractPaths( jsn, 0 )
        # Calculate path distances
        print "Path Distances [km]: "
        i = 0
        totalDist = 0.
        for path in pathList:
            pathDist = pathDistance(path)
            print "  Path ", i, pathDist/1000.
            totalDist += pathDist/1000.
            i += 1
        print "  TOTAL: ", totalDist, " km"
        kml = self.GetKMLHeader()
        styleName = "SurveyorStyle"
        kml += self.GetStyleBlock(styleName, "      ")
        if (dumpPath):
            kml += self.GetKMLOpenPlacemark( "Survey Path", "", styleName, "      " )
            kml += '        <MultiGeometry>\n'  
            for i in range(len(pathList)):
                kml += self.GetKMLLineSegment( pathList[i], "        " )
            kml += '        </MultiGeometry>\n'  
            kml += self.GetKMLClosePlacemark("      ")    
        if (dumpSwath):
            kml += self.GetKMLOpenPlacemark( "Field of View", "", styleName, "      ")     
            kml += '        <MultiGeometry>\n' 
            for i in range(len(polyList)):
                kml += self.ListOfPolygons2KMLBlock( polyList[i], "          " ) 
            kml += '        </MultiGeometry>\n'
            kml += self.GetKMLClosePlacemark("      ")
        kml += self.GetKMLFooter()
        return kml
    
    def ConvertJSONFileToKMLFile( self, json_fn, kml_fn ):
        kml1 = self.ConvertFileToKMLString( json_fn, True, False )
        kml2 = self.ConvertFileToKMLString( json_fn, False, True )
        fn1 = kml_fn + "_path.kml"
        fn2 = kml_fn + "_swath.kml"
        print "Writing to files ", fn1, " ", fn2
        outFile1 = open( fn1, "wb" )
        outFile1.write( kml1 )
        outFile1.close()
        outFile2 = open( fn2, "wb" )
        outFile2.write( kml2 )
        outFile2.close()       
        
        
if __name__ == "__main__":
    print "JSON to KML Conversion Utility"
    print "Copyright (c) 2012 Picarro, Inc., All Rights Reserved.\n"
    converter = Json2Kml()
    # kml = converter.ConvertFileToKMLString( "pathData.0.json" )
    # print kml
    if len(sys.argv) >= 2:
        json_fn = sys.argv[1]
        xml_fn = sys.argv[2]
    else:
        json_fn = raw_input("Name of JSON file to read? ")
        xml_fn = raw_input("Name of XML file to write? ")
    converter.ConvertJSONFileToKMLFile( json_fn, xml_fn )