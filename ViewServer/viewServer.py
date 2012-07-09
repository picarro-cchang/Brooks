"""
 viewSerer is an HTTP server that is run on a computer which is used with Google Earth to view data stored on P3

 It supports two main functions
  /updateView: Used to retrieve the location of the vehicle
  /updateData: Used to retrieve the path traversed and the concentration of the target species along the path
 An additional function /base is provided to define the style of various visual elements used by Google Earth
 
"""

import sys
sys.path.append(r"C:\Picarro\G2000\ReportGen\ViewServer")
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
import time
import traceback
import urllib

from SecureRestProxy import SecureRestProxy

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# configuration
DEBUG = False
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
DEFAULT_CONFIG_NAME = "viewServer.ini"

class Settings(object):
    def __init__(self):
        self.viewParamsList = []
        self.viewParamsAsDir = {}
        self.alogName = None
        self.changeIni = os.path.join(appDir,'MobileKit.ini')
        self.baseIni = os.path.join(appDir,'MobileKit_inactive.ini') 
        self.service = None
        self.refreshNeeded = False
        self.primeView = False
        
    def setupFromConfig(self):
        # There is a ViewParams object for each species (section name other than SETTINGS) in the INI file
        ini = ConfigObj(self.baseIni)
        for secName in ini:
            if secName == 'SETTINGS':
                self.alogName = ini[secName].get('alog',self.alogName)
                continue
            scale = float(ini[secName].get('scale',1.0))
            offset = float(ini[secName].get('offset',0.0))
            line_color = ini[secName].get('line_color',"7fffffff")
            poly_color = ini[secName].get('poly_color',"7fffffff")
            enabled = int(ini[secName].get('enabled',1))
            vp = ViewParams(secName,scale,offset,line_color,poly_color,enabled)
            self.viewParamsList.append(vp)
            self.viewParamsAsDir[secName] = vp
            
    def updateFromConfig(self):
        """This is run to update the settings when a new configuration file is present"""
        ini = ConfigObj(self.changeIni)
        self.settingsDict = {}
        for secName in ini:
            if secName == 'SETTINGS': 
                self.settingsDict = dict(ini[secName])
                continue
            settings = ini[secName]
            viewParams = self.viewParamsAsDir[secName]
            def update(key,conv):
                # Update the value of the specified key in viewParamsList, 
                #  if this is in the ini file
                #  Return True iff this changes the value of the key
                if key in settings:
                    if getattr(viewParams,key) != conv(settings[key]):
                        setattr(viewParams,key,conv(settings[key]))
                        return True
                return False
            self.refreshNeeded = update('scale',float) or self.refreshNeeded
            self.refreshNeeded = update('offset',float) or self.refreshNeeded
            self.refreshNeeded = update('line_color',str) or self.refreshNeeded
            self.refreshNeeded = update('poly_color',str) or self.refreshNeeded
            if 'enabled' in settings:
                viewParams.enabled = int(settings['enabled'])

    def refreshDone(self):
        """This is called after the path has been cleared on Google Earth"""
        self.refreshNeeded = False

    def processChangeIni(self):
        """Handle a change file, which updates the settings and potentially executes various actions
            on a prime-view analyzer"""
        if os.path.exists(self.changeIni):
            try:
                self.updateFromConfig()
                self.alogName = self.settingsDict.get('alog',self.alogName)
                if self.primeView:
                    restart = int(self.settingsDict.get('restart',0))
                    self.refreshNeeded = True
                    if restart: 
                        SETTINGS.service.restartDatalog({})
                        print "Restarting Data Log"
                    shutdown = int(settingsDict.get('shutdown',0))
                    if shutdown: 
                        SETTINGS.service.shutdownAnalyzer({})
                        print "Shutting down analyzer"
            except:
                print traceback.format_exc()
                print "Error processing .ini file"
            finally:
                os.remove(self.changeIni)


SETTINGS = Settings()

