/* newP3ApiService.js returns a new P3ApiService object for making P3 rest calls */
/*global console, exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
	var getRest = require('./getRest');
    var newParamsValidator = require('../public/js/common/paramsValidator').newParamsValidator;
	var url = require('url');
	var _ = require('underscore');

    /****************************************************************************/
    /* P3ApiService:  P3 service object for making rest calls                   */
    /****************************************************************************/
    function P3ApiService(pv) {
        this.pv = pv;
        this.ticket = null;
    }

    P3ApiService.prototype.getTicket = function (callback) {
        var ticket = null;
        this.ticket = null;
        var params = { "qry": "issueTicket",
                       "sys": this.pv.get("psys"),
                       "identity": this.pv.get("identity"),
                       "rprocs": this.pv.get("rprocs")};
        var options = url.parse(this.pv.get("ticket_url"));
        options.query = params;
        options.method = 'GET';
        options.headers =  {'Content-Type': 'application/json'};
        var that = this;
        getRest(options, function(err, statusCode, output) {
            var result;
            if (err) callback(err);
            else if (statusCode != 200) {
                callback(new Error("getTicket bad status code: " + statusCode));
            }
            else {
                try {
                    result = JSON.parse(output);
                }
                catch (e) {
                    callback(new Error("getTicket JSON decode error: " + e.message));
                }
                if (_.has(result,"ticket")) {
                    ticket = result["ticket"];
                    that.ticket = ticket;
                    callback(null,ticket);
                }
            }
        });
    };

    // Make a rest call to P3 with the P3ApiService object
    // svc: is the name of the service
    // ver: is the version of the API
    // rsc: is the requested resource
    // params: are the parameters for the request (as a dictionary)
    // callback: callback function with parameters err and obj

    // We make a rest call with the current ticket and see if it succeeds.
    // Depending on the error that occurs on the rest call, we perform various recovery strategies:
    // i)   A 403 ticket error causes us to get  new ticket and retry the rest call up to 100 times at full speed.
    //       Subsequent ticket errors cause retries at intervals given by "timeout"
    // ii)  A status code between 500 and 599, or an error during the request is considered recoverable. Up to
    //       "max_retries" are performed at intervals of "sleep_seconds"
    // iii) Any other error is considered unrecoverable, and leads to immediate execution of the callback.
    // iv)  A 401 or 403 error while fetching a new ticket is also considered unrecoverable.

    P3ApiService.prototype.get = function (svc, ver, rsc, params, callback) {
        var that = this;
        var ticketRetries = 0;
        var requestRetries = 0;

        function getTicketAndRetry() {
            ticketRetries += 1;
            that.getTicket(function (err, ticket) {
                if (err) {
                    if (err.message.indexOf("bad status")>=0 &&
                       (err.message.indexOf("401")>=0 || err.message.indexOf("403")>=0))  {
                        callback(new Error("Authentication failed in P3ApiService.get: " + err.message));
                        return;
                    }
                }
                else console.log("New ticket: " + ticket);
                wrappedGetRest();
            });
        }

        function handleRestResult(err, statusCode, output) {
            var result;
            if (statusCode === 200) { // Success
                try {
                    result = JSON.parse(output);
                }
                catch (e) {
                    callback(new Error("Bad JSON in P3ApiService.get: " + e.message));
                    return;
                }
                callback(null, result);
            }
            else if (statusCode === 403 && output.indexOf("invalid ticket") >= 0) {
                if (ticketRetries < 100) getTicketAndRetry();
                else setTimeout(getTicketAndRetry, 1000*that.pv.get("timeout"));
            }
            /*
            else if (err && err.message.indexOf('request error') >= 0) {
                callback(new Error("P3ApiService.get connection error: " + err));
            }
            */
            else if (err || (statusCode >= 500 && statusCode < 600)) {  // Try again after sleep_seconds
                if (requestRetries >= that.pv.get("max_retries")) {
                    callback(new Error("P3ApiService.get failed after " + that.pv.get("max_retries") + " retries."));
                }
                else {
                    setTimeout(wrappedGetRest, 1000*that.pv.get("sleep_seconds"));
                    requestRetries += 1;
                    console.log("Retry " + requestRetries + ": " + err + ', ' + statusCode + ', ' + output);
                }
            }
            else { // Unrecoverable error
                callback(new Error("P3ApiService.get unrecoverable error, statusCode: " + statusCode + " error:" + output));
            }
        }

        function wrappedGetRest() {
            var qry_url = that.pv.get("csp_url") + '/rest/' + svc + '/' + that.ticket + '/' + ver + '/' + rsc;
            var options = url.parse(qry_url);
            options.query = params;
            options.method = 'GET';
            options.timeout = 30;
            getRest(options,handleRestResult);
        }

        wrappedGetRest();
    };

    function newP3ApiService(options) {
        var pv = newParamsValidator(options, [
                {"name": "csp_url",      "required": true,  "validator": "string"},
                {"name": "ticket_url",   "required": true,  "validator": "string"},
                {"name": "identity",     "required": true,  "validator": "string"},
                {"name": "psys",         "required": true,  "validator": "string"},
                {"name": "rprocs",       "required": true,  "validator": "string"},
                {"name": "debug",        "required": false, "validator": "boolean", "default_value": false},
                {"name": "sleep_seconds","required": false, "validator": "number",  "default_value": 10.0},
                {"name": "timeout",      "required": false, "validator": "number",  "default_value": 5.0},
                {"name": "max_retries",  "required": false, "validator": "number", "default_value": 10}
        ]);
        if (pv.ok()) return new P3ApiService(pv);
        else return new Error(pv.errors());
    }

    module.exports = newP3ApiService;

});
