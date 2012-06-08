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

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

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
IMAGEROOT = os.path.join(appDir,'images')
STATICROOT = os.path.join(appDir,'static')
REPORTROOT = os.path.join(appDir,'static/ReportGen')
LAYERBASEURL = '/static/ReportGen/' # Need trailing /
imagesAvailable = {}

UPLOAD_FOLDER = os.path.join(appDir,'static')
ALLOWED_EXTENSIONS = set(['png'])

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Images are stored in images/<imageName>/<epochTime>.png. This allows multiple versions of each image to be kept.
#
# The call /rest/getImagePath returns the full path of the images directory. This is useful for the artist to know where 
#  to place the image files.
#
# When the server starts up, it goes through the subdirectories of images. It constructs a dictionary called imagesAvailable 
# such that imagesAvailable[<imageName>] is a sorted list of the epoch times of the images available called imageName.
#
# When an artist generates a new version of an image, it calls the server function rest/newImage?name=<imageName>&time=<epochTime>. 
# The server updates imagesAvailable and deletes any old versions of that image until at most two remain. Note that the list in 
# imagesAvailable must be updated before the file is removed from the directory.
#
# When a consumer wishes to request an image, it first calls rest/mostRecentImage?name=<imageName>. The server returns the epoch 
#  time of the most recent image with that name, by looking up imagesAvailable. The consumer can decide whether to call 
#  rest/getImage?name=<imageName>, which returns the most recent image then available. Note that this may be more recent than that 
#  sent back to the consumer, but this is not a problem, since all that the #consumer does with the time it is given is to decide 
#  whether to load a more recent image.

for dirpath,dirnames,filenames in os.walk(IMAGEROOT):
    pngfiles = sorted([int(f[:-4]) for f in filenames if f.endswith('.png')])
    if pngfiles:
        name = os.path.split(dirpath)[-1]
        for f in pngfiles[:-2]:
            os.remove(os.path.join(dirpath,'%d.png'%f))
        imagesAvailable[name] = pngfiles[-2:]

def unix_line_endings(str):
    return str.replace('\r\n', '\n').replace('\r', '\n')
                
@app.route('/map')
def map():
    return render_template('showmap.html')
    
@app.route('/dateTime')
def dateTime():
    return render_template('datetimeEntryBasic.html')

@app.route('/sprites')
def sprites():
    return render_template('sprites.html')

@app.route('/bar')
def bar():
    return render_template('progressbar.html')

@app.route('/wait')
def wait():    
    duration = float(request.values.get('duration',10))
    time.sleep(duration)
    return "Responding after %s seconds" % (duration,)
    
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

@app.route('/showLayers')
def showLayers():
    ticket = request.values.get('ticket')
    return render_template('showLayers.html',ticket=ticket)
    
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

@app.route('/rest/pathLayer',methods=['GET'])
def pathLayer():
    startEtmDef = calendar.timegm(time.strptime("2012-04-01T09:50:00","%Y-%m-%dT%H:%M:%S"))
    endEtmDef   = calendar.timegm(time.strptime("2012-04-01T12:00:00","%Y-%m-%dT%H:%M:%S"))
    analyzerDef = 'FCDS2006'
    startEtm = float(request.values.get('startEtm',startEtmDef))
    endEtm = float(request.values.get('endEtm',endEtmDef))
    anz = request.values.get('analyzer',analyzerDef)
    plat = request.values.get('plat','2465F1')
    mp = GoogleMap().getPlatParams(plat)
    sl = SurveyorLayers(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
    response = make_response(sl.makePath(anz,startEtm,endEtm))
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time()))
    return response
    
