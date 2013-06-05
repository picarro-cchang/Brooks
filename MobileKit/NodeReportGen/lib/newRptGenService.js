/* newRptGenService.js returns a new RptGenService object to access the rest
   calls of the report generator */
/*global console, exports, module, require */

/* 
This function performs a GET rest call on a server, passing the parameters to the call as a query string to the URL
If the server returns an error or if the status code is in the range [500,600), the call is retried at intervals of
"sleep_seconds" up to "max_retries" times.

Example Usage: Calling the time zone conversion routine on a server

var rptGenService = newRptGenService({rptgen_url: "http://localhost:8300/stage"});
var params = {"tz":"America/Los_Angeles","posixTimes":1000000};
var rsc = "Utilities/tz";

rptGenService.get(rsc, params, function (err,result) {
    console.log("err: " + err);
    console.log("result: " + JSON.stringify(result));
});

The actual rest call consists of rptgen_url + "/rest/" + rsc

*/

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
	var getRest = require('./getRest');
    var newParamsValidator = require('../public/js/common/paramsValidator').newParamsValidator;
	var url = require('url');
	var _ = require('underscore');

    /****************************************************************************/
    /* RptGenService:  RptGen service object for making rest calls              */
    /****************************************************************************/
    function RptGenService(pv) {
        this.pv = pv;
    }

    RptGenService.prototype.get = function (rsc, params, callback) {
        var that = this;
        var requestRetries = 0;

        var handleRestResult = function (err, statusCode, output) {
            var result;
            if (statusCode === 200) { // Success
                try {
                    result = JSON.parse(output);
                }
                catch (e) {
                    callback(new Error("Bad JSON in RptGenService.get: " + e.message));
                    return;
                }
                callback(null, result);
            }
            /*
            else if (err && err.message.indexOf('request error') >= 0) {
                callback(new Error("RptGenService.get connection error: " + err));
            }
            */
            else if (err || (statusCode >= 500 && statusCode < 600)) {  // Try again after sleep_seconds
                if (requestRetries >= that.pv.get("max_retries")) {
                    callback(new Error("RptGenService.get failed after " + that.pv.get("max_retries") + " retries."));
                }
                else {
                    setTimeout(wrappedGetRest, 1000*that.pv.get("sleep_seconds"));
                    requestRetries += 1;
                    console.log("Retry " + requestRetries + ": " + err + ', ' + statusCode + ', ' + output);
                }
            }
            else { // Unrecoverable error
                callback(new Error("RptGenService.get unrecoverable error, statusCode: " + statusCode + " error:" + output));
            }
        };

        function wrappedGetRest() {
            var qry_url = that.pv.get("rptgen_url") + '/rest/' + rsc;
            var options = url.parse(qry_url);
            options.query = params;
            options.method = 'GET';
            options.timeout = 30;
            getRest(options,handleRestResult);
        }

        wrappedGetRest();
    };

    function newRptGenService(options) {
        var pv = newParamsValidator(options, [
                {"name": "rptgen_url",    "required": true,  "validator": "string"},
                {"name": "sleep_seconds", "required": false, "validator": "number", "default_value": 10.0},
                {"name": "max_retries",   "required": false, "validator": "number", "default_value": 10}
            ]);
        if (pv.ok()) return new RptGenService(pv);
        else return new Error(pv.errors());
    }

    module.exports = newRptGenService;

});
