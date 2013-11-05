/*jshint undef:true, unused:true */
/*global console, process, require */

'use strict';

var databaseUrl = "main_pfranz";
var MongoClient = require('mongodb').MongoClient;

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
    // Find the fnm of the log name containing the data
    var logs_list = db.collection('analyzer_dat_logs_list');
    var dat_logs = db.collection('analyzer_dat_logs');
    var fnm;
    var lat = [], lng = [], resFlag = [];
    var x = [], y = [], eList = [];
    var Re = 6371000, DTR = Math.PI/180.0;
    var npts = 0;
    var avgLat = 0, avgLng = 0;
    eList = [];
    for (var i=-2; i<=12; i+=2) {
        eList.push(Math.pow(2.0,-i));
    }

    logs_list.find({logname:logname}).toArray(function (err, logs) {
        var stream;
        if (err) callback(err);
        else {
            if (logs.length != 1) callback(new Error("Cannot resolve log name " + logname + " to a unique fnm in database"));
            else {
                fnm = logs[0].fnm;
                // Fetch data from the dat_logs collection for this fnm
                stream = dat_logs.find({fnm: fnm},{sort:{row:1}, fields:{lat:1,lng:1,fit:1,row:1}}).stream();
                stream.on("data", function(item) {
                    if (item.fit >= 1) {
                        resFlag[item.row] = 0;
                        lat[item.row] = item.lat;
                        lng[item.row] = item.lng;
                        avgLat += item.lat;
                        avgLng += item.lng;
                        npts += 1;
                    }
                });
                stream.on("end", function() {
                    var i;
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
                    // Update the records in the database

                    stream = dat_logs.find({fnm: fnm},{sort:{row:1}, fields:{row:1}}).stream();
                    var counter = 0;
                    var ended = false;
                    stream.on("data", function(item) {
                        counter += 1;
                        dat_logs.update({_id:item._id},{$set: {resFlag:resFlag[item.row]}}, function (err) {
                            if (err) console.log(err.message);
                            counter -= 1;
                            if (counter === 0 && ended) callback(null);
                        });
                    });
                    stream.on("end", function() {
                        ended = true;
                        console.log("All done: " + resFlag.length + " Average lat, lng: " + avgLat + " " + avgLng + " " + counter);
                        if (counter === 0) callback(null);
                    });
                });
            }
        }
    });
}

MongoClient.connect("mongodb://localhost:27017/" + databaseUrl, function (err, db) {
    if (err) {
        console.log("Error: " + err.message);
    }
    else {
        console.log("We are connected");

        // Find the fnm of the log name containing the data
        var logname = 'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat';
        addResolutionFlags(logname, db, function (err, flags) {
            if (err) console.log("Error: " + err.message);
            else {
                // Update the database with the flags info
                console.log("Updated database");
            }
            process.exit();
        });
    }
});
