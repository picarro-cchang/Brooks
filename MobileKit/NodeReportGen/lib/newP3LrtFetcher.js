/* newP3LrtFetcher.js makes a new long-running task fetcher for P3. */
/*global console, exports, module, require */


// TODO: If we get a status from P3 that a previous LRT is not yet done when we make a
//   request to start a new task with the same hash, we should compare the request_ts
//   and the start_ts. If they differ by more than a preset amount, the task should be
//   resubmitted with the force flag
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var events = require('events');
    var rptGenStatus = require('../public/js/common/rptGenStatus');
    var util = require('util');

    function P3LrtFetcher(p3service, svc, ver, rsc, params) {
        // The P3LrtFetcher initiates and retrieves data from a long-running task
        //  p3Service: an instance of a P3ApiService
        //  svc: name of service
        //  ver: version of API
        //  rsc: resource requested
        //  params: parameters of request
        // The fetcher emits the following events:
        //  'data': indicates that a list of data objects has been retrieved
        //  'end': indicates the end of the data for the request
        //  'error': indicates that some error has occured
        events.EventEmitter.call(this); // Call the constructor of the superclass
        this.p3service = p3service;
        this.svc = svc;
        this.ver = ver;
        this.rsc = rsc;
        this.params = params;
        this.lrt_status = null;
        this.lrt_parms_hash = null;
        this.lrt_start_ts = null;
        this.sortPos = null;
        this.setSize = 1000;
        this.start = 0;
    }

    util.inherits(P3LrtFetcher, events.EventEmitter);

    P3LrtFetcher.prototype.setSize = function (size) {
        this.setSize = size;
    };

    P3LrtFetcher.prototype.run = function () {
        var that = this;

        function makeRequest() {
            that.p3service.get(that.svc, that.ver, that.rsc, that.params, function (err, result) {
                if (err) that.emit("error", err);
                else {
                    if (result["lrt_start_ts"] === result["request_ts"]) {
                        console.log("This is a new request, made at " + result["request_ts"]);
                    }
                    else {
                        console.log("This is a duplicate of a request made at " + result["lrt_start_ts"]);
                    }
                    that.lrt_status = result["status"];
                    console.log("P3Lrt Status: " + that.lrt_status);
                    that.lrt_parms_hash = result["lrt_parms_hash"];
                    that.lrt_start_ts = result["lrt_start_ts"];
                    pollUntilDone();
                }
            });
        }

        function pollUntilDone() {
            // Always make at least one call to getStatus so we know the number of rows in the result
            var params = {'prmsHash': that.lrt_parms_hash, 'startTs':that.lrt_start_ts, 'qry': 'getStatus'};
            that.p3service.get(that.svc, that.ver, "AnzLrt", params, function (err, result) {
                if (err) that.emit("error", err);
                else {
                    that.lrt_status = result["status"];
                    that.lrt_count = result["count"];
                    console.log("P3Lrt Status: " + that.lrt_status);
                    if (that.lrt_status === rptGenStatus.DONE) fetchFirst();
                    else if (that.lrt_status < 0 || that.lrt_status > rptGenStatus.DONE) that.emit("error", new Error("Failure status: " + that.lrt_status));
                    else setTimeout(pollUntilDone,5000);
                }
            });
        }

        function fetchFirst() {
            that.start = 1;
            var params = {'prmsHash': that.lrt_parms_hash, 'startTs':that.lrt_start_ts, 'qry': 'firstSet',
                          'limit':that.setSize};
            that.p3service.get(that.svc, that.ver, "AnzLrt", params, function (err, result) {
                if (err) {
                    if (err.message.indexOf("404") >= 0 && err.message.indexOf("9999") >= 0) {
                        that.emit("end");
                    }
                    else that.emit("error", err);
                }
                else {
                    console.log("Fetching " + that.start + " to " + (that.start + result.length - 1) +
                                " of " + that.lrt_count + " results");
                    that.start += result.length;
                    that.sortPos = result[result.length-1]["lrt_sortpos"];
                    that.emit("data", result);
                    fetchNext();
                }
            });
        }

        function fetchNext() {
            var params = {'prmsHash': that.lrt_parms_hash, 'startTs':that.lrt_start_ts, 'qry': 'nextSet',
                          'sortPos': that.sortPos, 'limit':that.setSize};
            that.p3service.get(that.svc, that.ver, "AnzLrt", params, function (err, result) {
                if (err) {
                    if (err.message.indexOf("404") >= 0 && err.message.indexOf("9999") >= 0) {
                        that.emit("end");
                    }
                    else that.emit("error", err);
                }
                else {
                    console.log("Fetching " + that.start + " to " + (that.start + result.length - 1) +
                                " of " + that.lrt_count + " results");
                    that.start += result.length;
                    that.sortPos = result[result.length-1]["lrt_sortpos"];
                    that.emit("data", result);
                    fetchNext();
                }
            });
        }
        makeRequest();
    };

    function newP3LrtFetcher(p3service, svc, ver, rsc, params) {
        return new P3LrtFetcher(p3service, svc, ver, rsc, params);
    }

    module.exports = newP3LrtFetcher;

});
