/*global console, describe, before, beforeEach, it, require  */
/* jshint -W030, -W024, -W097, undef:true, unused:true */

'use strict';
var events = require('events');
var p3nodeapi = require('../lib/p3nodeapi');
var rptGenStatus = require('../public/js/common/rptGenStatus');
var util = require('util');

var IDENTITY = "dc1563a216f25ef8a20081668bb6201e";
var PSYS = "APITEST2";
var HOST = "dev.picarro.com";
var PORT = 443;
var SITE = "dev";

var initArgs = {host: HOST, port: PORT, site: SITE,
                 identity: IDENTITY, psys: PSYS,
                 rprocs: ["AnzLog:byEpoch"],
                 svc: "gdu", version: "1.0",
                 resource: "AnzLog",
                 debug: false};
var AnzLog = new p3nodeapi.p3NodeApi(initArgs);

initArgs = {host: HOST, port: PORT, site: SITE,
                 identity: IDENTITY, psys: PSYS,
                 rprocs: ["AnzLrt:getStatus", "AnzLrt:firstSet", "AnzLrt:nextSet"],
                 svc: "gdu", version: "1.0",
                 resource: "AnzLrt",
                 debug: false};
var AnzLrt = new p3nodeapi.p3NodeApi(initArgs);


function P3LrtFetcher(reqApi, lrtApi, reqType, params) {
    // The P3LrtFetcher initiates and retrieves data from a long-running task
    //  reqApi: an instance of a P3NodeApi to which the request will be made
    //  lrtApi: an instance of a P3NodeApi to which the long running task requests will be made
    //  reqType: request type, e.g. byEpoch
    //  params: parameters of request
    // The fetcher emits the following events:
    //  'data': indicates that a list of data objects has been retrieved
    //  'end': indicates the end of the data for the request
    //  'error': indicates that some error has occured
    events.EventEmitter.call(this); // Call the constructor of the superclass
    this.reqApi = reqApi;
    this.lrtApi = lrtApi;
    this.params = params;
    this.reqType = reqType;
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
        that.reqApi[that.reqType](that.params,
        function (err) {
            if (err) that.emit("error", err);
        },
        function (status, result) {
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
        });
    }

    function pollUntilDone() {
        // Always make at least one call to getStatus so we know the number of rows in the result
        var params = {'prmsHash': that.lrt_parms_hash, 'startTs':that.lrt_start_ts};
        that.lrtApi.getStatus(params,
        function (err) {
            if (err) that.emit("error", err);
        },
        function (status, result) {
            that.lrt_status = result["status"];
            that.lrt_count = result["count"];
            console.log("P3Lrt Status: " + that.lrt_status);
            if (that.lrt_status === rptGenStatus.DONE) fetchFirst();
            else if (that.lrt_status < 0 || that.lrt_status > rptGenStatus.DONE) that.emit("error", new Error("Failure status" + that.lrt_status));
            else setTimeout(pollUntilDone,5000);
        });
    }

    function fetchFirst() {
        that.start = 1;
        var params = {'prmsHash': that.lrt_parms_hash, 'startTs':that.lrt_start_ts,
                      'limit':that.setSize};
        that.lrtApi.firstSet(params,
        function (err) {
            if (err.indexOf("404")>=0 && err.indexOf("9999")>=0) that.emit("end");
            else that.emit("error", err);
        },
        function (status,result) {
            console.log("Fetching " + that.start + " to " + (that.start + result.length - 1) +
                        " of " + that.lrt_count + " results");
            that.start += result.length;
            that.sortPos = result[result.length-1]["lrt_sortpos"];
            that.emit("data", result);
            fetchNext();
        });
    }

    function fetchNext() {
        var params = {'prmsHash': that.lrt_parms_hash, 'startTs':that.lrt_start_ts,
                      'sortPos': that.sortPos, 'limit':that.setSize};
        that.lrtApi.nextSet(params,
        function (err) {
            if (err.indexOf("404")>=0 && err.indexOf("9999")>=0) that.emit("end");
            else that.emit("error", err);
        },
        function (status,result) {
            console.log("Fetching " + that.start + " to " + (that.start + result.length - 1) +
                        " of " + that.lrt_count + " results");
            that.start += result.length;
            that.sortPos = result[result.length-1]["lrt_sortpos"];
            that.emit("data", result);
            fetchNext();
        });
    }
    makeRequest();
};

function newP3LrtFetcher(reqApi, lrtApi, reqType, params) {
    return new P3LrtFetcher(reqApi, lrtApi, reqType, params);
}

var p3lrt = newP3LrtFetcher(AnzLog, AnzLrt, "byEpoch",
            {'anz':'CFADS2274', 'startEtm':1354838400, 'endEtm': 1354924740, 'logtype':'peaks',
            'minLng':-105.04715, 'minLat':39.67958, 'maxLng':-105.01814, 'maxLat':39.71366,
            'forceLrt':false, 'resolveLogname':true, 'doclist':false, 'limit':'all', 'rtnFmt':'lrt'});

p3lrt.on("data", function(data) {
    console.log('DATA');
    console.log(data);
});

p3lrt.on("error", function(err) {
    console.log('ERROR');
    console.log(err);
});

p3lrt.on("end", function() {
    console.log('END');
});

p3lrt.run();
