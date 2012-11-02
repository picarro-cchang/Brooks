'''
Flask server for Picarro Surveyor Report Generation

Created on Jun 9, 2012

@author: stan
'''
from collections import namedtuple
from flask import Flask, abort
from flask import make_response, render_template, request
import hashlib
import json
import math
import multiprocessing as mp
import optparse
import os
import shutil
import sys
import time
import traceback
import urllib
from werkzeug import secure_filename
import ReportGenSupportNew as rgs
from ReportCommon import getTicket, PROJECT_SUBMISSION_PORT
import ProjectSupport as PP
from Host.Common.configobj import ConfigObj
import zmq

if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(os.path.abspath(appPath))[0]

# Make an initial call to strptime in the main thread to avoid problems with calling it in a
#  child thread
time.strptime("2012-04-01T09:50:00", "%Y-%m-%dT%H:%M:%S")

configFile = os.path.splitext(appPath)[0] + ".ini"
config = ConfigObj(configFile)
if "Plats" in config:
    PLAT_BOUNDARIES = os.path.join(appDir, config["Plats"]["plat_corners"])
else:
    PLAT_BOUNDARIES = "platBoundaries.json"

try:
    with open(PLAT_BOUNDARIES, "rb") as fp:
        platBoundaries = json.loads(fp.read())
except IOError:
    platBoundaries = {}

RTD = 180.0 / math.pi
DTR = math.pi / 180.0
EARTH_RADIUS = 6378100

MapParams = namedtuple("MapParams", ["minLng", "minLat", "maxLng",
                       "maxLat", "nx", "ny", "padX", "padY"])

# configuration
DEBUG = False
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
STATICROOT = os.path.join(appDir, 'static')
REPORTROOT = os.path.join(appDir, 'static', 'ReportGen')
LAYERBASEURL = '/static/ReportGen/'  # Need trailing /

app = Flask(__name__)
app.config.from_object(__name__)
context = zmq.Context()


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def unix_line_endings(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')


@app.route('/rest/validate', methods=['GET', 'POST'])
def validate():
    # Checks the validity of the secure hash at the top of a Picarro JSON file
    data = request.values.get('contents')
    try:
        sig, rest = data.split('\n', 1)
        secHash = hashlib.md5('Picarro Surveyor' + rest).hexdigest()
        if sig != '// ' + secHash:
            raise ValueError('Invalid hash')
        data = {'contents': rest}
    except:
        data = {'error': traceback.format_exc()}
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/rest/submitProject')
def submitProject():
    # Services upload of instructions for generating report
    contents = request.values.get('contents')
    # Pass directory in which report files are to be placed and the
    #  contents of the instruction file
    if contents:
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://127.0.0.1:%d" % PROJECT_SUBMISSION_PORT)
        # Try for up to 5 s for submitting project
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN | zmq.POLLOUT)
        evts = dict(poller.poll(1000))
        if evts.get(socket) == zmq.POLLOUT:
            socket.send(json.dumps({"msg": "PROJECT",
                        "reportRoot": REPORTROOT, "contents": contents}))
            evts = dict(poller.poll(5000))
            if evts.get(socket) == zmq.POLLIN:
                data = json.loads(socket.recv())
            else:
                data = {'error':
                    "No reply: Check project manager has been started"}
        else:
            data = {'error': "Cannot send project: Check ZMQ installation"}
        socket.close()
    else:
        data = {'error': "Missing contents in submitProject"}
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

