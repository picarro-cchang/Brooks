// Get result of long running task from Pcubed
/*global console, exports, require */

'use strict';

var newP3ApiService = require('./lib/newP3ApiService');
var newP3LrtFetcher = require('./lib/newP3LrtFetcher');
var events = require('events');
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
    p3LrtFetcher.on("error", function (err) {
        console.log("Error in p3LrtFetcher: " + err);
    });

    p3LrtFetcher.on("data", function (data) {
        data.forEach(function (d) {
            result.push(d.document);
        });
        // result.push.apply(result, data);
    });

    p3LrtFetcher.on("end", function () {
        console.log("Done");
        console.log("Result length: " + result.length);
    });

    p3LrtFetcher.run();
}
