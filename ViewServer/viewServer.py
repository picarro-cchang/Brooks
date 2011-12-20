from flask import Flask, Markup
from flask import make_response, render_template, request
try:
    import simplejson as json
except:
    import json
from functools import wraps
from configobj import ConfigObj
import httplib
from math import cos, pi
import os
import sys
import time
import traceback
import urllib

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]
changeIni = os.path.join(appDir,'MobileKit.ini')
baseIni = os.path.join(appDir,'MobileKit_inactive.ini') 

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
DEFAULT_CONFIG_NAME = "viewServer.ini"

viewParamsList = []
viewParamsAsDir = {}

class ViewParams(object):
    def __init__(self,speciesName,scale,offset,line_color,poly_color,enabled=True):
        self.speciesName = speciesName
        self.scale = scale
        self.offset = offset
        self.line_color = line_color
        self.poly_color = poly_color
        self.enabled = enabled
    def __repr__(self):
        return "<%s, scale: %s, offset: %s, line_color: %s, poly_color: %s, enabled: %s>" % (self.speciesName, 
            self.scale, self.offset, self.line_color, self.poly_color, self.enabled)
            
def setupFromConfig(baseIni):
    ini = ConfigObj(baseIni)
    for secName in ini:
        if secName == 'SETTINGS': continue
        scale = float(ini[secName].get('scale',1.0))
        offset = float(ini[secName].get('offset',0.0))
        line_color = ini[secName].get('line_color',"7fffffff")
        poly_color = ini[secName].get('poly_color',"7fffffff")
        enabled = int(ini[secName].get('enabled',1))
        viewParamsList.append(ViewParams(secName,scale,offset,line_color,poly_color,enabled))
        viewParamsAsDir[secName] = viewParamsList[-1]
        
def updateFromConfig(changeIni):
    ini = ConfigObj(changeIni)
    refreshNeeded = False
    settingsDict = {}
    for secName in ini:
        if secName == 'SETTINGS': 
            settingsDict = dict(ini[secName])
            continue
        settings = ini[secName]
        viewParams = viewParamsAsDir[secName]
        def update(key,conv):
            # Update the value of the specified key in viewParamsList, 
            #  if this is in the ini file
            #  Return True iff this changes the value of the key
            if key in settings:
                if getattr(viewParams,key) != conv(settings[key]):
                    setattr(viewParams,key,conv(settings[key]))
                    return True
            return False
        refreshNeeded = update('scale',float) | refreshNeeded
        refreshNeeded = update('offset',float) | refreshNeeded
        refreshNeeded = update('line_color',str) | refreshNeeded
        refreshNeeded = update('poly_color',str) | refreshNeeded
        if 'enabled' in settings:
            viewParams.enabled = int(settings['enabled'])
    return refreshNeeded, settingsDict
    
app = Flask(__name__)
app.config.from_object(__name__)

class RestCallError(Exception):
    pass
    
class RestProxy(object):
    # Proxy to make a rest call to a server
    def __init__(self,host):
        self.host = host
    # Attributes are mapped to a function which performs
    #  a GET request to host/rest/attrName
    def __getattr__(self,attrName):
        def dispatch(argsDict):
            url = "rest/%s" % attrName
            conn = httplib.HTTPConnection(self.host)
            conn.request("GET","%s?%s" % (url,urllib.urlencode(argsDict)))
            r = conn.getresponse()
            if not r.reason == 'OK':
                raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
            else:
                return json.loads(r.read()).get("result",{})
        return dispatch
        
def emptyResponse():
    empty_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
  </Document>
</kml>"""
    response = make_response(empty_kml)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    return response

BLOCK = """<Folder id="multi%d">
    <name>%s Concentration</name>
    <Style id="poly%d">
        <LineStyle>
            <color>%s</color>
            <width>4</width>
        </LineStyle>
        <PolyStyle>
            <color>%s</color>
        </PolyStyle>
    </Style>
</Folder>"""

BASE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document id="baseDoc">
        <name>Select Concentrations to Display</name>
        %s
    </Document>
</kml>"""

@app.route('/base')
def base():
    blockStrings = []
    for i,viewParams in enumerate(viewParamsList):
        blockStrings.append(BLOCK % (i,viewParams.speciesName,i,viewParams.line_color,viewParams.poly_color))

    kml = BASE % ("\n".join(blockStrings),)
    response = make_response(kml)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    return response

VIEW = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <LookAt>
          <longitude>%s</longitude>
          <latitude>%s</latitude>
          <range>%s</range>
          <tilt>%s</tilt>
          <heading>%s</heading>
          <altitude>%s</altitude>
    </LookAt>
</Document>
</kml>"""
    
@app.route('/updateView')
def updateView():
    DTR = pi/180.0
    range = float(request.values['range'])
    tilt = float(request.values['tilt'])
    heading = float(request.values['heading'])
    altitude = float(request.values['altitude'])
    if range<0 or range>20000:
        range = 2000.0
        tilt = 45
        heading = 0
        altitude = 0
    try:
        result = service.getData({'startPos':-2,'varList':'["GPS_ABS_LONG","GPS_ABS_LAT"]'})
        long = result['GPS_ABS_LONG'][-1]
        lat = result['GPS_ABS_LAT'][-1]
        kml = VIEW % (long,lat,range-altitude/cos(tilt*DTR),tilt,heading,altitude)
        response = make_response(kml)
        response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        return response
    except:
        print traceback.format_exc()
        return emptyResponse()

UPDATE = """<Delete>
    %s
