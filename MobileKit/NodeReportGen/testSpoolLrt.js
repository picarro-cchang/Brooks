// Get result of long running task from Pcubed
/*global console, __dirname, exports, require */

'use strict';
var fs = require('fs');
var rs = require('./reportSupport');
var events = require('events');
var newP3ApiService = require('./lib/newP3ApiService');
var newP3LrtFetcher = require('./lib/newP3LrtFetcher');
var newSerializer = require('./lib/newSerializer');
var util = require('util');
var _ = require('underscore');

var csp_url = "https://dev.picarro.com/dev";
var ticket_url = csp_url + "/rest/sec/dummy/1.0/Admin";
var identity = "dc1563a216f25ef8a20081668bb6201e";
var psys = "APITEST2";
var rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath","AnzMeta:byAnz","AnzLrt:getStatus",' +
         '"AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo"]';
var p3Api = newP3ApiService({"csp_url": csp_url, "ticket_url": ticket_url, "identity": identity, "psys": psys, "rprocs": rprocs});

if (p3Api instanceof Error) {
    console.log("Error getting P3ApiService: " + p3Api);
}
else {
    var svc = "gdu";
    var ver = "1.0";
    var rsc = "AnzLog";
    var params = {'anz':'CFADS2276', 'startEtm':1354641132, 'endEtm':1355011140,
                    'box':'[-105.31494,39.4892,-104.65576,39.98343]', 'qry':'byGeo',
                    'resolveLogname':true, 'doclist':false, 'limit':5000, 'rtnFmt':'lrt' };
    var result = [];
    var p3LrtFetcher = newP3LrtFetcher(p3Api, svc, ver, rsc, params);
    var ser = newSerializer(p3LrtFetcher);

    var resultFile = "mytest.txt";

    ser.on("error", function (err) {
        console.log("Error in serialized P3LrtFetcher: " + err);
    });

    ser.on("data", function (data) {
        var lines = [];
        data.forEach(function(d) {
            lines.push(JSON.stringify(d));
        });
        fs.appendFile(resultFile, lines.join("\n") + (lines.length>0 ? "\n":""), function(err) {
            if (err) console.log("Error in appending to file: " + err);
            else {
                ser.acknowledge();
            }
        });
    });

    ser.on("end", function () {
        console.log("Done");
    });

    // Start by creating new result file and running fetcher
    fs.writeFile(resultFile,"",function (err) {
        if (err) console.log("Error in creating result file: " + err);
        else {
            p3LrtFetcher.run();
        }
    });
}
