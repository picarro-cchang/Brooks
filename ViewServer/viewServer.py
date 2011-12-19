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

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

SCALE = 300.0
OFFSET = 1.85
LINE_COLOR = "7f00ffff"
POLY_COLOR = "7f00ff00"

app = Flask(__name__)
app.config.from_object(__name__)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]
changeIni = os.path.join(appDir,'MobileKit.ini')

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
        kml = """<?xml version="1.0" encoding="UTF-8"?>
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
</kml>""" % (long,lat,range-altitude/cos(tilt*DTR),tilt,heading,altitude)
        response = make_response(kml)
        response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        return response
    except:
        print traceback.format_exc()
        return emptyResponse()
        
@app.route('/updateData')
def updateData():
    global SCALE, OFFSET, LINE_COLOR, POLY_COLOR
    cookie = {}
    clearClientData = False
    
    try:
        if 'lastPos' in request.values:
            result = service.getData({'startPos':int(request.values['lastPos']),'varList':'["CH4","GPS_ABS_LAT","GPS_ABS_LONG"]'})
        else:
            result = service.getData({'varList':'["CH4","GPS_ABS_LAT","GPS_ABS_LONG"]'})
            
        filename = request.values.get('filename','')
        lastPos = result['lastPos']
        CH4 = result['CH4']
        long = result['GPS_ABS_LONG']
        lat = result['GPS_ABS_LAT']
        cookie['filename'] = result['filename']
        if filename != result['filename']:
            clearClientData = True
        
        if os.path.exists(changeIni):
            try:
                ini = ConfigObj(changeIni)
                if 'SETTINGS' in ini:
                    settings = ini['SETTINGS']
                    SCALE = float(settings.get('scale',SCALE))
                    OFFSET = float(settings.get('offset',OFFSET))
                    LINE_COLOR = settings.get('line_color',LINE_COLOR)
                    POLY_COLOR = settings.get('poly_color',POLY_COLOR)
                    restart = int(settings.get('restart',0))
                    if restart: 
                        service.restartDatalog({})
                        print "Restarting Data Log"
            except:
                print traceback.format_exc()
                print "Error processing .ini file"
            finally:
                os.remove(changeIni)
            clearClientData = True
            
        kmlPrefix = ""
        data = []
        data2 = []
        if clearClientData:
            kmlPrefix = """
<Delete>
    <Folder targetId="multi1">
    </Folder>
    <Folder targetId="multi2">
    </Folder>
</Delete>
<Create>
    <Document targetId="baseDoc">
        <name>Select Concentrations to Display</name>
        <Folder id="multi1">
            <name>Methane Concentration</name>
            <Style id="poly1">
                <LineStyle>
                    <color>%s</color>
                    <width>4</width>
                </LineStyle>
                <PolyStyle>
                    <color>%s</color>
                </PolyStyle>
            </Style>
        </Folder>
        <Folder id="multi2">
            <name>Hydrogen Sulphide Concentration</name>
            <Style id="poly2">
                <LineStyle>
                    <color>%s</color>
                    <width>4</width>
                </LineStyle>
                <PolyStyle>
                    <color>%s</color>
                </PolyStyle>
            </Style>
        </Folder>
    </Document>
</Create>""" % (LINE_COLOR, POLY_COLOR, "7fff0000", "7fff0000"
)
        else:
            cookie["lastPos"] = "%s" % lastPos
            for ch4,lat,long in zip(CH4,lat,long):
                data.append("%.5f,%.5f,%.0f" % (long,lat,SCALE*(ch4-OFFSET)))
                data2.append("%.5f,%.5f,%.0f" % (long,lat,0.5*SCALE*(ch4-OFFSET)))
        
        # Convert the cookie dictionary into a string
        cookie = Markup.escape("&".join(["%s=%s" % (k,cookie[k]) for k in cookie]))
        
        kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<NetworkLinkControl>
    <Update>
        <targetHref>http://localhost:5100/static/base.kml</targetHref>
        %s
        <Create>
            <Folder targetId="multi1">
                <name>Methane Concentration</name>
                <visibility>1</visibility>
                <Placemark>
                    <name>Methane Concentration</name>
                    <styleUrl>#poly1</styleUrl>
                    <LineString>
                        <extrude>1</extrude>
                        <tessellate>1</tessellate>
                        <altitudeMode>relativeToGround</altitudeMode>
                        <coordinates>
                            %s
                        </coordinates>
                     </LineString>
                </Placemark>
            </Folder>
            <Folder targetId="multi2">
                <name>Hydrogen Sulphide Concentration</name>
                <visibility>1</visibility>
                <Placemark>
                    <name>Hydrogen Sulphide Concentration</name>
                    <styleUrl>#poly2</styleUrl>
                    <LineString>
                        <extrude>1</extrude>
                        <tessellate>1</tessellate>
                        <altitudeMode>relativeToGround</altitudeMode>
                        <coordinates>
                            %s
                        </coordinates>
                     </LineString>
                </Placemark>
            </Folder>
        </Create>
    </Update>
    <cookie>%s</cookie>
</NetworkLinkControl>
</kml>""" % (kmlPrefix, "\n".join(data), "\n".join(data2), cookie)
        response = make_response(kml)
        response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        return response
    except:
        print traceback.format_exc()
        return emptyResponse()
    
if __name__ == '__main__':
    import getopt
    shortOpts = 'a:'
    longOpts = []
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    addr = '127.0.0.1'
    if "-a" in options:
        addr = options["-a"]

    # Connect to the analyzer rest server
    service = RestProxy('%s:5000' % addr.strip())
    app.run(host='127.0.0.1',port=5100)
    