@app.route('/rest/markerLayer',methods=['GET'])
def markerLayer():
    startEtmDef = calendar.timegm(time.strptime("2012-04-01T09:50:00","%Y-%m-%dT%H:%M:%S"))
    endEtmDef   = calendar.timegm(time.strptime("2012-04-01T12:00:00","%Y-%m-%dT%H:%M:%S"))
    analyzerDef = 'FCDS2006'
    minAmplDef = 0.10
    maxAmplDef = 1000000.0
    startEtm = float(request.values.get('startEtm',startEtmDef))
    endEtm = float(request.values.get('endEtm',endEtmDef))
    minAmpl = float(request.values.get('minAmpl',minAmplDef))
    maxAmpl = float(request.values.get('maxAmpl',maxAmplDef))
    anz = request.values.get('analyzer',analyzerDef)
    plat = request.values.get('plat','2465F1')
    mp = GoogleMap().getPlatParams(plat)
    sl = SurveyorLayers(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
    response = make_response(sl.makeMarkers(anz,startEtm,endEtm,minAmpl,maxAmpl,True,True))
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time()))
    return response
    
@app.route('/rest/plat')
def plat():
    plat = request.values.get('plat','2465F1')
    satellite = int(request.values.get('satellite',0))
    image,mp = GoogleMap().getPlat(plat,satellite)
    response = make_response(image)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time()))
    return response
    
@app.route('/rest/mapImage')
def map_image():
    # Default is plat 2465F1
    minLat = float(request.values.get('minLat',38.6838))
    minLng = float(request.values.get('minLng',-121.4556))
    maxLat = float(request.values.get('maxLat',38.6927))
    maxLng = float(request.values.get('maxLng',-121.4474))
    meanLat = 0.5*(minLat + maxLat)
    meanLng = 0.5*(minLng + maxLng)
    Xp = maxLng-minLng
    Yp = maxLat-minLat
    # Find the largest zoom consistent with these limits
    cosLat = math.cos(meanLat*DTR)
    zoom = int(math.floor(math.log(min((360.0*640)/(256*Xp),(360.0*640*cosLat)/(256*Yp)))/math.log(2.0)))
    # Find the number of pixels in each direction
    fac = (256.0/360.0)*2**zoom
    mx = int(math.ceil(fac*Xp))
    my = int(math.ceil(fac*Yp/cosLat))
    response = make_response(GoogleMap().getMap(meanLat,meanLng,zoom,mx,my,scale=2,satellite=True))
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time()))
    return response
    
@app.route('/rest/platBoundaries')
def get_plat_boundaries():
    result = [[k]+platBoundaries[k] for k in sorted(platBoundaries.keys())]
    if 'callback' in request.values:
        response = make_response(request.values['callback'] + '(' + json.dumps({"aaData":result}) + ')')
    else:
        response = make_response(json.dumps({"aaData":result}))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/rest/autocompletePlat')
def autocompletePlat():
    term = request.values.get('query').upper()
    result = sorted([k for k in platBoundaries.keys() if k.upper().startswith(term)]) + sorted([k for k in platBoundaries.keys() if term in k.upper() and not(k.upper().startswith(term))])
    if 'callback' in request.values:
        response =  make_response(request.values['callback'] + '(' + json.dumps(result) + ')')
    else:
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
    
@app.route('/show_plats',methods=['GET'])
def show_plats():
    return render_template('show_plats.html')

def allowed_file(filename,allowed=ALLOWED_EXTENSIONS):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in allowed

@app.route('/show_peaks',methods=['GET'])
def show_peaks():
    startEtmDef = calendar.timegm(time.strptime("2012-04-01T09:50:00","%Y-%m-%dT%H:%M:%S"))
    endEtmDef   = calendar.timegm(time.strptime("2012-04-01T15:00:00","%Y-%m-%dT%H:%M:%S"))
    analyzerDef = 'FCDS2006'
    startEtm = float(request.values.get('startEtm',startEtmDef))
    endEtm = float(request.values.get('endEtm',endEtmDef))
    anz = request.values.get('analyzer',analyzerDef)
    p3 = gp3.P3_Accessor(anz)
    headings = None
    rows = []
    for m in p3.genAnzLog("peaks")(startEtm=startEtm,endEtm=endEtm):
        if headings is None:
            headings = sorted(m.data.keys())
        rows.append([m.data[h] for h in headings])    
    return render_template('show_peaks.html',peak_table=dict(headings=headings,rows=rows))
           
