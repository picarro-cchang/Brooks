/* newRptGenService.js returns a new RptGenService object to access the rest
   calls of the report generator */
/*global console, exports, module, require */

define(['jquery', 'underscore', 'app/paramsValidator'],
function($, _, paramsValidator) {
	'use strict';
    var newParamsValidator = paramsValidator.newParamsValidator;

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
            $.ajax({contentType: "application/json",
                data: $.param(params),
                dataType: "text",
                url: qry_url,
                type: "GET",
                timeout: 20000,
                success: function (data, textStatus, jqXHR) {
                    handleRestResult(null, jqXHR.status, data);
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    handleRestResult(new Error(textStatus + ' ' + errorThrown), jqXHR.status, null);
                }
            });
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

    return newRptGenService;

});