def url_join(*args):
    """Join any arbitrary strings into a forward-slash delimited list.
    Do not strip leading / from first element, nor trailing / from last element."""
    if len(args) == 0:
        return ""

    if len(args) == 1:
        return str(args[0])

    else:
        args = [str(arg).replace("\\", "/") for arg in args]

        work = [args[0]]
        for arg in args[1:]:
            if arg.startswith("/"):
                work.append(arg[1:])
            else:
                work.append(arg)

        joined = reduce(os.path.join, work)

    return joined.replace("\\", "/")
    
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
            
    
app = Flask(__name__)
app.config.from_object(__name__)

class RestCallError(Exception):
    pass
    
class RestProxy(object):
    # Proxy to make a rest call to a server
    def __init__(self,host,baseUrl):
        self.host = host
        self.baseUrl = baseUrl
    # Attributes are mapped to a function which performs
    #  a GET request to host/rest/attrName
    def __getattr__(self,attrName):
        def dispatch(argsDict):
            url = "%s/%s" % (self.baseUrl,attrName)
            print self.host, "GET","%s?%s" % (url,urllib.urlencode(argsDict))
            conn = httplib.HTTPConnection(self.host)
            try:
                conn.request("GET","%s?%s" % (url,urllib.urlencode(argsDict)))
                r = conn.getresponse()
                if not r.reason == 'OK':
                    raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
                else:
                    return json.loads(r.read()).get("result",{})
            finally:
                conn.close()
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
    for i,viewParams in enumerate(SETTINGS.viewParamsList):
        blockStrings.append(BLOCK % (i,viewParams.speciesName,i,viewParams.line_color,viewParams.poly_color))

    kml = BASE % ("\n".join(blockStrings),)
    response = make_response(kml)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    return response

VIEW = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <LookAt>
          %s
          %s
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
    SETTINGS.processChangeIni()
    if range<0 or range>20000:
        range = 2000.0
        tilt = 45
        heading = 0
        altitude = 0
    try:
        varList = ["GPS_ABS_LONG","GPS_ABS_LAT","GPS_FIT"]
        params = {'startPos':-2,'varList':json.dumps(varList)}
        params['alog'] = SETTINGS.alogName
        try:
            result = SETTINGS.service.getData(params)
            if result['GPS_FIT'][-1] > 0:
                longStr = "<longitude>%s</longitude>" % result['GPS_ABS_LONG'][-1]
                latStr = "<latitude>%s</latitude>" % result['GPS_ABS_LAT'][-1]
        except:    
            longStr = ""
            latStr = ""
        kml = VIEW % (longStr,latStr,range-altitude/cos(tilt*DTR),tilt,heading,altitude)
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
    # Note: The cookie that is passed back in the KML is used to make the request for the next time that the
    #  network link is called. This allows us to retrieve from the last point fetched.
    cookie = {}
    clearClientData = False
    SETTINGS.processChangeIni()
    
    try:
        lastFilename = request.values.get('filename','')
        lastPos = 1
        varList = ["GPS_ABS_LAT","GPS_ABS_LONG"]
        for viewParams in SETTINGS.viewParamsList:
            varList.append(viewParams.speciesName)
        params = {'varList':json.dumps(varList)}
        if 'lastPos' in request.values: 
            lastPos = int(request.values['lastPos'])
        params['startPos'] = lastPos
        params['alog'] = SETTINGS.alogName

        try:
            result = SETTINGS.service.getData(params)
            thisFilename = result['filename']
            if thisFilename != lastFilename: 
                print "******************* LOG CHANGED **************************"
                SETTINGS.refreshNeeded = True
            lastPos = result.get('lastPos',1)
            cookie['filename'] = thisFilename
            data = [[] for viewParams in SETTINGS.viewParamsList]
            try:
                concs = [result[viewParams.speciesName] for viewParams in SETTINGS.viewParamsList]
                longs = result['GPS_ABS_LONG']
                lats = result['GPS_ABS_LAT']
            except:
                concs = []
                longs = []
                lats = []
        except:
            if 'filename' in request.values: cookie['filename'] = request.values['filename']            
            concs = []
            longs = []
            lats = []
        
        # Generate the KML file for Google Earth
        kmlPrefix = ""
        kmlData = ""
        if SETTINGS.refreshNeeded:
            delStrings = []
            createStrings = []
            for i,viewParams in enumerate(SETTINGS.viewParamsList):
                delStrings.append("""<Folder targetId="multi%d"></Folder>""" % (i,))
                createStrings.append(BLOCK % (i,viewParams.speciesName,i,viewParams.line_color,viewParams.poly_color))
            kmlPrefix = UPDATE  % ("\n".join(delStrings), "\n".join(createStrings))
            SETTINGS.refreshDone()
            lastPos = 1
        else:
            dataStrings = []
            for i,viewParams in enumerate(SETTINGS.viewParamsList):
                placeMark = ""
                if len(lats)>1:
                    for conc,lat,long in zip(concs[i],lats,longs):
                        data[i].append("%.5f,%.5f,%.0f" % (long,lat,viewParams.scale*(conc-viewParams.offset)))
                    placeMark = PLACEMARK % (viewParams.speciesName,i,"\n".join(data[i]))
                dataStrings.append(CONCFOLDER % (i,viewParams.enabled,placeMark))
                kmlData = """<Create>%s</Create>""" % ("\n".join(dataStrings))
        cookie["lastPos"] = "%s" % lastPos
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

