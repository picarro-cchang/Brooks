/*jshint undef:true, unused:true, globalstrict:true */
/*global Mongo, quit, print */
'use strict';

function dpSplit(x, y, ifirst, ilast) {
    // Analyze the path (x,y) between indices ifirst and ilast inclusive,
    //  returning the position and squared distance of the point that is furthest
    //  away from the line segment joining (x[ifirst], y[ifirst]) and 
    //  (x[ilast], y[ilast]). A point which is not in the arrays x, y is 
    //  automatically assumed to represent bad GPS data and so is returned
    //  promptly with d2max set to null. If no point is in range, isplit is null
    var ax = x[ilast] - x[ifirst];
    var ay = y[ilast] - y[ifirst];
    var d2min, d2max = 0;
    var isplit = null;
    for (var i=ifirst+1; i<ilast; i++) {
        if ((x[i] === null) || (y[i] === null)) {
            return {split: i, d2max: null};
        }
        var vx = x[i] - x[ifirst];
        var vy = y[i] - y[ifirst];
        var vv = vx*vx + vy*vy;
        var aa = ax*ax + ay*ay;
        var va = vx*ax + vy*ay;
        var alpha = (aa !== 0) ? va/aa : 0;
        if ((0 <= alpha) && (alpha <= 1)) {
            // The nearest point is within the line segment
            d2min = vv-alpha*alpha*aa;
        }
        else {
            d2min = Math.min(vv, vv-aa);
        }
        if (d2max <= d2min) {
            d2max = d2min;
            isplit = i;
        }
    }
    return {split:isplit, d2max:d2max};
}

function computeFlags(x, y, resFlag, ifirst, ilast, eList) {
    // Decimate the arrays of points (x,y) by assigning labels to
    //  the resFlag array which indicates whether a point is needed when
    //  rendering the path to a particular tolerance. A point 
    //  x[k],y[k] needs to be included when rendering to a tolerance
    //   eList[j] provided that resFlag[k]<=j
    // The list of tolerances eList must be strictly decreasing
    function _decimate(ifirst, ilast) {
        var k;
        for (; ifirst<ilast; ifirst++) {
            if (x[ifirst] !== null && y[ifirst] !== null) break;
        }
        for (; ifirst<ilast; ilast--) {
            if (x[ilast] !== null && y[ilast] !== null) break;
        }
        if (ifirst === ilast) return;
        var s = dpSplit(x, y, ifirst, ilast);
        var isplit = s.split;
        var d2max = s.d2max;
        if (isplit === null) return;
        var kmin = Math.max(resFlag[ifirst],resFlag[ilast]);
        for (k=kmin; k<eList.length; k++) {
            if (eList[k] < d2max) break;
        }
        resFlag[isplit] = k;
        if ((isplit - ifirst) < (ilast - isplit)) {
            _decimate(ifirst, isplit);
            _decimate(isplit, ilast);
        }
        else {
            _decimate(isplit, ilast);
            _decimate(ifirst, isplit);
        }
    }
    _decimate(ifirst, ilast);
}

function addResolutionFlags(logname, db, callback) {
    var fnm;
    var lat = [], lng = [], resFlag = [], valveMask = [];
    var x = [], y = [], eList = [];
    var Re = 6371000, DTR = Math.PI/180.0;
    var i, npts = 0, valveIndex;
    var avgLat = 0, avgLng = 0;
    eList = [];
    for (i=-2; i<=12; i+=2) {
        eList.push(Math.pow(2.0,-i));
    }

    var log_meta = db.analyzer_dat_logs_list.findOne({logname:logname});
    if (!log_meta) {
        print("Cannot find metadata for " + logname);
        quit();
    }
    fnm = log_meta.fnm;
    valveIndex = log_meta.docmap.ValveMask;
    // Fetch data from the dat_logs collection for this fnm. 
    //  Get list of fields, together with valve mask
    var fields = {lat:1,lng:1,fit:1,row:1,_id:0};
    fields[valveIndex] = 1;
    var logs = db.analyzer_dat_logs.find({fnm: fnm}, fields).sort({row:1});
    logs.forEach( function(item) {
        valveMask[item.row] = item[valveIndex];
        resFlag[item.row] = 0;
        if (item.fit >= 1) {
            lat[item.row] = item.lat;
            lng[item.row] = item.lng;
            avgLat += item.lat;
            avgLng += item.lng;
            npts += 1;
        }
        else {
            lat[item.row] = null;
            lng[item.row] = null;
        }
    });

    if (npts>0) {
        avgLat = avgLat / npts;
        avgLng = avgLng / npts;
    }
    var scale = Math.cos(avgLat * DTR);
    for (i=0; i<resFlag.length; i++) {
        if (resFlag[i] !== undefined) { // TODO: Also filter out rows in which the ValveMask changes
            x[i] = (lng[i]-avgLng) * Re * DTR * scale;
            y[i] = (lat[i]-avgLat) * Re * DTR;
        }
        else {
            x[i] = null;
            y[i] = null;
            resFlag[i] = 0;
        }
    }
    computeFlags(x, y, resFlag, 0, x.length-1, eList);
    print(resFlag);
    logs = db.analyzer_dat_logs.find({fnm: fnm}, {_id:1, row:1}).sort({row:1});
    logs.forEach( function(item) {
        db.analyzer_dat_logs.update({_id:item._id},{$set: {resFlag:resFlag[item.row]}});
    });
    print(resFlag.length + ' points. Avg lat: ' + avgLat + ', Avg lng: ' + avgLng);
    callback(null);
}

// Find the fnm of the log name containing the data
var logname = 'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat';
var conn = new Mongo();
var db = conn.getDB("main_pfranz");
addResolutionFlags(logname, db, function (err) {
    if (err) print("Error: " + err.message);
    else print("Updated database");
    quit();
});
