#!/usr/bin/python
"""
File Name: dummyServer.py
Purpose: Flask server to simulate a subset of PCubed functionality

File History:
    24-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from math import pi, sin
from flask import Flask
from flask import make_response, render_template, request
import json
from random import random
import time

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
PARAMS = {
    "fnm": 157,
    "dTime": 1.2,
    "histTime": 1200,
    "startTime": None,
    "systemStatus": 0,
    "carSpeed": "10.0 + 7.0*sin(0.001*t)",
    "windN": 3.0,
    "windE": 4.0,
    "eTimeByRow": [],
    "carSpeedByRow": [],
    "WLonByRow": [],
    "WLatByRow": [],
    "fnmByRow": [],
    "systemStatusByRow": [],
    "windNByRow": [],
    "windEByRow": [],    
}


app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/dummy')
def hello():
    return 'Dummy rest server'

@app.route('/stage/rest/sec/NONE/1.0/Admin')
def admin():
    print "Admin called"
    return make_response(json.dumps({"ticket":"1234567890"}))

@app.route('/stage/rest/gdu/1234567890/1.0/AnzMeta')
def anzmeta():
    print "AnzMeta called"
    req = request.values
    if req['qry'] == "byAnz" and req['doclist']:
        return make_response(json.dumps({"result" : {"ANALYZER" : ["DEMO2000", "DUMMY1", "DUMMY2", "DUMMY3"]}}))
    return make_response(json.dumps({"result":{}}))

@app.route('/stage/rest/gdu/1234567890/1.0/AnzLogMeta')
def anzlogmeta():
    print "AnzLogMeta called"
    req = request.values
    if req['qry'] == "byEpoch":
        if 'alog' in req:
            alog = req['alog']
            docmap = [{"EPOCH_TIME":1, "CAR_SPEED":2, "WS_WIND_LON":3, "WS_WIND_LAT":4, 
                       "FILENAME_nint":"fnm", "SYSTEM_STATUS":5, "WIND_N":6, "WIND_E":7}]
            fnm = [PARAMS["fnm"]]
            return make_response(json.dumps({"result" : {"FILENAME_nint": fnm, "docmap": docmap}}))
        elif 'anz' in req:
            analyzer = req['anz']
            return make_response(json.dumps({"result" : {"name": ["%s_20130101_130000_UserLog_Minimal.dat" % analyzer,
                                                                  "%s_20130105_140000_UserLog_Minimal.dat" % analyzer]}}))
    return make_response(json.dumps({"result":{}}))

@app.route('/stage/rest/gdu/1234567890/1.0/AnzLog')
def anzlog():
    print "AnzLog called"
    req = request.values
    assert req['qry'] == "byPos"
    startPos = int(req['startPos'])
    limit = int(req['limit'])
    fillLog()
    if startPos < len(PARAMS["eTimeByRow"]):
        epochTime = PARAMS["eTimeByRow"][startPos:startPos+limit]
        carSpeed = PARAMS["carSpeedByRow"][startPos:startPos+limit]
        wsWindLon = PARAMS["WLonByRow"][startPos:startPos+limit]
        wsWindLat = PARAMS["WLatByRow"][startPos:startPos+limit]
        fnm = PARAMS["fnmByRow"][startPos:startPos+limit]
        systemStatus = PARAMS["systemStatusByRow"][startPos:startPos+limit]
        windN = PARAMS["windNByRow"][startPos:startPos+limit]
        windE = PARAMS["windEByRow"][startPos:startPos+limit]
        row = range(startPos, startPos+len(epochTime))
        return make_response(json.dumps({"result":{
            "EPOCH_TIME":epochTime, "CAR_SPEED":carSpeed, "WS_WIND_LON":wsWindLon,
            "WS_WIND_LAT":wsWindLat, "FILENAME_nint":fnm, "SYSTEM_STATUS":systemStatus, 
            "WIND_N":windN, "WIND_E":windE, "row":row}}))
    else:
        return make_response(json.dumps({"result":{}}))

def fillLog():
    now = time.time()
    dTime = PARAMS["dTime"]
    if len(PARAMS["eTimeByRow"]) > 0:
        startTime = PARAMS["eTimeByRow"][-1] + dTime
    else:
        startTime = now - PARAMS["histTime"]
        PARAMS["startTime"] = startTime
    while startTime < now:
        PARAMS["eTimeByRow"].append(startTime)
        t = startTime - PARAMS["startTime"]
        carSpeed = eval(PARAMS["carSpeed"])
        PARAMS["carSpeedByRow"].append(carSpeed)
        PARAMS["WLonByRow"].append(carSpeed + random())
        PARAMS["WLatByRow"].append(random())
        PARAMS["fnmByRow"].append(PARAMS["fnm"])
        PARAMS["windNByRow"].append(PARAMS["windN"])
        PARAMS["windEByRow"].append(PARAMS["windE"])
        PARAMS["systemStatusByRow"].append(PARAMS["systemStatus"])
        startTime += dTime

# Live log:
#  When we restart the log, set the start time of the log to a fixed time before present
#  Generate data rows at the specified rate 


@app.route('/newLog')
def newLog():
    PARAMS["fnm"] += 1
    PARAMS["startTime"] = None
    PARAMS["eTimeByRow"] = []
    PARAMS["carSpeedByRow"] = []
    PARAMS["WLonByRow"] = []
    PARAMS["WLatByRow"] = []
    PARAMS["fnmByRow"] = []
    PARAMS["systemStatusByRow"] = []
    fillLog()
    return "New fnm = %d" % PARAMS["fnm"]

@app.route('/dTime/<value>')
def dTime(value):
    PARAMS["dTime"] = float(value)
    return "New dTime = %s" % PARAMS["dTime"]

@app.route('/systemStatus/<value>')
def systemStatus(value):
    PARAMS["systemStatus"] = int(value)
    return "New systemStatus = %s" % PARAMS["systemStatus"]

@app.route('/wind/<windN>/<windE>')
def wind(windN, windE):
    PARAMS["windN"] = float(windN)
    PARAMS["windE"] = float(windE)
    return "New wind velocity = %s, %s" % (PARAMS["windN"], PARAMS["windE"])

@app.route('/carSpeed/<expr>')
def carSpeed(expr):
    PARAMS["carSpeed"] = expr
    return "New car speed = %s" % PARAMS["carSpeed"]

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8003,debug=True)

# 127.0.0.1 - - [24/Dec/2013 10:51:08] "GET /stage/rest/gdu/1234567890/1.0/AnzLog?alog=@@Live:DEMO2000&logtype=dat&limit=500&doclist=True&qry=byPos&startPos=0 HTTP/1.1" 200 -