</Delete>
<Create>
    <Document targetId="baseDoc">
        <name>Select Concentrations to Display</name>
        %s
    </Document>
</Create>"""

PLACEMARK = """<Placemark>
    <name>%s Concentration</name>
    <styleUrl>#poly%d</styleUrl>
    <LineString>
        <extrude>1</extrude>
        <tessellate>1</tessellate>
        <altitudeMode>relativeToGround</altitudeMode>
        <coordinates>
            %s
        </coordinates>
     </LineString>
</Placemark>"""

CONCFOLDER = """<Folder targetId="multi%d">
    <visibility>%s</visibility>
    %s
</Folder>"""

NETLINKCONTROL = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<NetworkLinkControl>
    <Update>
        <targetHref>http://localhost:5100/base</targetHref>
        %s
        %s
    </Update>
    <cookie>%s</cookie>
</NetworkLinkControl>
</kml>"""

@app.route('/updateData')
def updateData():
    cookie = {}
    clearClientData = False
    
    try:
        varList = ["GPS_ABS_LAT","GPS_ABS_LONG"]
        for viewParams in viewParamsList:
            varList.append(viewParams.speciesName)
        if 'lastPos' in request.values:
            result = service.getData({'startPos':int(request.values['lastPos']),'varList':json.dumps(varList)})
        else:
            result = service.getData({'varList':json.dumps(varList)})
            
        filename = request.values.get('filename','')
        lastPos = result['lastPos']
        concs = [result[viewParams.speciesName] for viewParams in viewParamsList]
        longs = result['GPS_ABS_LONG']
        lats = result['GPS_ABS_LAT']
        data = [[] for viewParams in viewParamsList]
        cookie['filename'] = result['filename']
        if filename != result['filename']:
            clearClientData = True
        
        if os.path.exists(changeIni):
            refreshNeeded = False
            try:
                refreshNeeded,settingsDict = updateFromConfig(changeIni)
                restart = int(settingsDict.get('restart',0))
                if restart: 
                    service.restartDatalog({})
                    print "Restarting Data Log"
                shutdown = int(settingsDict.get('shutdown',0))
                if shutdown: 
                    service.shutdownAnalyzer({})
                    print "Shutting down analyzer"
            except:
                print traceback.format_exc()
                print "Error processing .ini file"
            finally:
                os.remove(changeIni)
            if refreshNeeded or restart: 
                clearClientData = True
        
        kmlPrefix = ""
        kmlData = ""
        if clearClientData:
            delStrings = []
            createStrings = []
            for i,viewParams in enumerate(viewParamsList):
                delStrings.append("""<Folder targetId="multi%d"></Folder>""" % (i,))
                createStrings.append(BLOCK % (i,viewParams.speciesName,i,viewParams.line_color,viewParams.poly_color))
            kmlPrefix = UPDATE  % ("\n".join(delStrings), "\n".join(createStrings))
        else:
            cookie["lastPos"] = "%s" % lastPos
            dataStrings = []
            
            for i,viewParams in enumerate(viewParamsList):
                placeMark = ""
                if len(lats)>1:
                    for conc,lat,long in zip(concs[i],lats,longs):
                        data[i].append("%.5f,%.5f,%.0f" % (long,lat,viewParams.scale*(conc-viewParams.offset)))
                    placeMark = PLACEMARK % (viewParams.speciesName,i,"\n".join(data[i]))
                dataStrings.append(CONCFOLDER % (i,viewParams.enabled,placeMark))
                kmlData = """<Create>%s</Create>""" % ("\n".join(dataStrings))
        # Convert the cookie dictionary into a string
        cookie = Markup.escape("&".join(["%s=%s" % (k,cookie[k]) for k in cookie]))
        
        kml = NETLINKCONTROL  % (kmlPrefix, kmlData, cookie)
        response = make_response(kml)
        response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        return response
    except:
        print traceback.format_exc()
        return emptyResponse()
        
HELP_STRING = \
"""

viewServer.py [-h] [-c <FILENAME>] [-a <IPADDR>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.
-a         : Specify IP address fror analyzerServer
"""

def PrintUsage():
    print HELP_STRING

    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:a:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(appPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        
    return configFile, options

if __name__ == '__main__':
    configFile,options = HandleCommandSwitches()
    configFile = os.path.abspath(configFile)
    configPath = os.path.split(configFile)[0]
    
    addr = '127.0.0.1'
    if "-a" in options:
        addr = options["-a"]

    ini = ConfigObj(configFile)
    if 'Main' in ini:
        baseIni = os.path.join(configPath,ini['Main'].get('inactiveIniPath',baseIni))
        changeIni = os.path.join(configPath,ini['Main'].get('activeIniPath',changeIni))
    
    setupFromConfig(baseIni)
    
    # Connect to the analyzer rest server
    service = RestProxy('%s:5000' % addr.strip())
    app.run(host='127.0.0.1',port=5100)
    