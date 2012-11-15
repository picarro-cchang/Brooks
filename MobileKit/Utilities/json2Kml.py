'''
  Json2Kml.py
  
  Utility to convert swaths and paths from JSON instructions file into KML format
  
  D. Steele (dsteele@picarro.com)
   
  Revisions:
        -- 11/15/2012 Initial Version
'''

import sys
import numpy as np
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
        for i in range(len(swaths)):
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
        
    def ExtractPaths( self, jsn ):
        paths = []  # elements are PolyLine
        pth = jsn["PATHS"]
        for i in range(len(pth)):
            pathHash = pth[i]["PATH"]
            pathPoly = []
            for j in range(len(pathHash)):
                pathPoly.append( LatLng( geohash.decode( pathHash[j] )[0], geohash.decode( pathHash[j] )[1] ) )
            paths.append( pathPoly )
        return paths
        
    def ConvertFileToKMLString( self, json_fn ):
        json_str = open( json_fn ).read()
        jsn = json.loads( json_str )
        edge1List, edge2List = self.ExtractSwaths( jsn ) # returns two lists of lists of LatLng
        polyList = []    # this will also be a list of lists
        for i in range(len(edge1List)):
            polyList.append( self.FOV2ListOfPoly( edge1List[i], edge2List[i] ) )
        kml = self.GetKMLHeader()
        styleName = "SurveyorStyle"
        kml += self.GetStyleBlock(styleName, "      ")
        kml += self.GetKMLOpenPlacemark( "Survey Path", "", styleName, "      " )
        kml += '        <MultiGeometry>\n'  
        for i in range(len(pathList)-1):
            kml += self.GetKMLLineSegment( pathList[i], "        " )
        kml += '        </MultiGeometry>\n'  
        kml += self.GetKMLClosePlacemark("      ")
        kml += self.GetKMLOpenPlacemark( "Field of View", "", styleName, "      ")  
        kml += '        <MultiGeometry>\n'        
        for i in range(len(polyList)-1):
            kml += self.ListOfPolygons2KMLBlock( polyList[i], "          " ) 
        kml += '        </MultiGeometry>\n'
        kml += self.GetKMLClosePlacemark("      ")
        kml += self.GetKMLFooter()
        return kml
    
    def ConvertJSONFileToKMLFile( self, json_fn, kml_fn ):
        kml = self.ConvertFileToKMLString( json_fn )
        outFile = open( kml_fn, "wb" )
        outFile.write( kml )
        outFile.close()
        
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