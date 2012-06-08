import calendar
import cStringIO
from collections import namedtuple
from flask import Flask, Markup
from flask import make_response, redirect, render_template, request, Response, url_for
import getFromP3 as gp3
from glob import glob
import hashlib
try:
    import json
except:
    import simplejson as json
import math
import os
from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
import sys
import time
import traceback
import urllib2
import urllib
from werkzeug import secure_filename
from ReportGenSupport import ReportGen, ReportStatus, GoogleMap, SurveyorLayers
from ReportGenSupport import LayerFilenamesGetter, CompositeMapMaker

from peaksReport import testPage

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# Make an initial call to strptime in the main thread to avoid problems with calling it in a 
#  child thread
time.strptime("2012-04-01T09:50:00","%Y-%m-%dT%H:%M:%S")

fname = "platBoundaries.json"
fp = open(fname,"rb")
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

def unix_line_endings(str):
    return str.replace('\r\n', '\n').replace('\r', '\n')
    
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
    params = urllib.urlencode(request.values)
    mapUrl = '/rest/getComposite?%s' % params
    peaksTableFileName = os.path.join(REPORTROOT,'%s.peaksMap.%d.html'%(ticket,region))
    if os.path.exists(peaksTableFileName):
        fp = file(peaksTableFileName,'rb')
        peaksTable = fp.read()
        fp.close()
    else:
        peaksTable = ""
    return render_template('report.html',peaksTable=peaksTable,mapUrl=mapUrl)

@app.route('/rest/getComposite')
def getComposite():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT,'%s.compositeMap.%d.png'%(ticket,region))
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
    
@app.route('/makeInstructions')
def makeInstructions():
    ticket = request.values.get('ticket','')
    contents = ""
    fname = request.values.get('fname','')
    if ticket:
        instrFname  = os.path.join(REPORTROOT,"%s.json" % ticket)
        if os.path.exists(instrFname):
            fp = open(instrFname,"rb")
            contents = fp.read()
            fp.close()
    return render_template('makeInstructions.html',ticket=ticket,contents=contents,fname=fname)
    
@app.route('/')
def index():
    return makeInstructions()
    
@app.route('/test')
def test():
    return render_template('test.html',html="\n".join([line for line in testPage()]))
    
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5200,debug=True,threaded=True)
