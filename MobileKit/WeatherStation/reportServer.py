'''
Flask server for Picarro Surveyor Report Generation

Created on Jun 9, 2012

@author: stan
'''
try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple
from flask import Flask, abort
from flask import make_response, render_template, request
import hashlib
try:
    import json
except:
    import simplejson as json
import math
import os
import shutil
import sys
import time
import traceback
import urllib
from werkzeug import secure_filename
from ReportGenSupport import ReportGen, ReportStatus, getTicket
from ReportGenSupport import LayerFilenamesGetter, pretty_ticket
from ReportGenSupport import BubbleMaker
from Host.Common.configobj import ConfigObj

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# Make an initial call to strptime in the main thread to avoid problems with calling it in a 
#  child thread
time.strptime("2012-04-01T09:50:00","%Y-%m-%dT%H:%M:%S")

configFile = os.path.splitext(appPath)[0] + ".ini"
config = ConfigObj(configFile)
if "Plats" in config:
    PLAT_BOUNDARIES = os.path.join(appDir,config["Plats"]["plat_corners"])
else:
    PLAT_BOUNDARIES = "platBoundaries.json"
    
fp = open(PLAT_BOUNDARIES,"rb")
platBoundaries = json.loads(fp.read())
fp.close()

RTD = 180.0/math.pi
DTR = math.pi/180.0
EARTH_RADIUS = 6378100

MapParams = namedtuple("MapParams",["minLng","minLat","maxLng","maxLat","nx","ny","padX","padY"])

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
STATICROOT = os.path.join(appDir,'static')
REPORTROOT = os.path.join(appDir,'static/ReportGen')
LAYERBASEURL = '/static/ReportGen/' # Need trailing /

app = Flask(__name__)
app.config.from_object(__name__)

