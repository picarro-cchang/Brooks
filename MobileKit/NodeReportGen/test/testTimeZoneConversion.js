// testTimeZoneConversion is used to develop a routine that deals with many conversion requests which would
//  otherwise overflow a single rest call
/*global console, describe, afterEach, beforeEach, it, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */
'use strict';
var expect = require("chai").expect;
var path = require("path");
var newRptGenService = require("../lib/newRptGenService");

// Wrap this in something that more closely resembles the P3 API
function Timezone() {
    var rptGenService = newRptGenService({rptgen_url: "http://localhost:8300/stage"});
    this.timezone = function(qry_obj, errorCbFn, successCbFn) {
        rptGenService.get("Utilities/tz", qry_obj, function (err,result) {
            if (err) {
                errorCbFn(err.message);
            }
            else {
                successCbFn(200, result);
            }
        });
    };
}

var posList = [];
for (var i=0; i<5000; i++) {
    posList.push(1000*i);
}

var Utility = new Timezone();
var params = {"tz":"America/Los_Angeles","posixTimes":posList};
bufferedTimezone(Utility.timezone, params,
    function (err) {
        console.log("Error callback: " + err);
    },
    function (s, result) {
        console.log("Success status: " + s);
        console.log("Success result: " + JSON.stringify(result));
        var timeList = [];
        for (var j=0; j<result.timeStrings.length; j++) {
            timeList.push(result.timeStrings[j].substr(0,19));
        } 

        var newParams = {"tz":"America/Los_Angeles", "timeStrings":timeList};
        bufferedTimezone(Utility.timezone, newParams,
            function (err) {
                console.log("Error callback: " + err);
            },
            function (s, result) {
                console.log("Success status: " + s);
                console.log("Success result: " + JSON.stringify(result));
            }
        );
    });

/* The following is used to buffer requests to a timezone handling service, so 
    that not too many requests are made at once */

function bufferedTimezone(service, qry_obj, errorCbFn, successCbFn) {
    var chunk, subqry, input, output1, output2;
    var chunkSize = 100;
    if ("posixTimes" in qry_obj && qry_obj.posixTimes.length>0) {
        input = qry_obj.posixTimes.slice(0);
        output1 = [];
        output2 = [];
        var next1 = function() {
            if (input.length === 0) {
                successCbFn(200, {"tz": qry_obj.tz, "posixTimes": output1, "timeStrings": output2});
            }
            else {
                chunk = input.splice(0,chunkSize);
                subqry = {"tz": qry_obj.tz, "posixTimes": chunk};
                service(subqry,
                function (err) {
                    errorCbFn(err);
                },
                function (s, result) {
                    output1.push.apply(output1, result.posixTimes);
                    output2.push.apply(output2, result.timeStrings);
                    next1();
                });
            }
        };
        next1();
    }
    else if ("timeStrings" in qry_obj && qry_obj.timeStrings.length>0) {
        input = qry_obj.timeStrings.slice(0);
        output1 = [];
        output2 = [];
        var next2 = function() {
            if (input.length === 0) {
                successCbFn(200, {"tz": qry_obj.tz, "posixTimes": output1, "timeStrings": output2});
            }
            else {
                chunk = input.splice(0,chunkSize);
                subqry = {"tz": qry_obj.tz, "timeStrings": chunk};
                service(subqry,
                function (err) {
                    errorCbFn(err);
                },
                function (s, result) {
                    output1.push.apply(output1, result.posixTimes);
                    output2.push.apply(output2, result.timeStrings);
                    next2();
                });
            }
        };
        next2();
    }
}