@app.route('/upload',methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return redirect(url_for('uploaded_file',filename=filename))
    return render_template('upload.html')

@app.route('/print',methods=['GET','POST'])
def print_file():
    if request.method == 'POST':
        file = request.files['file']
        print file.filename
        if file and allowed_file(file.filename,["js","py"]):
            code = file.read()
            lexer = guess_lexer_for_filename(file.filename,code)
            formatter = HtmlFormatter(linenos=True)
            result = highlight(code, lexer, formatter)
            file.close()
            print result
            return render_template('pygments.html',body=result)
    return render_template('upload.html')

@app.route('/report',methods=['GET','POST'])
def report():
    if request.method == 'POST':
        file = request.files['file']
        print file.filename
        if file and allowed_file(file.filename,["js","py"]):
            code = file.read()
            lexer = guess_lexer_for_filename(file.filename,code)
            formatter = HtmlFormatter(linenos=True)
            result = highlight(code, lexer, formatter)
            file.close()
            print result
            return render_template('pygments.html',body=result)
    return render_template('report.html')

@app.route('/makeInstructions')
def makeInstructions():
    return render_template('makeInstructions.html')
    
@app.route('/uploaded_file')
def uploaded_file():
    filename = request.values['filename']
    fp = open(os.path.join(app.config['UPLOAD_FOLDER'],filename),'rb')
    try:
        response = make_response(fp.read())
        when = time.time()
    finally:
        fp.close()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response
    
@app.route('/')
def index():
    return render_template('graph.html')

def getImagePathEx(params):
    try:
        return dict(path=os.path.abspath(IMAGEROOT))
    except:
        return dict(error=traceback.format_exc())
    
@app.route('/rest/getImagePath')
def getImagePath():
    result = getImagePathEx(request.values)
    if 'callback' in request.values:
        response = make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        response = make_response(json.dumps({"result":result}))
    response.headers['Content-Type'] = 'application/json'
    return response
    
def newImageEx(params):
    try:
        name = params['name'].strip()
        when = int(params['when'].strip())
        fname = os.path.join(IMAGEROOT,'%s/%d.png'%(name,when))
        if not os.path.exists(fname):
            raise ValueError('Image file %s not found on server' % fname)
        if name not in imagesAvailable: imagesAvailable[name] = []
        imagesAvailable[name].append(when)
        for f in imagesAvailable[name][:-2]:
            try:
                os.remove(os.path.join(IMAGEROOT,'%s/%d.png'%(name,f)))
            except:
                pass
        imagesAvailable[name][:] = imagesAvailable[name][-2:]
        return dict(available=imagesAvailable[name])
    except:
        return dict(error=traceback.format_exc())
    
@app.route('/rest/newImage')
def newImage():
    result = newImageEx(request.values)
    if 'callback' in request.values:
        response = make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        response = make_response(json.dumps({"result":result}))
    response.headers['Content-Type'] = 'application/json'
    return response

def mostRecentImageEx(params):
    try:
        name = params['name'].strip()
        return dict(when=imagesAvailable[name][-1])
    except:
        return dict(when=None)
        
@app.route('/rest/mostRecentImage')
def mostRecentImage():
    result = mostRecentImageEx(request.values)
    if 'callback' in request.values:
        response = make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        response = make_response(json.dumps({"result":result}))
    response.headers['Content-Type'] = 'application/json'
    return response
        
@app.route('/rest/getImage')
def getImage():
    try:
        name = request.values['name'].strip()
        when = imagesAvailable[name][-1]
        fname = os.path.join(IMAGEROOT,'%s/%d.png'%(name,when))
        fp = file(fname,'rb')
        try:
            response = make_response(fp.read())
        finally:
            fp.close()
    except:
        fname = os.path.join(STATICROOT,'errorIcon.png')
        fp = file(fname,'rb')
        try:
            response = make_response(fp.read())
            when = time.time()
        finally:
            fp.close()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response
    
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5200,debug=True,threaded=True)