-h, --help   : Print this help.
-c, --config : Specify a config file.
-a           : Specify IP address fror analyzerServer (local mode)
-u           : Specify path to p3 server (remote mode, insecure)
-s           : Use secure mode. The following options must then be specified
--csp-url    : URL with customer service prefix (without leading https://)
--ticket-url : URL from which to get ticket (without leading https://)
--identity   : Identity string
--sys        : System string
--svc        : Service string (e.g. gdu)
Note: Options -a, -u and -s are mutually exclusive
"""

def PrintUsage():
    print HELP_STRING

    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:a:u:s", 
                                       ["help","csp-url=","ticket-url=","identity=","sys=","svc=","config="])
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
        
    if "--config" in options:
        configFile = options["--config"]
        print "Config file specified at command line: %s" % configFile

    checkOpts = 0
    checkOpts += 1 if "-a" in options else 0;
    checkOpts += 1 if "-u" in options else 0;
    checkOpts += 1 if "-s" in options else 0;

    if checkOpts != 1:
        raise ValueError("Exactly one of -a, -u or -s must be specified")
    
    return configFile, options

def main():
    configFile,options = HandleCommandSwitches()
    configFile = os.path.abspath(configFile)
    configPath = os.path.split(configFile)[0]
    #print "configFile, options = ", configFile, options
    
    addr = '127.0.0.1'
    url = None
    if "-a" in options:
        addr = options["-a"]
    if "-u" in options:
        url = options["-u"]
        addr = None
        
    ini = ConfigObj(configFile)
    if 'Main' in ini:
        SETTINGS.baseIni = os.path.join(configPath,ini['Main'].get('inactiveIniPath',SETTINGS.baseIni))
        SETTINGS.changeIni = os.path.join(configPath,ini['Main'].get('activeIniPath',SETTINGS.changeIni))
    SETTINGS.setupFromConfig()
    
    # Connect to the analyzer rest server
    
    if "-a" in options:
        SETTINGS.service = RestProxy('%s:5000' % addr.strip(),"/rest")
        SETTINGS.primeView = True
    elif "-u" in options:
        urlcomp = url.split("/",1)
        host = urlcomp[0]
        restUrl = "/"
        if len(urlcomp)>1: restUrl += urlcomp[1]
        SETTINGS.service = RestProxy(host,restUrl)
    elif "-s" in options:
        csp_url = "https://" + options["--csp-url"]
        ticket_url = "https://" + options["--ticket-url"]
        svc = options["--svc"]
        identity = options["--identity"]
        psys = options["--sys"]
        SETTINGS.service = SecureRestProxy(csp_url, svc, ticket_url, identity, psys)
        print "service started"
    app.run(host='127.0.0.1',port=5100)
    
if __name__ == '__main__':
    main()
    