@app.route('/rest/getComposite')
def getComposite():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(
        REPORTROOT, '%s/compositeMap.%d.png' % (ticket, region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        fname = os.path.join(STATICROOT, 'errorIcon.png')
        when = time.time()
    fp = open(fname, 'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response


@app.route('/rest/getCSV')
def getCSV():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT, '%s/peaksMap.%d.csv' % (ticket, region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname, 'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename="%s_region_%d.csv"' % (ticket, region + 1)
    response.headers['Last-Modified'] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response


@app.route('/rest/getXML')
def getXML():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT, '%s/peaksMap.%d.xml' % (ticket, region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname, 'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'application/vnd.ms-excel'
    response.headers['Content-Disposition'] = 'attachment; filename="%s_region_%d.xml"' % (ticket, region + 1)
    response.headers['Last-Modified'] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response


@app.route('/rest/getPDF')
def getPDF():
    ticket = request.values.get('ticket')
    region = int(request.values.get('region'))
    fname = os.path.join(REPORTROOT, '%s/report.%d.pdf' % (ticket, region))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname, 'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename="%s_region_%d.pdf"' % (ticket, region + 1)
    response.headers['Last-Modified'] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response


@app.route('/rest/getZIP')
def getZIP():
    ticket = request.values.get('ticket')
    fname = os.path.join(REPORTROOT, '%s/archive.zip' % (ticket,))
    if os.path.exists(fname):
        when = os.path.getmtime(fname)
    else:
        abort(404)
    fp = open(fname, 'rb')
    response = make_response(fp.read())
    fp.close()
    response.headers['Content-Type'] = 'application/zip'
    response.headers[
        'Content-Disposition'] = 'attachment; filename="%s.zip"' % (ticket,)
    response.headers['Last-Modified'] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response


@app.route('/rest/autocompletePlat')
def autocompletePlat():
    term = request.values.get('query').upper()
    result = sorted([k for k in platBoundaries.keys() if k.upper().startswith(term)]) + sorted([k for k in platBoundaries.keys() if term in k.upper() and not(k.upper().startswith(term))])
    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/rest/platCorners')
def get_plat_corners():
    plat = request.values.get('plat', '').upper().strip()
    result = {}
    if plat in platBoundaries:
        minLng, minLat, maxLng, maxLat = platBoundaries[plat]
        result = {"MIN_LONG": minLng, "MAX_LONG": maxLng,
            "MIN_LAT": minLat, "MAX_LAT": maxLat, "PLAT": plat}
    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/rest/download', methods=['GET', 'POST'])
def download():
    filename = request.values.get('filename', '')
    content = request.values.get('content', '')
    if not content or not filename:
        return
    filename = secure_filename(filename)
    content = unix_line_endings(content)
    # Prepend a secure hash to the content
    secHash = hashlib.md5('Picarro Surveyor' + content).hexdigest()
    response = make_response('// ' + secHash + '\n' + content)
    response.headers['Cache-Control'] = ''
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers[
        'Content-Disposition'] = 'attachment; filename="' + filename + '"'
    return response


@app.route('/rest/remove', methods=['GET'])
def remove():
    """Get rid of all files associated with the specified ticket.
    TODO: Stop any running processes associated with this ticket first"""
    ticket = request.values.get('ticket', '')
    dirName = os.path.join(REPORTROOT, "%s" % ticket)
    result = {'dirName': dirName}
    if os.path.exists(dirName):
        try:
            shutil.rmtree(dirName)
            result['result'] = "Report directory removed"
        except:
            result['error'] = traceback.format_exc()
    else:
        result['result'] = "Report directory not found"
    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/rest/getReportEnv', methods=['GET'])
def getReportEnv():
    """Get details of the environment in which the report server is running"""
    result = dict(
        REPORTROOT=REPORTROOT, STATICROOT=STATICROOT, APIKEY=rgs.APIKEY,
                  WKHTMLTOPDF=rgs.WKHTMLTOPDF, IMGCONVERT=rgs.IMGCONVERT)
    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/report')
def report():
    ticket = request.values.get('ticket', '')
    contents = ""
    fname = request.values.get('fname', '')
    if ticket:
        instrFname = os.path.join(REPORTROOT, "%s/json" % ticket)
        if os.path.exists(instrFname):
            fp = open(instrFname, "rb")
            contents = fp.read()
            fp.close()
    return render_template('makeInstructions.html', ticket=ticket, contents=contents, fname=fname)


@app.route('/')
def index():
    return report()


@app.route('/shutdown', methods=["POST"])
def shutdown():
    # This is intended for testing purposes only. Should be disabled in production code.
    shutdown_server()
    return "Server shutting down"


@app.route('/test')
def test():
    return render_template('testTable.html')


def main():
    global REPORTROOT
    usage = "%prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-r", dest="reportRoot", help="Specify root directory for report files", default=REPORTROOT)
    parser.add_option("--no-pmstart", dest="startPm", help="Do not start project manager", action="store_false", default=True)
    options, args = parser.parse_args()
    REPORTROOT = options.reportRoot
    if options.startPm:
        rmProcess = mp.Process(
            target=PP.ResourceManager(REPORTROOT, os.getpid()).run)
        psProcess = mp.Process(
            target=PP.ProjectManagerInterface(REPORTROOT, os.getpid()).run)
        rmProcess.start()
        psProcess.start()
    app.run(host='0.0.0.0', port=5200, debug=DEBUG, threaded=True)
    if options.startPm:
        psProcess.terminate()
        rmProcess.terminate()
        psProcess.join()
        rmProcess.join()

if __name__ == "__main__":
    main()
