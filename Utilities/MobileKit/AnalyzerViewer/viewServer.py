from flask import Flask, Markup
from flask import make_response, render_template, request
from jsonrpc import JSONRPCHandler, Fault
from jsonrpcutils import Proxy
from functools import wraps
from configobj import ConfigObj
import glob
from math import cos, pi
import os
import sys
import time
import traceback

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

# Provide JSON RPC service for mapping software
handler = JSONRPCHandler('jsonrpc')
handler.connect(app,'/jsonrpc')

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]
changeIni = os.path.join(appDir,'MobileKit.ini')

class JSON_Remote_Procedure_Error(RuntimeError):
    pass

def rpcWrapper(func):
    """This decorator wraps a remote procedure call so that any exceptions from the procedure
    raise a JSON_Remote_Procedure_Error and has a traceback."""
    @wraps(func)
    def JSON_RPC_wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except:
            type,value = sys.exc_info()[:2]
            raise JSON_Remote_Procedure_Error, "\n%s" % (traceback.format_exc(),)
    return JSON_RPC_wrapper

def emptyResponse():
    empty_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
  </Document>
</kml>"""
    response = make_response(empty_kml)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    return response

@app.route('/maps')
def maps():
    threshold = float(request.values.get('threshold',2.5))
    return render_template('maps.html',threshold=threshold)
    
@app.route('/updateView')
def updateView():
    DTR = pi/180.0
    range = float(request.values['range'])
    tilt = float(request.values['tilt'])
    heading = float(request.values['heading'])
    altitude = float(request.values['altitude'])
    if range>20000:
        range = 2000.0
        tilt = 45
        heading = 0
        altitude = 0
    try:
        result = service.getPos()
        long = result['GPS_ABS_LONG']
        lat = result['GPS_ABS_LAT']
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

@handler.register
@rpcWrapper
def getPath(params):
    result = service.getLastDataRows(params)
    epochTime, long, lat, ch4 = result["EPOCH_TIME"], result["GPS_ABS_LONG"], result["GPS_ABS_LAT"], result["CH4"]
    peakPos = ch4.index(max(ch4))
    timeStrings = [time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) for t in epochTime]
    return(dict(long=long,lat=lat,ch4=ch4,timeStrings=timeStrings,peakPos=peakPos))
        
@app.route('/updateData')
def updateData():
    global SCALE, OFFSET, LINE_COLOR, POLY_COLOR
    cookie = {}
    clearClientData = False
    
    try:
        if 'lastPos' in request.values:
            result = service.getData({'startPos':int(request.values['lastPos'])})
        else:
            result = service.getData({})
            
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
        if clearClientData:
            kmlPrefix = """
<Delete>
    <Folder targetId="multi1">
    </Folder>
</Delete>
<Create>
    <Document targetId="baseDoc">
        <Folder id="multi1">
            <Style id="yellowLineGreenPoly">
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
</Create>""" % (LINE_COLOR, POLY_COLOR)
        else:
            cookie["lastPos"] = "%s" % lastPos
            for ch4,lat,long in zip(CH4,lat,long):
                data.append("%.5f,%.5f,%.0f" % (long,lat,SCALE*(ch4-OFFSET)))
        
        # Convert the cookie dictionary into a string
        cookie = Markup.escape("&".join(["%s=%s" % (k,cookie[k]) for k in cookie]))
        
        kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<NetworkLinkControl>
    <Update>
        <targetHref>http://localhost:5100/static/base2.kml</targetHref>
        %s
        <Create>
            <Folder targetId="multi1">
                <Placemark>
                    <name>Methane Concentration</name>
                    <styleUrl>#yellowLineGreenPoly</styleUrl>
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
</kml>""" % (kmlPrefix, "\n".join(data), cookie)
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

    # Connect to the analyzer JSON RPC server
    service = Proxy('http://%s:5000/jsonrpc' % addr.strip())
    app.run(host='127.0.0.1',port=5100)
    