def unix_line_endings(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

@app.route('/rest/validate',methods=['GET','POST'])
def validate():
    # Checks the validity of the secure hash at the top of a Picarro JSON file
    data = request.values.get('contents')
    try:
        sig,rest = data.split('\n',1)
        secHash = hashlib.md5('Picarro Surveyor' + rest).hexdigest()
        if sig != '// ' + secHash:
            raise ValueError('Invalid hash')
        data = { 'contents':rest }
    except:
        data = { 'error':traceback.format_exc() }
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/rest/instrUpload')
def instrUpload():
    # Services upload of instructions for generating report
    contents = request.values.get('contents')
    # Pass directory in which report files are to be placed and the 
    #  contents of the instruction file
    ticket = ReportGen(REPORTROOT,contents).run()
    data = {'contents': contents, 'ticket':ticket}
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/rest/getReportStatus')
def getReportStatus():
    ticket = request.values.get('ticket')
    data = ReportStatus(REPORTROOT,ticket).run()
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/rest/getTicket')
def getReportTicket():
    contents = request.values.get('contents')
    data = {'ticket': getTicket(contents)}
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/rest/getLayerUrls')
def getLayerUrls():
    ticket = request.values.get('ticket')
    data = LayerFilenamesGetter(REPORTROOT,ticket).run()
    for d in data:
        data[d] = LAYERBASEURL + data[d]
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response
    
@app.route('/rest/getReport')
def getReport():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    name = request.values.get('name')
    params = urllib.urlencode(request.values)
    mapUrl = '/rest/getComposite?%s' % params
    pathFileName = os.path.join(REPORTROOT,'%s/pathMap.%d.html'%(ticket,region))
    if os.path.exists(pathFileName):
        fp = file(pathFileName,'rb')
        pathLogs = fp.read()
        fp.close()
    else:
        pathLogs = ""
    peaksTableFileName = os.path.join(REPORTROOT,'%s/peaksMap.%d.html'%(ticket,region))
    if os.path.exists(peaksTableFileName):
        fp = file(peaksTableFileName,'rb')
        peaksTable = fp.read()
        fp.close()
    else:
        peaksTable = ""
    markerTableFileName = os.path.join(REPORTROOT,'%s/markerMap.%d.html'%(ticket,region))
    if os.path.exists(markerTableFileName):
        fp = file(markerTableFileName,'rb')
        markerTable = fp.read()
        fp.close()
    else:
        markerTable = ""
    return render_template('report.html',peaksTable=peaksTable,markerTable=markerTable,
                           pathLogs=pathLogs,mapUrl=mapUrl,
                           name=name,region=region,prettyTicket=pretty_ticket(ticket))

@app.route('/rest/getComposite')
def getComposite():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT,'%s/compositeMap.%d.png'%(ticket,region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        fname = os.path.join(STATICROOT,'errorIcon.png')
        when = time.time()
    fp = open(fname,'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response

@app.route('/rest/getCSV')
def getCSV():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT,'%s/peaksMap.%d.csv'%(ticket,region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname,'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename="%s_region_%d.csv"' % (ticket,region+1)
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response
    
@app.route('/rest/getXML')
def getXML():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT,'%s/peaksMap.%d.xml'%(ticket,region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname,'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'application/vnd.ms-excel'
    response.headers['Content-Disposition'] = 'attachment; filename="%s_region_%d.xml"' % (ticket,region+1)
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response

@app.route('/rest/getPDF')
def getPDF():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT,'%s/report.%d.pdf'%(ticket,region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname,'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename="%s_region_%d.pdf"' % (ticket,region+1)
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response

@app.route('/rest/getZIP')
def getZIP():
    ticket = request.values.get('ticket')
    fname = os.path.join(REPORTROOT,'%s/archive.zip'%(ticket,))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        flask.abort(404)
    fp = open(fname,'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename="%s.zip"' % (ticket,)
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response

@app.route('/rest/autocompletePlat')
def autocompletePlat():
    term = request.values.get('query').upper()
    result = sorted([k for k in platBoundaries.keys() if k.upper().startswith(term)]) + sorted([k for k in platBoundaries.keys() if term in k.upper() and not(k.upper().startswith(term))])
    response =  make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response
    
@app.route('/rest/platCorners')
def get_plat_corners():
    plat = request.values.get('plat','').upper().strip()
    result = {}
    if plat in platBoundaries:
        minLng,minLat,maxLng,maxLat = platBoundaries[plat]
        result = {"MIN_LONG":minLng, "MAX_LONG":maxLng, "MIN_LAT":minLat, "MAX_LAT":maxLat, "PLAT":plat}
    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/rest/download',methods=['GET','POST'])
def download():
    filename = request.values.get('filename','')
    content =  request.values.get('content','')
    if not content or not filename: return
    filename = secure_filename(filename)
    content = unix_line_endings(content)
    # Prepend a secure hash to the content
    secHash = hashlib.md5('Picarro Surveyor' + content).hexdigest()
    response = make_response('// ' + secHash + '\n' + content)
    response.headers['Cache-Control'] = ''
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename="' + filename + '"'
    return response

@app.route('/rest/remove',methods=['GET'])
def remove():
    """Get rid of all files associated with the specified ticket.
    TODO: Stop any running processes associated with this ticket first"""
    ticket = request.values.get('ticket','')
    dirName = os.path.join(REPORTROOT,"%s" % ticket)
    result = { 'dirName': dirName }
    if os.path.exists(dirName):
        try:
            shutil.rmtree(dirName)
            result['result'] =  "Report directory removed"
        except:
            result['error'] = traceback.format_exc()
    else:
        result['result'] =  "Report directory not found"
    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response
    
@app.route('/report')
def report():
    ticket = request.values.get('ticket','')
    contents = ""
    fname = request.values.get('fname','')
    if ticket:
        instrFname  = os.path.join(REPORTROOT,"%s/json" % ticket)
        if os.path.exists(instrFname):
            fp = open(instrFname,"rb")
            contents = fp.read()
            fp.close()
    return render_template('makeInstructions.html',ticket=ticket,contents=contents,fname=fname)
    
@app.route('/')
def index():
    return report()
    
@app.route('/test')
def test():
    return render_template('testTable.html');

@app.route('/bubble')
def bubble():
    # Bubble of size n is of size 36n+1 x 65n+1 pixels
    size = float(request.values.get('size',2.0))
    marker = BubbleMaker().getMarker(size)
    response = make_response(marker)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    return response
        
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5200,debug=DEBUG,threaded=True)
