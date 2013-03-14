/* newRptGenLrtController.js makes a new long-running task controller for the report generator. */
/*global console, exports, module, require */


// TODO: If we get a status from RptGen that a previous LRT is not yet done when we make a
//   request to start a new task with the same hash, we should compare the request_ts
//   and the start_ts. If they differ by more than a preset amount, the task should be
//   resubmitted with the force flag
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var events = require('events');
    var http = require('http');
    var rptGenStatus = require('./rptGenStatus');
    var ts = require('./timeStamps');
    var util = require('util');

    function RptGenLrtController(rptGenService, rsc, params) {
        // The RptGenLrtController initiates and retrieves data from a long-running task
        //  rptGenService: an instance of a RptGenService
        //  svc: name of service
        //  ver: version of API
        //  rsc: resource requested
        //  params: parameters of request
        // The fetcher emits the following events:
        //  'data': indicates that a list of data objects has been retrieved
        //  'end': indicates the end of the data for the request
        //  'error': indicates that some error has occured
        events.EventEmitter.call(this); // Call the constructor of the superclass
        this.rptGenService = rptGenService;
        this.rsc = rsc;
        this.params = params;
        this.rpt_status = null;
        this.rpt_contents_hash = null;
        this.rpt_start_ts = null;
        this.submit_key = {};
        this.start = 0;
    }

    util.inherits(RptGenLrtController, events.EventEmitter);

    RptGenLrtController.prototype.run = function () {
        var that = this;

        function makeRequest() {
            that.rptGenService.get(that.rsc, that.params, function (err, result) {
                if (err) that.emit("error", err);
                else {
                    if (result["rpt_start_ts"] === result["request_ts"]) {
                        console.log("This is a new request, made at " + result["request_ts"]);
                    }
                    else {
                        console.log("This is a duplicate of a request made at " + result["rpt_start_ts"]);
                    }
                    that.rpt_status = result["status"];
                    console.log("RptGen status: " + that.rpt_status);
                    that.rpt_contents_hash = result["rpt_contents_hash"];
                    that.rpt_start_ts = result["rpt_start_ts"];
                    that.submit_key = {"hash": that.rpt_contents_hash,
                                       "time_stamp": that.rpt_start_ts,
                                       "request_ts": result["request_ts"],
                                       "dir_name": ts.timeStringAsDirName(that.rpt_start_ts)};
                    that.emit("submit",that.submit_key);
                    pollUntilDone();
                }
            });
        }

        function pollUntilDone() {
            // Always make at least one call to getStatus
            var params = {'contents_hash': that.rpt_contents_hash, 'start_ts':that.rpt_start_ts, 'qry': 'getStatus'};
            that.rptGenService.get(that.rsc, params, function (err, result) {
                if (err) that.emit("error", err);
                else {
                    that.rpt_status = result["status"];
                    console.log("RptGen status: " + that.rpt_status);
                    if (that.rpt_status === rptGenStatus.DONE) {
                        // Get the information from the key file for the request
                        var rsc = "data/" + that.submit_key["hash"] +
                                  "/" + that.submit_key["dir_name"] + "/key.json";
                        that.rptGenService.get(rsc, {}, function (err, result) {
                            if (err) that.emit("error", err);
                            else {
                                that.emit("end",that.submit_key,result);
                            }
                        });
                    }
                    else if (that.rpt_status < 0) that.emit("error", new Error("Failure status" + that.rpt_status));
                    else setTimeout(pollUntilDone,5000);
                }
            });
        }
        makeRequest();
    };

    function newRptGenLrtController(rptGenService, rsc, params) {
        return new RptGenLrtController(rptGenService, rsc, params);
    }

    module.exports = newRptGenLrtController;

});

